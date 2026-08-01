from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from runtime.event_store import EventStore

from ..bridge.orchestrator import run_bridge, BridgeConfig, BridgeOutput
from ..bridge.project_scanner import ProjectScanner
from ..bridge.task_contract import TaskContract
from ..execution_guard.models import AutonomyLevel
from .models import RuntimeConfig, ApprovalPolicy
from .session_manager import SessionManager
from .checkpoint_manager import CheckpointManager
from .runtime_state import RuntimeStateProjection
from ..knowledge.extractor import KnowledgeExtractor
from ..knowledge.validator import KnowledgeValidator
from ..knowledge.knowledge_writer import KnowledgeWriter
from .observability import RuntimeObservability


@dataclass
class RuntimeOutput:
    session_id: str
    checkpoint_id: Optional[str]
    bridge_output: Optional[BridgeOutput]
    status: str
    errors: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "runtime_output": {
                "session_id": self.session_id,
                "checkpoint_id": self.checkpoint_id,
                "status": self.status,
                "errors": self.errors,
            }
        }


@dataclass
class RecoveryResult:
    sessions_recovered: int
    checkpoints_recovered: int
    interrupted_sessions: int
    status: str

    def to_dict(self) -> dict:
        return {
            "recovery_result": {
                "sessions_recovered": self.sessions_recovered,
                "checkpoints_recovered": self.checkpoints_recovered,
                "interrupted_sessions": self.interrupted_sessions,
                "status": self.status,
            }
        }


class RuntimeCoordinator:

    def __init__(self, config: Optional[RuntimeConfig] = None,
                 event_store: Optional[EventStore] = None):
        self._config = config or RuntimeConfig()
        self._store = event_store
        self._observability = RuntimeObservability(event_store)
        self._session_manager = SessionManager(event_store, self._observability)
        self._checkpoint_manager = CheckpointManager(event_store, self._observability)
        self._state_projection = RuntimeStateProjection(event_store, self._observability)

    def execute(
        self,
        message: str,
        task: Optional[TaskContract] = None,
        workdir: Optional[Path] = None,
        autonomy_level: Optional[str] = None,
    ) -> RuntimeOutput:
        tid = task.id if task else str(uuid.uuid4())
        errors: list[str] = []

        target = workdir or Path.cwd()
        try:
            scanner = ProjectScanner(target)
            context = scanner.scan()
            project_id = str(context.root)
            git_commit = context.commit
            project = context.repository
        except Exception as e:
            project_id = str(target)
            git_commit = "unknown"
            project = "unknown"

        session = self._session_manager.create_session(
            task_id=tid,
            project_id=project_id,
        )
        session_id = session.session_id
        execution_id = session.execution_id

        self._observability.emit_execution_started(execution_id, tid, session_id)

        checkpoint = self._checkpoint_manager.create_checkpoint(
            execution_id=execution_id,
            task_id=tid,
            project=project,
            git_commit=git_commit,
            session_id=session_id,
            state_reference=f"pre:{git_commit}",
        )
        checkpoint_id = checkpoint.checkpoint_id

        self._session_manager.update_session(session_id, "RUNNING")
        session.last_checkpoint = checkpoint_id

        level_str = (autonomy_level or self._config.autonomy_level).upper()
        try:
            level_enum = AutonomyLevel(f"A{level_str}" if level_str.isdigit() else level_str)
        except ValueError:
            level_enum = AutonomyLevel.A3_MODIFY_AND_TEST

        cfg = BridgeConfig(
            workdir=target,
            autonomy_level=level_enum,
            max_retries=self._config.max_retries,
            verification_required=self._config.verification_required,
        )

        bridge_output = run_bridge(
            message=message,
            task=task,
            config=cfg,
        )

        if bridge_output.status == "completed":
            self._session_manager.update_session(session_id, "COMPLETED")
            self._observability.emit_execution_completed(execution_id, tid, session_id)
            self._process_knowledge(bridge_output, task, execution_id, tid)
        else:
            self._session_manager.update_session(session_id, "FAILED")
            self._observability.emit_execution_failed(
                execution_id, tid, session_id,
                error="; ".join(bridge_output.errors) if bridge_output.errors else "Unknown error",
            )
            errors = bridge_output.errors

        return RuntimeOutput(
            session_id=session_id,
            checkpoint_id=checkpoint_id,
            bridge_output=bridge_output,
            status=bridge_output.status,
            errors=errors,
        )

    def _process_knowledge(self, bridge_output: Any, task: Optional[TaskContract],
                           execution_id: str, task_id: str) -> None:
        try:
            extractor = KnowledgeExtractor()
            validator = KnowledgeValidator()
            writer = KnowledgeWriter(event_emitter=self._observability)
            candidate = extractor.extract(bridge_output, task=task)
            if candidate is None:
                return
            self._observability.emit_knowledge_candidate_created(
                candidate, execution_id=execution_id, task_id=task_id,
            )
            is_valid, reasons = validator.validate(candidate)
            if is_valid:
                state = validator.evaluate(candidate)
                if state.name == "VALIDATED":
                    writer.write_validated(candidate)
                    self._observability.emit_knowledge_candidate_validated(
                        candidate, execution_id=execution_id, task_id=task_id,
                    )
                else:
                    writer.write_candidate(candidate)
            else:
                writer.write_candidate(candidate)
        except Exception:
            pass

    def recover_runtime(self) -> RecoveryResult:
        self._observability.emit(
            "runtime.recovery.started",
            {"message": "Runtime recovery initiated"},
        )
        sessions_count = self._session_manager.recover_sessions()
        checkpoints_count = self._checkpoint_manager.recover_checkpoints()
        interrupted = self._session_manager.list_active_sessions()
        interrupted_active = [s for s in interrupted if s.status == "INTERRUPTED"]

        self._observability.emit_recovery_completed(
            execution_id="",
            result=f"recovered:{sessions_count}_sessions:{checkpoints_count}_checkpoints",
        )

        return RecoveryResult(
            sessions_recovered=sessions_count,
            checkpoints_recovered=checkpoints_count,
            interrupted_sessions=len(interrupted_active),
            status="completed",
        )

    def get_approval_policy(self, level: Optional[str] = None) -> ApprovalPolicy:
        return ApprovalPolicy.for_level(level or self._config.autonomy_level)

    @property
    def sessions(self) -> SessionManager:
        return self._session_manager

    @property
    def checkpoints(self) -> CheckpointManager:
        return self._checkpoint_manager

    @property
    def observability(self) -> RuntimeObservability:
        return self._observability

    def get_state(self) -> Any:
        return self._state_projection.compute()
