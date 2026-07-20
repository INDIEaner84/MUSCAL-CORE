import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from runtime.database import get_connection


class EventStore:
    """Append-only SQLite-backed event persistence with cursor-based replay."""

    def __init__(self, db_path: Optional[Path] = None):
        if db_path is None:
            from config import DB_PATH
            db_path = DB_PATH
        self._db_path = Path(db_path)
        self._conn = get_connection(self._db_path)
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
                created_at TEXT NOT NULL
            )"""
        )
        self._conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_stored_events_topic ON stored_events(topic)"
        )
        self._conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_stored_events_created ON stored_events(created_at)"
        )
        self._conn.commit()

    def append(self, event: Dict[str, Any]) -> Optional[int]:
        """Append a single event. Returns the assigned seq.

        Returns None if event is suppressed (replay marker).
        Raises sqlite3.IntegrityError on duplicate event_id.
        """
        import time
        import datetime

        payload = event.get("payload", {})
        if isinstance(payload, dict) and payload.get("_replayed"):
            return None
        if not isinstance(payload, str):
            payload = json.dumps(payload, ensure_ascii=False, sort_keys=False)

        priority = event.get("priority", "NORMAL")
        if hasattr(priority, "name"):
            priority = priority.name

        ts = event.get("timestamp", time.time())
        created_at = datetime.datetime.now(datetime.timezone.utc).isoformat()

        cursor = self._conn.execute(
            """INSERT INTO stored_events
               (topic, payload, source, priority, timestamp, event_id, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (
                event.get("topic", ""),
                payload,
                event.get("source", ""),
                str(priority),
                float(ts),
                event.get("id", ""),
                created_at,
            ),
        )
        self._conn.commit()
        return cursor.lastrowid

    def replay(
        self,
        cursor: Optional[int] = None,
        topic: Optional[str] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """Replay events. cursor is last_seen_seq (seq > cursor)."""
        if limit <= 0:
            raise ValueError("limit must be positive")

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
        row = self._conn.execute(
            "SELECT MAX(seq) AS max_seq FROM stored_events"
        ).fetchone()
        return row["max_seq"] if row and row["max_seq"] is not None else 0

    def event_count(self, topic: Optional[str] = None) -> int:
        """Count events, optionally filtered by topic."""
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
        }
