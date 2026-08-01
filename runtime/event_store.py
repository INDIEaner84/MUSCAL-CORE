import json
import logging
import threading
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional

from runtime.database import get_connection

logger = logging.getLogger(__name__)


class VerificationConflictError(ValueError):
    """Raised when a verification conflicts with an existing verification for the same execution_id."""


class EvidenceRequiredError(ValueError):
    """Raised when a verification to 'verified' lacks required evidence."""


_EXECUTION_REQUIRED_TOPICS = frozenset({
    "EXECUTION_STARTED",
    "EXECUTION_FINISHED",
    "TOOL_EXECUTED",
    "SYSTEM_ACTION_STARTED",
    "SYSTEM_ACTION_COMPLETED",
    "SYSTEM_ACTION_FAILED",
    "execution.receipt",
    "execution.verification",
    "VERIFICATION_PASSED",
    "VERIFICATION_FAILED",
})


class EventStore:
    """Append-only SQLite-backed event persistence with cursor-based replay.
    This is the SINGLE CANONICAL EVENT AUTHORITY for all production events."""

    def __init__(self, db_path: Optional[Path] = None):
        if db_path is None:
            from config import DB_PATH
            db_path = DB_PATH
        self._db_path = Path(db_path)
        self._conn = get_connection(self._db_path)
        self._lock = threading.Lock()
        self._init_table()

    def _init_table(self) -> None:
        self._conn.execute(
            """CREATE TABLE IF NOT EXISTS stored_events (
                seq        INTEGER PRIMARY KEY AUTOINCREMENT,
                topic      TEXT NOT NULL,
                payload    TEXT NOT NULL DEFAULT '{}',
                source     TEXT NOT NULL DEFAULT '',
                priority   TEXT NOT NULL DEFAULT 'NORMAL',
                timestamp  REAL NOT NULL,
                event_id   TEXT NOT NULL UNIQUE,
                created_at TEXT NOT NULL,
                execution_id TEXT NOT NULL DEFAULT '',
                correlation_id TEXT NOT NULL DEFAULT '',
                causation_id TEXT NOT NULL DEFAULT '',
                execution_mode TEXT NOT NULL DEFAULT 'real',
                execution_state TEXT NOT NULL DEFAULT 'planned',
                verification_state TEXT NOT NULL DEFAULT 'unverified',
                is_replayed INTEGER NOT NULL DEFAULT 0,
                receipt_id TEXT NOT NULL DEFAULT ''
            )"""
        )
        self._conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_stored_events_topic ON stored_events(topic)"
        )
        self._conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_stored_events_created ON stored_events(created_at)"
        )
        self._migrate_add_columns()
        self._conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_stored_events_execution ON stored_events(execution_id)"
        )

    def append(self, event: Dict[str, Any]) -> Optional[int]:
        """Append a single event. Returns the assigned seq.

        Returns None if event is suppressed (replay marker).
        Raises sqlite3.IntegrityError on duplicate event_id.
        Raises ValueError if an execution-required event lacks execution_id.
        """
        import time
        import datetime

        with self._lock:
            topic = event.get("topic", "")

            payload = event.get("payload", {})
            if isinstance(payload, dict) and payload.get("_replayed"):
                return None

            execution_id = event.get("execution_id", "") or (payload.get("execution_id", "") if isinstance(payload, dict) else "")
            if topic in _EXECUTION_REQUIRED_TOPICS and not execution_id:
                raise ValueError(
                    f"Event topic '{topic}' requires execution_id, but none provided"
                )
            if not isinstance(payload, str):
                payload = json.dumps(payload, ensure_ascii=False, sort_keys=True)

            priority = event.get("priority", "NORMAL")
            if hasattr(priority, "name"):
                priority = priority.name

            ts = event.get("timestamp", time.time())
            created_at = datetime.datetime.now(datetime.timezone.utc).isoformat()

            is_replayed = event.get("is_replayed", 0)
            if isinstance(payload, str):
                try:
                    parsed = json.loads(payload)
                    if isinstance(parsed, dict) and parsed.get("_replayed"):
                        is_replayed = 1
                except Exception:
                    pass

            try:
                cursor = self._conn.execute(
                    """INSERT INTO stored_events
                       (topic, payload, source, priority, timestamp, event_id, created_at,
                        execution_id, correlation_id, causation_id, execution_mode,
                        execution_state, verification_state, schema_version, is_replayed,
                        receipt_id)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (
                        event.get("topic", ""),
                        payload,
                        event.get("source", ""),
                        str(priority),
                        float(ts),
                        event.get("id", ""),
                        created_at,
                        event.get("execution_id", ""),
                        event.get("correlation_id", ""),
                        event.get("causation_id", ""),
                        event.get("execution_mode", "real"),
                        event.get("execution_state", "planned"),
                        event.get("verification_state", "unverified"),
                        event.get("schema_version", 1),
                        int(is_replayed),
                        event.get("receipt_id", ""),
                    ),
                )
                self._conn.commit()
                return cursor.lastrowid
            except Exception:
                self._conn.rollback()
                raise

    def store_receipt(self, receipt: Any) -> Optional[int]:
        import time
        import logging
        payload = receipt.to_dict() if hasattr(receipt, "to_dict") else {"receipt_id": str(receipt)}
        receipt_eid = getattr(receipt, "execution_id", "")
        receipt_causation = getattr(receipt, "causation_id", "") or receipt_eid
        receipt_mode = getattr(receipt, "execution_mode", "")
        if not receipt_mode:
            logging.getLogger(__name__).warning(
                "store_receipt: receipt missing execution_mode, defaulting to 'real'"
            )
            receipt_mode = "real"
        return self.append({
            "topic": "execution.receipt",
            "payload": payload,
            "source": "UnifiedToolRuntime",
            "priority": "NORMAL",
            "timestamp": time.time(),
            "id": getattr(receipt, "receipt_id", str(uuid.uuid4())),
            "execution_id": receipt_eid,
            "correlation_id": getattr(receipt, "correlation_id", ""),
            "causation_id": receipt_causation,
            "execution_mode": receipt_mode,
            "execution_state": "completed" if getattr(receipt, "success", False) else "failed",
            "verification_state": "verified" if getattr(receipt, "verification_status", "pending") == "verified" else "unverified",
        })

    def store_verification(self, vr: Any) -> Optional[int]:
        import time
        import logging
        import datetime
        payload = vr.to_dict() if hasattr(vr, "to_dict") else {"verification_id": str(vr)}
        vr_mode = getattr(vr, "execution_mode", "")
        if not vr_mode:
            logging.getLogger(__name__).warning(
                "store_verification: verification missing execution_mode, defaulting to 'real'"
            )
            vr_mode = "real"
        vr_causation = getattr(vr, "causation_id", "") or getattr(vr, "receipt_id", "")

        vr_status = getattr(vr, "status", "pending")
        if hasattr(vr_status, "value"):
            vr_status = vr_status.value
        vr_status = str(vr_status)

        vr_execution_id = getattr(vr, "execution_id", "")
        vr_receipt_id = getattr(vr, "receipt_id", "")

        if vr_status == "verified":
            if not vr_receipt_id:
                raise EvidenceRequiredError(
                    "store_verification: cannot store 'verified' without a receipt_id"
                )
            if not vr_execution_id:
                raise EvidenceRequiredError(
                    "store_verification: cannot store 'verified' without an execution_id"
                )

        event_id = getattr(vr, "verification_id", str(uuid.uuid4()))

        with self._lock:
            row = self._conn.execute(
                "SELECT verification_state, event_id FROM stored_events "
                "WHERE execution_id = ? AND topic = 'execution.verification' "
                "ORDER BY seq DESC LIMIT 1",
                (vr_execution_id,),
            ).fetchone()

            if row is not None:
                existing_status = row["verification_state"]
                existing_event_id = row["event_id"]
                if existing_status != vr_status and existing_status in ("verified", "failed"):
                    raise VerificationConflictError(
                        f"Verification conflict for execution_id='{vr_execution_id}': "
                        f"existing={existing_status} (event_id={existing_event_id}), "
                        f"new={vr_status}. Conflicting verifications must be explicitly resolved."
                    )

            if isinstance(payload, dict):
                payload_str = json.dumps(payload, ensure_ascii=False, sort_keys=True)
            else:
                payload_str = payload

            ts = time.time()
            created_at = datetime.datetime.now(datetime.timezone.utc).isoformat()
            priority = "NORMAL"

            try:
                cursor = self._conn.execute(
                    """INSERT INTO stored_events
                       (topic, payload, source, priority, timestamp, event_id, created_at,
                        execution_id, correlation_id, causation_id, execution_mode,
                        execution_state, verification_state, schema_version, is_replayed,
                        receipt_id)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (
                        "execution.verification",
                        payload_str,
                        "VerificationOrchestrator",
                        priority,
                        ts,
                        event_id,
                        created_at,
                        vr_execution_id,
                        getattr(vr, "correlation_id", ""),
                        vr_causation,
                        vr_mode,
                        "completed",
                        vr_status,
                        1,
                        0,
                        vr_receipt_id,
                    ),
                )
                self._conn.commit()
                return cursor.lastrowid
            except Exception:
                self._conn.rollback()
                raise

    def _migrate_add_columns(self) -> None:
        legacy_cols = {
            "execution_id": "TEXT NOT NULL DEFAULT ''",
            "correlation_id": "TEXT NOT NULL DEFAULT ''",
            "causation_id": "TEXT NOT NULL DEFAULT ''",
            "execution_mode": "TEXT NOT NULL DEFAULT 'real'",
            "execution_state": "TEXT NOT NULL DEFAULT 'planned'",
            "verification_state": "TEXT NOT NULL DEFAULT 'unverified'",
        }
        existing = {
            r["name"] for r in
            self._conn.execute("PRAGMA table_info(stored_events)")
        }
        for col_name, col_def in legacy_cols.items():
            if col_name not in existing:
                sql = f"ALTER TABLE stored_events ADD COLUMN {col_name} {col_def}"
                self._conn.execute(sql)
        if "schema_version" not in existing:
            self._conn.execute(
                "ALTER TABLE stored_events ADD COLUMN schema_version INTEGER NOT NULL DEFAULT 1"
            )
        if "is_replayed" not in existing:
            self._conn.execute(
                "ALTER TABLE stored_events ADD COLUMN is_replayed INTEGER NOT NULL DEFAULT 0"
            )
        if "receipt_id" not in existing:
            self._conn.execute(
                "ALTER TABLE stored_events ADD COLUMN receipt_id TEXT NOT NULL DEFAULT ''"
            )
        self._conn.commit()

    def replay(
        self,
        cursor: Optional[int] = None,
        topic: Optional[str] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """Replay events. cursor is last_seen_seq (seq > cursor)."""
        if limit <= 0:
            raise ValueError("limit must be positive")

        with self._lock:
            clauses: List[str] = []
            params: List[Any] = []

            if cursor is not None:
                clauses.append("seq > ?")
                params.append(cursor)

            if topic is not None:
                clauses.append("topic = ?")
                params.append(topic)

            where = (" WHERE " + " AND ".join(clauses)) if clauses else ""
            sql = f"SELECT * FROM stored_events{where} ORDER BY seq ASC LIMIT ?"
            params.append(limit)

            rows = self._conn.execute(sql, params).fetchall()
            return [self._row_to_dict(r) for r in rows]

    def get_cursor(self) -> int:
        """Return the highest seq in stored_events, or 0 if empty."""
        with self._lock:
            row = self._conn.execute(
                "SELECT MAX(seq) AS max_seq FROM stored_events"
            ).fetchone()
            return row["max_seq"] if row and row["max_seq"] is not None else 0

    def event_count(self, topic: Optional[str] = None) -> int:
        """Count events, optionally filtered by topic."""
        with self._lock:
            if topic is not None:
                row = self._conn.execute(
                    "SELECT COUNT(*) AS cnt FROM stored_events WHERE topic = ?",
                    (topic,),
                ).fetchone()
            else:
                row = self._conn.execute(
                    "SELECT COUNT(*) AS cnt FROM stored_events"
                ).fetchone()
            return row["cnt"]

    def close(self) -> None:
        """Close the database connection. Idempotent."""
        with self._lock:
            if self._conn is not None:
                try:
                    self._conn.close()
                except Exception:
                    pass
                self._conn = None

    def _row_to_dict(self, row: Any) -> Dict[str, Any]:
        payload_raw = row["payload"]
        try:
            payload = json.loads(payload_raw)
        except (json.JSONDecodeError, TypeError):
            payload = payload_raw
        return {
            "seq": row["seq"],
            "topic": row["topic"],
            "payload": payload,
            "source": row["source"],
            "priority": row["priority"],
            "timestamp": row["timestamp"],
            "id": row["event_id"],
            "created_at": row["created_at"],
            "execution_id": row["execution_id"] if "execution_id" in row.keys() else "",
            "correlation_id": row["correlation_id"] if "correlation_id" in row.keys() else "",
            "causation_id": row["causation_id"] if "causation_id" in row.keys() else "",
            "execution_mode": row["execution_mode"] if "execution_mode" in row.keys() else "real",
            "execution_state": row["execution_state"] if "execution_state" in row.keys() else "planned",
            "verification_state": row["verification_state"] if "verification_state" in row.keys() else "unverified",
            "is_replayed": bool(row["is_replayed"]) if "is_replayed" in row.keys() else False,
            "receipt_id": row["receipt_id"] if "receipt_id" in row.keys() else "",
            "schema_version": row["schema_version"] if "schema_version" in row.keys() else 1,
        }
