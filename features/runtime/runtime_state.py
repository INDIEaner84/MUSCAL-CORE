from __future__ import annotations

import time
from datetime import datetime, timezone
from typing import Optional

from runtime.event_store import EventStore

from .models import RuntimeState, RUNTIME_EVENTS
from .observability import RuntimeObservability


class RuntimeStateProjection:

    def __init__(self, event_store: Optional[EventStore] = None,
                 observability: Optional[RuntimeObservability] = None):
        self._store = event_store
        self._observability = observability or RuntimeObservability(event_store)
        self._last_health: Optional[str] = None

    def compute(self) -> RuntimeState:
        state = RuntimeState()
        if self._store is None:
            state.health = "unknown"
            return state

        session_events = self._store.replay(topic="runtime.session.created", limit=1000)
        update_events = self._store.replay(topic="runtime.session.updated", limit=1000)
        execution_events = self._store.replay(topic="runtime.execution.started", limit=1000)
        completed = self._store.replay(topic="runtime.execution.completed", limit=1000)
        failed = self._store.replay(topic="runtime.execution.failed", limit=1000)
        interrupted = self._store.replay(topic="runtime.execution.interrupted", limit=1000)
        last = self._store.replay(topic=None, limit=1)

        session_map: dict[str, str] = {}
        for ev in session_events:
            sid = ev.get("payload", {}).get("session", {}).get("id", "")
            if sid:
                session_map[sid] = "CREATED"

        for ev in update_events:
            sid = ev.get("payload", {}).get("session", {}).get("id", "")
            status = ev.get("payload", {}).get("session", {}).get("status", "")
            if sid:
                session_map[sid] = status

        active = [{"id": sid, "status": st} for sid, st in session_map.items()
                   if st in {"CREATED", "RUNNING", "PAUSED", "RECOVERING"}]
        state.active_sessions = active

        inter_count = sum(1 for st in session_map.values() if st == "INTERRUPTED")
        state.interrupted_sessions = inter_count

        running = []
        for ev in execution_events:
            eid = ev.get("payload", {}).get("execution_id", "")
            if eid and not any(
                c.get("payload", {}).get("execution_id") == eid
                for c in list(completed) + list(failed)
            ):
                running.append(eid)
        state.running_executions = running

        state.failed_executions = len(failed)

        if last:
            evt = last[0]
            state.last_event = {
                "topic": evt.get("topic", ""),
                "timestamp": evt.get("timestamp", 0),
                "id": evt.get("id", ""),
            }
            state.event_lag = time.time() - evt.get("timestamp", time.time())

        recovery_completed = self._store.replay(topic="runtime.recovery.completed", limit=1)
        recovery_started = self._store.replay(topic="runtime.recovery.started", limit=1)

        if recovery_completed:
            state.recovery_status = "completed"
            last_recovery = recovery_completed[-1].get("payload", {}).get("result", "")
            if last_recovery:
                state.recovery_status = f"completed:{last_recovery}"
        elif recovery_started:
            state.recovery_status = "in_progress"
        else:
            state.recovery_status = "none"

        failed_count = state.failed_executions
        new_health = "healthy"
        if failed_count > 5:
            new_health = "degraded"
        if failed_count > 10:
            new_health = "down"
        if state.interrupted_sessions > 0:
            new_health = "degraded"

        state.health = new_health

        if self._last_health is not None and self._last_health != new_health:
            self._observability.emit(
                "runtime.health.changed",
                {"from": self._last_health, "to": new_health,
                 "failed_executions": failed_count,
                 "interrupted_sessions": state.interrupted_sessions},
            )
        self._last_health = new_health

        return state

    def get_health(self) -> str:
        return self.compute().health
