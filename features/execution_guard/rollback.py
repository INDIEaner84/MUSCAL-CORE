from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional


ROLLBACK_METHODS = frozenset({
    "git_commit_reference",
    "git_diff_patch",
    "checkpoint_reference",
})


@dataclass
class RollbackInfo:
    available: bool
    method: Optional[str]
    reference: Optional[str]
    created_at: str

    def __post_init__(self):
        if self.method and self.method not in ROLLBACK_METHODS:
            allowed = sorted(ROLLBACK_METHODS)
            raise ValueError(f"Invalid rollback method '{self.method}'. Must be one of: {allowed}")

    def to_dict(self) -> dict:
        return {
            "rollback": {
                "available": self.available,
                "method": self.method,
                "reference": self.reference,
                "created_at": self.created_at,
            }
        }

    @classmethod
    def not_available(cls) -> RollbackInfo:
        return cls(
            available=False,
            method=None,
            reference=None,
            created_at=datetime.now(timezone.utc).isoformat(),
        )

    @classmethod
    def from_commit(cls, commit: str) -> RollbackInfo:
        return cls(
            available=True,
            method="git_commit_reference",
            reference=commit,
            created_at=datetime.now(timezone.utc).isoformat(),
        )

    @classmethod
    def from_diff(cls, diff_reference: str) -> RollbackInfo:
        return cls(
            available=True,
            method="git_diff_patch",
            reference=diff_reference,
            created_at=datetime.now(timezone.utc).isoformat(),
        )

    @classmethod
    def from_checkpoint(cls, checkpoint: str) -> RollbackInfo:
        return cls(
            available=True,
            method="checkpoint_reference",
            reference=checkpoint,
            created_at=datetime.now(timezone.utc).isoformat(),
        )
