from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional


SESSION_STATES = frozenset({
    "CREATED", "RUNNING", "PAUSED", "RECOVERING", "COMPLETED", "FAILED", "INTERRUPTED",
})

CHECKPOINT_STATUS = frozenset({
    "available", "unavailable", "unknown",
})

CHECKPOINT_EVENTS = frozenset({
    "runtime.checkpoint.created",
    "runtime.checkpoint.restored",
})

RUNTIME_EVENTS = frozenset({
    "runtime.started",
    "runtime.session.created",
    "runtime.session.updated",
    "runtime.session.restored",
    "runtime.checkpoint.created",
    "runtime.checkpoint.restored",
    "runtime.execution.started",
    "runtime.execution.completed",
    "runtime.execution.failed",
    "runtime.execution.interrupted",
    "runtime.recovery.started",
    "runtime.recovery.completed",
    "runtime.health.changed",
})

KNOWLEDGE_EVENTS = frozenset({
    "knowledge.candidate.created",
    "knowledge.candidate.validated",
    "knowledge.candidate.rejected",
    "knowledge.entry.updated",
    "knowledge.retrieval.requested",
})

OPTIMIZATION_EVENTS = frozenset({
    "optimization.execution.evaluated",
    "optimization.agent.profile.updated",
    "optimization.selection.recommended",
    "optimization.workflow.improved",
})

TOOL_EVENTS = frozenset({
    "tool.requested",
    "tool.approved",
    "tool.denied",
    "tool.executed",
    "tool.failed",
})

KERNEL_EVENTS = frozenset({
    "kernel.intent.created",
    "kernel.goal.created",
    "kernel.context.built",
    "kernel.strategy.selected",
    "kernel.pipeline.completed",
})

MEMORY_EVENTS = frozenset({
    "memory.created",
    "memory.classified",
    "memory.retrieved",
    "memory.consolidated",
    "memory.promoted",
    "memory.persisted",
    "memory.validation.started",
    "memory.validation.completed",
    "memory.lifecycle.changed",
    "memory.consolidation.completed",
})

INTERFACE_EVENTS = frozenset({
    "interface.requested",
    "interface.approved",
    "interface.executed",
    "interface.failed",
    "interface.verified",
})

ALL_RUNTIME_EVENTS = RUNTIME_EVENTS | KNOWLEDGE_EVENTS | OPTIMIZATION_EVENTS | TOOL_EVENTS | KERNEL_EVENTS | MEMORY_EVENTS | INTERFACE_EVENTS

APPROVAL_ACTION_CATEGORIES = frozenset({
    "modify_files",
    "run_tests",
    "create_reports",
    "push_remote",
    "modify_authority",
    "delete_history",
    "change_adr",
    "deploy",
    "inspect_system",
    "read_only",
})


@dataclass
class Session:
    session_id: str
    execution_id: str
    task_id: str
    project_id: str
    opencode_session_id: Optional[str]
    status: str
    created_at: str
    updated_at: str
    last_checkpoint: Optional[str] = None

    def __post_init__(self):
        if self.status not in SESSION_STATES:
            raise ValueError(f"Invalid session state '{self.status}'. Must be one of: {sorted(SESSION_STATES)}")

    def to_dict(self) -> dict:
        return {
            "session": {
                "id": self.session_id,
                "execution_id": self.execution_id,
                "task_id": self.task_id,
                "project_id": self.project_id,
                "opencode_session_id": self.opencode_session_id,
                "status": self.status,
                "created_at": self.created_at,
                "updated_at": self.updated_at,
                "last_checkpoint": self.last_checkpoint,
            }
        }


@dataclass
class Checkpoint:
    checkpoint_id: str
    execution_id: str
    task_id: str
    project: str
    git_commit: str
    session_id: str
    timestamp: str
    state_reference: Optional[str] = None
    status: str = "available"

    def __post_init__(self):
        if self.status not in CHECKPOINT_STATUS:
            raise ValueError(f"Invalid checkpoint status '{self.status}'. Must be one of: {sorted(CHECKPOINT_STATUS)}")

    def to_dict(self) -> dict:
        return {
            "checkpoint": {
                "id": self.checkpoint_id,
                "execution_id": self.execution_id,
                "task_id": self.task_id,
                "project": self.project,
                "git_commit": self.git_commit,
                "session_id": self.session_id,
                "timestamp": self.timestamp,
                "state_reference": self.state_reference,
                "status": self.status,
            }
        }


@dataclass
class RuntimeState:
    active_sessions: list[dict] = field(default_factory=list)
    queued_tasks: list[str] = field(default_factory=list)
    running_executions: list[str] = field(default_factory=list)
    failed_executions: int = 0
    interrupted_sessions: int = 0
    last_event: Optional[dict] = None
    event_lag: float = 0.0
    recovery_status: str = "none"
    health: str = "unknown"

    def to_dict(self) -> dict:
        return {
            "runtime": {
                "active_sessions": self.active_sessions,
                "queued_tasks": self.queued_tasks,
                "running_executions": self.running_executions,
                "failed_executions": self.failed_executions,
                "interrupted_sessions": self.interrupted_sessions,
                "last_event": self.last_event,
                "event_lag": self.event_lag,
                "recovery_status": self.recovery_status,
                "health": self.health,
            }
        }


@dataclass
class RuntimeConfig:
    event_store_path: Optional[str] = None
    opencode_path: str = "opencode"
    autonomy_level: str = "A3"
    max_retries: int = 3
    verification_required: bool = True


@dataclass
class ApprovalPolicy:
    autonomy_level: str
    allowed_actions: set[str] = field(default_factory=set)
    denied_actions: set[str] = field(default_factory=set)
    requires_confirmation: set[str] = field(default_factory=set)

    def __post_init__(self):
        invalid = (self.allowed_actions | self.denied_actions | self.requires_confirmation) - APPROVAL_ACTION_CATEGORIES
        if invalid:
            raise ValueError(f"Invalid action categories: {invalid}. Must be subset of: {sorted(APPROVAL_ACTION_CATEGORIES)}")
        overlap = self.allowed_actions & self.denied_actions
        if overlap:
            raise ValueError(f"Actions cannot be both allowed and denied: {overlap}")

    def is_allowed(self, action: str) -> bool:
        if action not in APPROVAL_ACTION_CATEGORIES:
            return False
        if action in self.denied_actions:
            return False
        if self.allowed_actions and action not in self.allowed_actions:
            return False
        return True

    def needs_confirmation(self, action: str) -> bool:
        return action in self.requires_confirmation

    def to_dict(self) -> dict:
        return {
            "approval_policy": {
                "autonomy_level": self.autonomy_level,
                "allowed_actions": sorted(self.allowed_actions),
                "denied_actions": sorted(self.denied_actions),
                "requires_confirmation": sorted(self.requires_confirmation),
            }
        }

    @classmethod
    def for_level(cls, level: str) -> ApprovalPolicy:
        if not hasattr(cls, '_level_cache') or not cls._level_cache:
            cls._level_cache = {
                "A0": cls(
                    autonomy_level="A0",
                    allowed_actions={"read_only", "inspect_system"},
                    denied_actions=set(APPROVAL_ACTION_CATEGORIES - {"read_only", "inspect_system"}),
                    requires_confirmation=set(),
                ),
                "A1": cls(
                    autonomy_level="A1",
                    allowed_actions={"inspect_system", "read_only", "create_reports"},
                    denied_actions=set(APPROVAL_ACTION_CATEGORIES - {"inspect_system", "read_only", "create_reports"}),
                    requires_confirmation=set(),
                ),
                "A2": cls(
                    autonomy_level="A2",
                    allowed_actions={"inspect_system", "read_only", "create_reports", "run_tests"},
                    denied_actions={"push_remote", "modify_authority", "delete_history", "change_adr", "deploy"},
                    requires_confirmation={"modify_files"},
                ),
                "A3": cls(
                    autonomy_level="A3",
                    allowed_actions={"modify_files", "run_tests", "create_reports", "inspect_system", "read_only"},
                    denied_actions={"push_remote", "modify_authority", "delete_history", "change_adr", "deploy"},
                    requires_confirmation={"push_remote", "deploy"},
                ),
                "A4": cls(
                    autonomy_level="A4",
                    allowed_actions={"modify_files", "run_tests", "create_reports", "inspect_system", "read_only", "push_remote"},
                    denied_actions={"modify_authority", "delete_history", "change_adr"},
                    requires_confirmation={"deploy", "modify_authority"},
                ),
                "A5": cls(
                    autonomy_level="A5",
                    allowed_actions=set(APPROVAL_ACTION_CATEGORIES),
                    denied_actions=set(),
                    requires_confirmation={"deploy", "modify_authority", "delete_history", "change_adr"},
                ),
            }
        if level in cls._level_cache:
            return cls._level_cache[level]
        return cls._level_cache["A0"]
