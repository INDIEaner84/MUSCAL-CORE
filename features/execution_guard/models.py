from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Optional


class AutonomyLevel(Enum):
    A0_OBSERVE = "A0"
    A1_INSPECT = "A1"
    A2_PROPOSE = "A2"
    A3_MODIFY_AND_TEST = "A3"
    A4_EXECUTE_APPROVED = "A4"
    A5_AUTONOMOUS_WORKFLOW = "A5"


class GuardDecision(Enum):
    ALLOW = "ALLOW"
    ALLOW_WITH_WARNING = "ALLOW_WITH_WARNING"
    BLOCK = "BLOCK"


@dataclass
class GuardFinding:
    category: str
    message: str
    severity: str = "info"

    def to_dict(self) -> dict:
        return {
            "category": self.category,
            "message": self.message,
            "severity": self.severity,
        }


@dataclass
class GitSnapshot:
    repository_root: Path
    branch: str
    commit: str
    dirty: bool
    modified_files: list[str]
    untracked_files: list[str]
    timestamp: str

    def to_dict(self) -> dict:
        return {
            "git_snapshot": {
                "repository_root": str(self.repository_root),
                "branch": self.branch,
                "commit": self.commit,
                "dirty": self.dirty,
                "modified_files": self.modified_files,
                "untracked_files": self.untracked_files,
                "timestamp": self.timestamp,
            }
        }


@dataclass
class PreExecutionGuard:
    task_id: str
    project_id: str
    snapshot: GitSnapshot
    autonomy_level: AutonomyLevel
    approval_status: GuardDecision
    allowed: bool
    findings: list[GuardFinding] = field(default_factory=list)
    reasons: list[str] = field(default_factory=list)
    timestamp: str = ""

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now(timezone.utc).isoformat()

    def to_dict(self) -> dict:
        return {
            "pre_execution_guard": {
                "task_id": self.task_id,
                "project_id": self.project_id,
                "snapshot": self.snapshot.to_dict(),
                "autonomy_level": self.autonomy_level.value,
                "approval_status": self.approval_status.value,
                "allowed": self.allowed,
                "findings": [f.to_dict() for f in self.findings],
                "reasons": self.reasons,
                "timestamp": self.timestamp,
            }
        }


@dataclass
class PostExecutionGuard:
    pre_snapshot: GitSnapshot
    post_snapshot: GitSnapshot
    changed_files: list[str]
    commit_changed: bool
    tests_changed: bool
    rollback_available: bool
    findings: list[GuardFinding] = field(default_factory=list)
    timestamp: str = ""

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now(timezone.utc).isoformat()

    def to_dict(self) -> dict:
        return {
            "post_execution_guard": {
                "pre_snapshot": self.pre_snapshot.to_dict(),
                "post_snapshot": self.post_snapshot.to_dict(),
                "changed_files": self.changed_files,
                "commit_changed": self.commit_changed,
                "tests_changed": self.tests_changed,
                "rollback_available": self.rollback_available,
                "findings": [f.to_dict() for f in self.findings],
                "timestamp": self.timestamp,
            }
        }
