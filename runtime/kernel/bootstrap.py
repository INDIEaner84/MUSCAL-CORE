import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import config
from runtime.database import get_connection
from runtime.kernel.writer import WriterThread

log = logging.getLogger("muscal.bootstrap")

SEED_WORKERS = [
    {"id": "qwen_router",   "model": config.QWEN_MODEL,  "type": "router"},
    {"id": "r1_reflection", "model": config.R1_MODEL,    "type": "reflection"},
]

DEFAULT_ROUTING = [
    ("reasoning",  "r1_reflection"),
    ("routing",    "qwen_router"),
]


def detect_bootstrap_needed(db_path: Path = config.DB_PATH) -> bool:
    try:
        conn = get_connection(db_path)
        count = conn.execute("SELECT COUNT(*) FROM events WHERE type = 'kernel.initialized'").fetchone()[0]
        conn.close()
        return count == 0
    except Exception:
        return True


def bootstrap_kernel(writer: WriterThread) -> None:
    log.info("Bootstrapping kernel for session %s", config.SESSION_ID)
    now = datetime.now(timezone.utc).isoformat()

    def seed_workers(conn):
        for w in SEED_WORKERS:
            conn.execute(
                "INSERT OR REPLACE INTO workers (id, model, status, registered_at) VALUES (?,?,?,?)",
                [w["id"], w["model"], "idle", now]
            )
        for task_type, worker_id in DEFAULT_ROUTING:
            conn.execute(
                "INSERT OR REPLACE INTO routing_policy (task_type, worker_id, updated_by, updated_at) VALUES (?,?,?,?)",
                [task_type, worker_id, "bootstrap", now]
            )

    writer.submit_and_wait({
        "type": "kernel.initialized", "domain": "system", "layer": "kernel",
        "stream": "event", "trust_level": 3, "actor": "bootstrap",
        "actor_type": "kernel", "session_id": config.SESSION_ID,
        "payload": {"kernel_version": "0.1", "session_id": config.SESSION_ID},
        "idempotency_key": f"bootstrap_{config.SESSION_ID}",
    }, transaction_fn=seed_workers)

    log.info("Bootstrap complete: %d workers, %d routing rules", len(SEED_WORKERS), len(DEFAULT_ROUTING))
