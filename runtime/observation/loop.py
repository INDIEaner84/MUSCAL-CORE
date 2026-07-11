import logging
import threading
import time
from typing import Any, Optional

import config
from runtime.database import _table_has_column, get_connection
from runtime.kernel.writer import WriterThread
from runtime.llm.client import ollama_keepalive

log = logging.getLogger("muscal.observation")

_governance: Any = None


def set_governance(g: Any) -> None:
    global _governance
    _governance = g


class ObservationLoop(threading.Thread):
    def __init__(self, writer: WriterThread, db_path: str = config.DB_PATH):
        super().__init__(name="muscal-observation", daemon=True)
        self._writer = writer
        self._db_path = db_path
        self._stopevent = threading.Event()
        self.last_tick: Optional[float] = None
        self.tick_count = 0
        self._keepalive_counter = 0

    def run(self) -> None:
        log.info("ObservationLoop started")
        while not self._stopevent.wait(config.OBSERVATION_INTERVAL):
            try:
                self._tick()
                self.last_tick = time.time()
                self.tick_count += 1
                self._keepalive_counter += 1
                if self._keepalive_counter >= 12:
                    self._keepalive_counter = 0
                    self._keepalive_ping()
            except Exception as exc:
                log.error("ObservationLoop error (continuing): %s", exc)
                self._writer.submit({
                    "type": "observation.loop_error", "domain": "observation",
                    "layer": "L2", "stream": "event", "severity": "error",
                    "actor": "obs_loop", "actor_type": "monitor",
                    "session_id": config.SESSION_ID,
                    "payload": {"error": str(exc)},
                })

    def _keepalive_ping(self) -> None:
        ollama_keepalive(config.QWEN_MODEL)

    def _tick(self) -> None:
        conn = get_connection(self._db_path)
        try:
            blocking_open = conn.execute("""
                SELECT COUNT(*) as n FROM intent_unknowns
                WHERE is_blocking=1 AND resolved=0
            """).fetchone()["n"]

            stuck = conn.execute("""
                SELECT id, current_task FROM workers
                WHERE status='running'
                AND started_at < datetime('now', '-5 minutes')
            """).fetchall() if _table_has_column(conn, "workers", "started_at") else []

            decisions = conn.execute("""
                SELECT AVG(confidence) as avg_conf, MIN(confidence) as min_conf
                FROM decisions WHERE made_at > datetime('now', '-10 minutes')
            """).fetchone()

            drift_detected = (
                decisions["avg_conf"] is not None and
                decisions["min_conf"] is not None and
                (decisions["avg_conf"] - decisions["min_conf"]) > 0.3
            )

            governance_violations = 0
            if _governance is not None:
                governance_violations = len(_governance.get_violations())

            if blocking_open > 0 or stuck or drift_detected or governance_violations > 0:
                self._writer.submit({
                    "type": "observation.anomaly_detected",
                    "domain": "observation", "layer": "L2",
                    "stream": "event", "severity": "warn",
                    "actor": "obs_loop", "actor_type": "monitor",
                    "session_id": config.SESSION_ID,
                    "payload": {
                        "blocking_unknowns": blocking_open,
                        "stuck_workers": [dict(r) for r in stuck],
                        "confidence_drift": drift_detected,
                        "governance_violations": governance_violations,
                    },
                })
        finally:
            conn.close()

    def health(self) -> dict:
        lag = (time.time() - self.last_tick) if self.last_tick else None
        return {
            "alive": self.is_alive(),
            "tick_count": self.tick_count,
            "lag_s": round(lag, 1) if lag else None,
            "status": "ok" if lag and lag < 30 else ("stale" if lag else "starting"),
        }

    def stop(self) -> None:
        self._stopevent.set()
        if threading.current_thread() is not self:
            self.join(timeout=10)
