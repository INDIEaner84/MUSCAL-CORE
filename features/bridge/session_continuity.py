from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional

from .project_scanner import ProjectContext
from .task_contract import TaskContract


@dataclass
class ExecutionRecord:
    bridge_execution_id: str
    opencode_session_id: Optional[str]
    project_identity: dict
    task_identity: dict
    checkpoint: Optional[str]
    previous_execution: Optional[str]
    next_action: str
    timestamp: str
    status: str

    def to_dict(self) -> dict:
        return {
            "execution_record": {
                "bridge_execution_id": self.bridge_execution_id,
                "opencode_session_id": self.opencode_session_id,
                "project_identity": self.project_identity,
                "task_identity": self.task_identity,
                "checkpoint": self.checkpoint,
                "previous_execution": self.previous_execution,
                "next_action": self.next_action,
                "timestamp": self.timestamp,
                "status": self.status,
            }
        }


class SessionContinuityTracker:

    def __init__(self, storage_dir: Optional[str] = None):
        self._storage_dir = storage_dir
        self._execution_history: list[ExecutionRecord] = []

    def record_execution(
        self,
        project: ProjectContext,
        task: TaskContract,
        opencode_session: Optional[str],
        checkpoint: Optional[str] = None,
        previous_execution: Optional[str] = None,
        status: str = "completed",
    ) -> ExecutionRecord:
        execution_id = str(uuid.uuid4())
        record = ExecutionRecord(
            bridge_execution_id=execution_id,
            opencode_session_id=opencode_session,
            project_identity={
                "root": str(project.root),
                "branch": project.branch,
                "commit": project.commit,
            },
            task_identity=task.to_dict(),
            checkpoint=checkpoint,
            previous_execution=previous_execution,
            next_action="",
            timestamp=datetime.now(timezone.utc).isoformat(),
            status=status,
        )
        self._execution_history.append(record)
        return record

    def update_next_action(self, execution_id: str, action: str) -> None:
        for record in self._execution_history:
            if record.bridge_execution_id == execution_id:
                record.next_action = action
                break

    def get_last_execution(self) -> Optional[ExecutionRecord]:
        if self._execution_history:
            return self._execution_history[-1]
        return None

    def get_execution(self, execution_id: str) -> Optional[ExecutionRecord]:
        for record in self._execution_history:
            if record.bridge_execution_id == execution_id:
                return record
        return None

    def get_history(self) -> list[ExecutionRecord]:
        return list(self._execution_history)

    def clear_history(self) -> None:
        self._execution_history.clear()
