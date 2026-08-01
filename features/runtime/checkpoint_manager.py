from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional

from runtime.event_store import EventStore

from .models import Checkpoint, CHECKPOINT_STATUS
from .observability import RuntimeObservability


class CheckpointManager:

    def __init__(self, event_store: Optional[EventStore] = None,
                 observability: Optional[RuntimeObservability] = None):
        self._store = event_store
        self._observability = observability or RuntimeObservability(event_store)
        self._checkpoints: dict[str, Checkpoint] = {}

    def create_checkpoint(
        self,
        execution_id: str,
        task_id: str,
        project: str,
        git_commit: str,
        session_id: str,
        state_reference: Optional[str] = None,
    ) -> Checkpoint:
        checkpoint_id = str(uuid.uuid4())
        checkpoint = Checkpoint(
            checkpoint_id=checkpoint_id,
            execution_id=execution_id,
            task_id=task_id,
            project=project,
            git_commit=git_commit,
            session_id=session_id,
            timestamp=datetime.now(timezone.utc).isoformat(),
            state_reference=state_reference,
        )
        self._checkpoints[checkpoint_id] = checkpoint
        self._observability.emit_checkpoint_created(checkpoint)
        return checkpoint

    def get_checkpoint(self, checkpoint_id: str) -> Optional[Checkpoint]:
        return self._checkpoints.get(checkpoint_id)

    def list_checkpoints(self, execution_id: Optional[str] = None) -> list[Checkpoint]:
        if execution_id is None:
            return list(self._checkpoints.values())
        return [c for c in self._checkpoints.values() if c.execution_id == execution_id]

    def latest_checkpoint(self, execution_id: str) -> Optional[Checkpoint]:
        candidates = [c for c in self._checkpoints.values() if c.execution_id == execution_id]
        if not candidates:
            return None
        return max(candidates, key=lambda c: c.timestamp)

    def mark_checkpoint_unavailable(self, checkpoint_id: str) -> Optional[Checkpoint]:
        cp = self._checkpoints.get(checkpoint_id)
        if cp is None:
            return None
        cp.status = "unavailable"
        return cp

    def clear(self) -> None:
        self._checkpoints.clear()

    def recover_checkpoints(self) -> int:
        if self._store is None:
            return 0
        cp_events = self._store.replay(topic="runtime.checkpoint.created", limit=1000)
        self._checkpoints.clear()

        for ev in cp_events:
            cd = ev.get("payload", {}).get("checkpoint", {})
            if cd.get("id"):
                cid = cd["id"]
                status = cd.get("status", "available")
                if status not in CHECKPOINT_STATUS:
                    status = "unknown"
                self._checkpoints[cid] = Checkpoint(
                    checkpoint_id=cid,
                    execution_id=cd.get("execution_id", ""),
                    task_id=cd.get("task_id", ""),
                    project=cd.get("project", ""),
                    git_commit=cd.get("git_commit", ""),
                    session_id=cd.get("session_id", ""),
                    timestamp=cd.get("timestamp", ""),
                    state_reference=cd.get("state_reference"),
                    status=status,
                )

        return len(self._checkpoints)
