from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from .models import AutonomyLevel, GuardDecision, GuardFinding


BUILTIN_AUTONOMY_LEVELS = {
    AutonomyLevel.A0_OBSERVE: {
        "modify_code": False,
        "run_tests": False,
        "push_external": False,
        "change_authority": False,
        "modify_adrs": False,
        "delete_history": False,
    },
    AutonomyLevel.A1_INSPECT: {
        "modify_code": False,
        "run_tests": False,
        "push_external": False,
        "change_authority": False,
        "modify_adrs": False,
        "delete_history": False,
    },
    AutonomyLevel.A2_PROPOSE: {
        "modify_code": False,
        "run_tests": False,
        "push_external": False,
        "change_authority": False,
        "modify_adrs": False,
        "delete_history": False,
    },
    AutonomyLevel.A3_MODIFY_AND_TEST: {
        "modify_code": True,
        "run_tests": True,
        "push_external": False,
        "change_authority": False,
        "modify_adrs": False,
        "delete_history": False,
    },
    AutonomyLevel.A4_EXECUTE_APPROVED: {
        "modify_code": True,
        "run_tests": True,
        "push_external": False,
        "change_authority": False,
        "modify_adrs": False,
        "delete_history": False,
    },
    AutonomyLevel.A5_AUTONOMOUS_WORKFLOW: {
        "modify_code": True,
        "run_tests": True,
        "push_external": True,
        "change_authority": False,
        "modify_adrs": False,
        "delete_history": False,
    },
}


FORBIDDEN_ACTIONS = {
    "change_authority": "Changing project authority is not permitted at any autonomy level",
    "modify_adrs": "Modifying ADRs is not permitted at any autonomy level",
    "delete_history": "Deleting history is not permitted at any autonomy level",
}


@dataclass
class AutonomyPolicy:
    level: AutonomyLevel = AutonomyLevel.A3_MODIFY_AND_TEST
    permissions: dict = field(default_factory=dict)

    def __post_init__(self):
        if not self.permissions:
            self.permissions = dict(BUILTIN_AUTONOMY_LEVELS.get(self.level, {}))

    def check_action(self, action: str) -> GuardDecision:
        if action in FORBIDDEN_ACTIONS:
            return GuardDecision.BLOCK
        allowed = self.permissions.get(action, False)
        return GuardDecision.ALLOW if allowed else GuardDecision.BLOCK

    def can(self, action: str) -> bool:
        return self.check_action(action) == GuardDecision.ALLOW

    def check_action_with_reason(self, action: str) -> tuple[GuardDecision, Optional[str]]:
        if action in FORBIDDEN_ACTIONS:
            return GuardDecision.BLOCK, FORBIDDEN_ACTIONS[action]
        allowed = self.permissions.get(action, False)
        if allowed:
            return GuardDecision.ALLOW, None
        return GuardDecision.BLOCK, f"Action '{action}' not permitted at autonomy level {self.level.value}"

    def to_dict(self) -> dict:
        return {
            "autonomy_level": self.level.value,
            "permissions": dict(self.permissions),
            "forbidden_actions": dict(FORBIDDEN_ACTIONS),
        }
