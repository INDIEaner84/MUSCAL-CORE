import logging

import config
from runtime.database import get_connection

log = logging.getLogger("muscal.services")


def create_snapshot(writer) -> dict:
    conn = get_connection(config.DB_PATH)
    try:
        last_seq = conn.execute("SELECT value FROM sequences WHERE name='events'").fetchone()
        event_count = conn.execute("SELECT COUNT(*) FROM events").fetchone()[0]
        snapshot_data = {
            "seq": last_seq[0] if last_seq else 0,
            "event_count": event_count,
        }

        def _tx(conn):
            from datetime import datetime, timezone
            conn.execute("""
                INSERT INTO snapshots (last_seq, state_json, event_count, created_at)
                VALUES (?, ?, ?, ?)
            """, [
                snapshot_data["seq"],
                "{}",
                snapshot_data["event_count"],
                datetime.now(timezone.utc).isoformat(),
            ])

        writer.submit({
            "type": "system.snapshot_taken",
            "domain": "system", "layer": "kernel",
            "stream": "event", "trust_level": 2,
            "actor": "snapshot_mgr", "actor_type": "kernel",
            "session_id": config.SESSION_ID,
            "payload": snapshot_data,
        }, transaction_fn=_tx)
        return {"status": "queued"}
    finally:
        conn.close()
