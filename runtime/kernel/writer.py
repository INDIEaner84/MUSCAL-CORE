import json
import logging
import queue
import sqlite3
import threading
import time
import uuid
from concurrent.futures import Future
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Optional

import config
from runtime.database import _next_seq, get_connection

log = logging.getLogger("muscal.writer")

WRITER_TIMEOUT = 5.0
_snapshot_mgr = None

_SEVERITY_TO_PRIORITY = {
    "debug": "LOW", "info": "NORMAL",
    "warn": "HIGH", "error": "CRITICAL", "critical": "CRITICAL",
}


def set_snapshot_manager(mgr: Any) -> None:
    global _snapshot_mgr
    _snapshot_mgr = mgr


def get_snapshot_manager() -> Any:
    return _snapshot_mgr


@dataclass
class WriteCommand:
    event: dict
    transaction_fn: Optional[Callable] = None
    future: Future = field(default_factory=Future)


class WriterThread(threading.Thread):
    """Compatibility adapter: delegates canonical persistence to EventStore,
    then writes a derived copy to the `events` table for legacy readers."""

    def __init__(self, db_path: Path = config.DB_PATH, event_store=None):
        super().__init__(name="muscal-writer", daemon=True)
        self.db_path = db_path
        self.event_store = event_store
        self._queue: queue.Queue[Optional[WriteCommand]] = queue.Queue()
        self._stopevent = threading.Event()
        self._event_count_since_snapshot = 0
        self._conn: Optional[sqlite3.Connection] = None

    def run(self) -> None:
        self._conn = get_connection(self.db_path)
        log.info("WriterThread started")
        while not self._stopevent.is_set():
            try:
                cmd = self._queue.get(timeout=1.0)
            except queue.Empty:
                continue
            if cmd is None:
                break
            self._process(cmd)
            self._queue.task_done()
        if self._conn:
            self._conn.close()
        log.info("WriterThread stopped")

    def _process(self, cmd: WriteCommand) -> None:
        try:
            result = self._write_atomic(cmd)
            cmd.future.set_result(result)
        except Exception as exc:
            log.error("WriterThread error: %s", exc)
            cmd.future.set_exception(exc)

    @staticmethod
    def _map_to_stored_event(ev: dict) -> dict:
        caused_by = ev.get("caused_by", [])
        if isinstance(caused_by, list):
            causation_id = caused_by[0] if caused_by else ""
        else:
            causation_id = str(caused_by)
        severity = ev.get("severity", "info")
        priority = _SEVERITY_TO_PRIORITY.get(severity, "NORMAL")
        return {
            "topic": ev.get("type", ev.get("topic", "unknown")),
            "payload": ev.get("payload", {}),
            "source": ev.get("actor", "kernel"),
            "priority": priority,
            "timestamp": time.time(),
            "id": ev.get("idempotency_key", str(uuid.uuid4())),
            "execution_id": ev.get("execution_id", ""),
            "correlation_id": ev.get("correlation_id", ""),
            "causation_id": causation_id,
            "execution_mode": ev.get("execution_mode", "real"),
            "execution_state": ev.get("execution_state", "planned"),
            "verification_state": ev.get("verification_state", "unverified"),
        }

    def _write_atomic(self, cmd: WriteCommand) -> dict:
        conn = self._conn
        ev = cmd.event
        now = datetime.now(timezone.utc).isoformat()

        # CANONICAL: persist to EventStore first (separate connection, own transaction)
        if self.event_store is not None:
            mapped = self._map_to_stored_event(ev)
            try:
                self.event_store.append(mapped)
            except sqlite3.IntegrityError:
                # Duplicate event_id — log and fall through to idempotency check
                log.warning("EventStore duplicate event_id (may be idempotent retry)")
            except Exception as exc:
                log.error("EventStore canonical write failed: %s", exc)
                raise

        # DERIVED: legacy events-table write inside its own transaction
        conn.execute("BEGIN IMMEDIATE")
        try:
            seq = _next_seq(conn)
            idem_key = ev.get("idempotency_key")
            if idem_key:
                existing = conn.execute(
                    "SELECT seq FROM events WHERE idempotency_key = ?", [idem_key]
                ).fetchone()
                if existing:
                    conn.execute("ROLLBACK")
                    return {"seq": existing["seq"], "duplicate": True}

            tx_result = None
            if cmd.transaction_fn:
                tx_result = cmd.transaction_fn(conn)
                if tx_result is False:
                    conn.execute("ROLLBACK")
                    return {"seq": None, "blocked": True}

            conn.execute("""
                INSERT INTO events (
                    seq, ts, occurred_at, type, actor, actor_type,
                    domain, layer, stream, session_id,
                    payload, caused_by, schema_version,
                    idempotency_key, model_id, confidence,
                    trust_level, severity, aggregate_id, aggregate_type,
                    replayable, payload_sanitized
                ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            """, [
                seq, now,
                ev.get("occurred_at", now),
                ev["type"],
                ev.get("actor", "kernel"),
                ev.get("actor_type", "worker"),
                ev.get("domain", "system"),
                ev.get("layer", "kernel"),
                ev.get("stream", "event"),
                ev.get("session_id", "default"),
                json.dumps(ev.get("payload", {})),
                json.dumps(ev.get("caused_by", [])),
                ev.get("schema_version", 1),
                idem_key,
                ev.get("model_id"),
                ev.get("confidence"),
                ev.get("trust_level", 1),
                ev.get("severity", "info"),
                ev.get("aggregate_id"),
                ev.get("aggregate_type"),
                ev.get("replayable", 1),
                ev.get("payload_sanitized", 0),
            ])
            conn.execute("COMMIT")
            return {"seq": seq, "tx_result": tx_result}
        except Exception:
            conn.execute("ROLLBACK")
            raise

    def submit(self, event: dict, transaction_fn: Optional[Callable] = None) -> Future:
        cmd = WriteCommand(event=event, transaction_fn=transaction_fn)
        self._queue.put(cmd)
        return cmd.future

    def submit_and_wait(self, event: dict, transaction_fn: Optional[Callable] = None,
                        timeout: float = WRITER_TIMEOUT) -> dict:
        return self.submit(event, transaction_fn).result(timeout=timeout)

    def stop(self) -> None:
        self._stopevent.set()
        self._queue.put(None)
        if threading.current_thread() is not self:
            self.join(timeout=10)
