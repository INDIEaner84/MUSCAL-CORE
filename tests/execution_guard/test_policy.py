from __future__ import annotations

from features.execution_guard.policy import AutonomyPolicy, BUILTIN_AUTONOMY_LEVELS
from features.execution_guard.models import AutonomyLevel, GuardDecision


class TestAutonomyPolicy:

    def test_a3_can_modify_code(self):
        policy = AutonomyPolicy(level=AutonomyLevel.A3_MODIFY_AND_TEST)
        assert policy.can("modify_code") is True
        assert policy.check_action("modify_code") == GuardDecision.ALLOW

    def test_a3_can_run_tests(self):
        policy = AutonomyPolicy(level=AutonomyLevel.A3_MODIFY_AND_TEST)
        assert policy.can("run_tests") is True

    def test_a3_cannot_push_external(self):
        policy = AutonomyPolicy(level=AutonomyLevel.A3_MODIFY_AND_TEST)
        assert policy.can("push_external") is False

    def test_a3_cannot_change_authority(self):
        policy = AutonomyPolicy(level=AutonomyLevel.A3_MODIFY_AND_TEST)
        assert policy.can("change_authority") is False

    def test_a3_cannot_modify_adrs(self):
        policy = AutonomyPolicy(level=AutonomyLevel.A3_MODIFY_AND_TEST)
        assert policy.can("modify_adrs") is False

    def test_a3_cannot_delete_history(self):
        policy = AutonomyPolicy(level=AutonomyLevel.A3_MODIFY_AND_TEST)
        assert policy.can("delete_history") is False

    def test_a0_cannot_modify(self):
        policy = AutonomyPolicy(level=AutonomyLevel.A0_OBSERVE)
        assert policy.can("modify_code") is False

    def test_forbidden_actions_always_blocked(self):
        policy = AutonomyPolicy(level=AutonomyLevel.A5_AUTONOMOUS_WORKFLOW)
        assert policy.can("change_authority") is False
        assert policy.can("modify_adrs") is False
        assert policy.can("delete_history") is False

    def test_check_action_with_reason_returns_reason(self):
        policy = AutonomyPolicy(level=AutonomyLevel.A1_INSPECT)
        decision, reason = policy.check_action_with_reason("modify_code")
        assert decision == GuardDecision.BLOCK
        assert reason is not None
        assert "not permitted" in reason

    def test_forbidden_action_reason(self):
        policy = AutonomyPolicy(level=AutonomyLevel.A5_AUTONOMOUS_WORKFLOW)
        decision, reason = policy.check_action_with_reason("change_authority")
        assert decision == GuardDecision.BLOCK
        assert "Changing project authority" in reason

    def test_to_dict(self):
        policy = AutonomyPolicy(level=AutonomyLevel.A3_MODIFY_AND_TEST)
        d = policy.to_dict()
        assert d["autonomy_level"] == "A3"
        assert "modify_code" in d["permissions"]
        assert "forbidden_actions" in d

    def test_builtin_levels_have_expected_keys(self):
        for level, perms in BUILTIN_AUTONOMY_LEVELS.items():
            assert "modify_code" in perms
            assert "run_tests" in perms
            assert "push_external" in perms
            assert "change_authority" in perms
            assert "modify_adrs" in perms
            assert "delete_history" in perms
