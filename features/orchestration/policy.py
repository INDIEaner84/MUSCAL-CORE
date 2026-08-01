from __future__ import annotations

from typing import Optional

from ..execution_guard.models import AutonomyLevel
from ..runtime.models import ApprovalPolicy


class OrchestrationPolicy:

    def __init__(self, approval_policy=ApprovalPolicy):
        self._approval_cls = approval_policy

    def can_execute_plan(self, autonomy_level: str) -> bool:
        level_num = int(autonomy_level[1]) if autonomy_level.startswith("A") and len(autonomy_level) == 2 else 0
        return level_num >= 3

    def requires_approval(self, action: str, autonomy_level: str) -> bool:
        level = self._approval_cls.for_level(autonomy_level)
        return level.needs_confirmation(action)

    def allowed_actions_for_level(self, autonomy_level: str) -> set[str]:
        level = self._approval_cls.for_level(autonomy_level)
        return level.allowed_actions

    def denied_actions_for_level(self, autonomy_level: str) -> set[str]:
        level = self._approval_cls.for_level(autonomy_level)
        return level.denied_actions

    def validate_plan_actions(self, actions: list[str], autonomy_level: str) -> list[str]:
        violations: list[str] = []
        for action in actions:
            if self.requires_approval(action, autonomy_level):
                violations.append(f"Action '{action}' requires approval at level {autonomy_level}")
        return violations
