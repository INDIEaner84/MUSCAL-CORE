from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional

from runtime.event_store import EventStore

from .models import Session, SESSION_STATES
from .observability import RuntimeObservability


class SessionManager:

    def __init__(self, event_store: Optional[EventStore] = None,
                 observability: Optional[RuntimeObservability] = None):
        self._store = event_store
        self._observability = observability or RuntimeObservability(event_store)
        self._sessions: dict[str, Session] = {}

    def create_session(
        self,
        task_id: str,
        project_id: str,
        execution_id: str = "",
        opencode_session_id: Optional[str] = None,
    ) -> Session:
        session_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc).isoformat()
        session = Session(
            session_id=session_id,
            execution_id=execution_id or str(uuid.uuid4()),
            task_id=task_id,
            project_id=project_id,
            opencode_session_id=opencode_session_id,
            status="CREATED",
            created_at=now,
            updated_at=now,
        )
        self._sessions[session_id] = session
        self._observability.emit_session_created(session)
        return session

    def update_session(self, session_id: str, status: str,
                        opencode_session_id: Optional[str] = None) -> Optional[Session]:
        session = self._sessions.get(session_id)
        if session is None:
            return None
        if status not in SESSION_STATES:
            raise ValueError(f"Invalid session state '{status}'. Must be one of: {sorted(SESSION_STATES)}")
        session.status = status
        session.updated_at = datetime.now(timezone.utc).isoformat()
        if opencode_session_id is not None:
            session.opencode_session_id = opencode_session_id
        self._observability.emit_session_updated(session)
        return session

    def complete_session(self, session_id: str) -> Optional[Session]:
        return self.update_session(session_id, "COMPLETED")

    def fail_session(self, session_id: str) -> Optional[Session]:
        return self.update_session(session_id, "FAILED")

    def interrupt_session(self, session_id: str, reason: str = "") -> Optional[Session]:
        session = self._sessions.get(session_id)
        if session is None:
            return None
        session.status = "INTERRUPTED"
        session.updated_at = datetime.now(timezone.utc).isoformat()
        self._observability.emit_session_updated(session)
        self._observability.emit_execution_interrupted(
            session.execution_id, session.task_id, session_id, reason,
        )
        return session

    def get_session(self, session_id: str) -> Optional[Session]:
        return self._sessions.get(session_id)

    def list_active_sessions(self) -> list[Session]:
        return [s for s in self._sessions.values() if s.status in {"CREATED", "RUNNING", "PAUSED", "RECOVERING"}]

    def lookup_by_task(self, task_id: str) -> list[Session]:
        return [s for s in self._sessions.values() if s.task_id == task_id]

    def lookup_by_execution(self, execution_id: str) -> list[Session]:
        return [s for s in self._sessions.values() if s.execution_id == execution_id]

    def has_active_execution(self, task_id: str) -> bool:
        return any(
            s.task_id == task_id and s.status in {"CREATED", "RUNNING", "PAUSED", "RECOVERING"}
            for s in self._sessions.values()
        )

    def all_sessions(self) -> list[Session]:
        return list(self._sessions.values())

    def clear(self) -> None:
        self._sessions.clear()

    def detect_interrupted(self) -> list[Session]:
        interrupted = []
        for session in self._sessions.values():
            if session.status in {"RUNNING", "CREATED"}:
                self.interrupt_session(session.session_id, "Detected during recovery — execution did not complete")
                interrupted.append(session)
        return interrupted

    def recover_sessions(self) -> int:
        if self._store is None:
            return 0
        session_events = self._store.replay(topic="runtime.session.created", limit=1000)
        update_events = self._store.replay(topic="runtime.session.updated", limit=1000)
        self._sessions.clear()

        for ev in session_events:
            sd = ev.get("payload", {}).get("session", {})
            if sd.get("id"):
                self._sessions[sd["id"]] = Session(
                    session_id=sd["id"],
                    execution_id=sd.get("execution_id", ""),
                    task_id=sd.get("task_id", ""),
                    project_id=sd.get("project_id", ""),
                    opencode_session_id=sd.get("opencode_session_id"),
                    status=sd.get("status", "CREATED"),
                    created_at=sd.get("created_at", ""),
                    updated_at=sd.get("updated_at", ""),
                    last_checkpoint=sd.get("last_checkpoint"),
                )

        for ev in update_events:
            sd = ev.get("payload", {}).get("session", {})
            sid = sd.get("id", "")
            if sid in self._sessions:
                self._sessions[sid].status = sd.get("status", self._sessions[sid].status)
                self._sessions[sid].updated_at = sd.get("updated_at", self._sessions[sid].updated_at)
                if sd.get("last_checkpoint"):
                    self._sessions[sid].last_checkpoint = sd["last_checkpoint"]

        count = len(self._sessions)
        interrupted = self.detect_interrupted()
        for s in interrupted:
            self._observability.emit_session_restored(s)

        return count
