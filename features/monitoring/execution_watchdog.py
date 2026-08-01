import logging
import time
import threading
from typing import Optional

logger = logging.getLogger(__name__)

DEFAULT_ORPHAN_TIMEOUT = 300.0
DEFAULT_POLL_INTERVAL = 30.0


class ExecutionWatchdog:
    def __init__(
        self,
        event_store=None,
        event_bus=None,
        orphan_timeout: float = DEFAULT_ORPHAN_TIMEOUT,
        poll_interval: float = DEFAULT_POLL_INTERVAL,
    ):
        self._event_store = event_store
        self._event_bus = event_bus
        self._orphan_timeout = orphan_timeout
        self._poll_interval = poll_interval
        self._watchdog_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._warnings_issued = 0
        self._orphans_resolved = 0

    def start(self) -> None:
        if self._watchdog_thread is not None:
            return
        self._stop_event.clear()
        self._watchdog_thread = threading.Thread(
            target=self._watchdog_loop,
            name="execution-watchdog",
            daemon=True,
        )
        self._watchdog_thread.start()
        logger.info(
            "ExecutionWatchdog started (timeout=%ss, poll=%ss)",
            self._orphan_timeout,
            self._poll_interval,
        )

    def stop(self) -> None:
        self._stop_event.set()
        if self._watchdog_thread is not None:
            self._watchdog_thread.join(timeout=5)
            self._watchdog_thread = None
        logger.info("ExecutionWatchdog stopped")

    def _watchdog_loop(self) -> None:
        while not self._stop_event.is_set():
            try:
                self._scan_for_orphans()
            except Exception:
                logger.exception("ExecutionWatchdog scan failed")
            self._stop_event.wait(timeout=self._poll_interval)

    def _scan_for_orphans(self) -> None:
        if self._event_store is None:
            return

        try:
            cursor = self._event_store.get_cursor()
        except Exception:
            return

        if cursor == 0:
            return

        try:
            events = self._event_store.replay(cursor=0, limit=5000)
        except Exception:
            logger.warning("ExecutionWatchdog: cannot replay event store")
            return

        running_by_execution: dict[str, dict] = {}
        for ev in events:
            eid = ev.get("execution_id", "")
            if not eid:
                continue
            state = ev.get("execution_state", "")
            if state == "running":
                running_by_execution[eid] = ev
            elif state in ("completed", "failed", "cancelled"):
                running_by_execution.pop(eid, None)

        now = time.time()
        for eid, ev in running_by_execution.items():
            ts = ev.get("timestamp", 0)
            elapsed = now - ts
            if elapsed > self._orphan_timeout:
                self._force_fail_orphan(eid, ev, elapsed)

    def _force_fail_orphan(self, execution_id: str, event: dict, elapsed: float) -> None:
        from event_bus import EventPriority

        self._orphans_resolved += 1
        self._warnings_issued += 1
        logger.warning(
            "Orphan execution %s stuck in 'running' for %.1fs — forcing FAILED",
            execution_id,
            elapsed,
        )

        if self._event_bus is not None:
            self._event_bus.publish(
                "EXECUTION_FAILED",
                {
                    "execution_id": execution_id,
                    "error": f"ORPHAN_DETECTED: execution stuck in 'running' for {elapsed:.1f}s",
                    "execution_state": "failed",
                    "execution_mode": event.get("execution_mode", "real"),
                    "verification_state": "unverified",
                },
                source="ExecutionWatchdog",
                priority=EventPriority.HIGH,
            )

    def stats(self) -> dict:
        return {
            "orphans_resolved": self._orphans_resolved,
            "warnings_issued": self._warnings_issued,
            "orphan_timeout": self._orphan_timeout,
            "poll_interval": self._poll_interval,
            "running": self._watchdog_thread is not None and self._watchdog_thread.is_alive(),
        }
