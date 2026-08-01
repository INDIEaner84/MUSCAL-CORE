from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class TaskContract:
    id: str
    project: str
    objective: str
    constraints: list[str] = field(default_factory=list)
    expected_output: Optional[str] = None
    verification_required: bool = True

    def validate(self) -> list[str]:
        errors: list[str] = []
        if not self.id:
            errors.append("task.id is required")
        if not self.project:
            errors.append("task.project is required")
        if not self.objective:
            errors.append("task.objective is required")
        return errors

    def to_dict(self) -> dict:
        return {
            "task": {
                "id": self.id,
                "project": self.project,
                "objective": self.objective,
                "constraints": self.constraints,
                "expected_output": self.expected_output,
                "verification_required": self.verification_required,
            }
        }

    @classmethod
    def from_dict(cls, data: dict) -> TaskContract:
        t = data.get("task", data)
        return cls(
            id=t.get("id", ""),
            project=t.get("project", ""),
            objective=t.get("objective", ""),
            constraints=t.get("constraints", []),
            expected_output=t.get("expected_output"),
            verification_required=t.get("verification_required", True),
        )
