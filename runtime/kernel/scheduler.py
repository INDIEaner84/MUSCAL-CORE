import logging
import threading
from pathlib import Path
from typing import Optional

import config
from runtime.database import get_connection

log = logging.getLogger("muscal.scheduler")


class RoutingPolicy:
    def __init__(self, db_path: Path = config.DB_PATH):
        self._db_path = db_path
        self._rules: dict[str, str] = {}
        self._lock = threading.RLock()
        self.reload()

    def reload(self) -> None:
        conn = get_connection(self._db_path)
        rows = conn.execute("SELECT task_type, worker_id FROM routing_policy").fetchall()
        conn.close()
        with self._lock:
            self._rules = {r["task_type"]: r["worker_id"] for r in rows}
        log.info("RoutingPolicy loaded: %d rules", len(self._rules))

    def route(self, task_type: str) -> str:
        with self._lock:
            return self._rules.get(task_type, self._rules.get("routing", "qwen_router"))

    @property
    def rules(self) -> dict[str, str]:
        with self._lock:
            return dict(self._rules)
