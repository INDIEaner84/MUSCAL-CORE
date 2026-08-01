from __future__ import annotations

from features.orchestration.policy import OrchestrationPolicy
from features.runtime.models import ApprovalPolicy


class TestOrchestrationPolicy:

    def test_can_execute_plan_a3(self):
        policy = OrchestrationPolicy()
        assert policy.can_execute_plan("A3") is True

    def test_cannot_execute_plan_a2(self):
        policy = OrchestrationPolicy()
        assert policy.can_execute_plan("A2") is False

    def test_requires_approval_modify_a2(self):
        policy = OrchestrationPolicy()
        assert policy.requires_approval("modify_files", "A2") is True

    def test_no_approval_needed_modify_a3(self):
        policy = OrchestrationPolicy()
        assert policy.requires_approval("modify_files", "A3") is False

    def test_requires_approval_push_a3(self):
        policy = OrchestrationPolicy()
        assert policy.requires_approval("push_remote", "A3") is True

    def test_denied_actions_for_a0(self):
        policy = OrchestrationPolicy()
        denied = policy.denied_actions_for_level("A0")
        assert len(denied) > 0

    def test_allowed_actions_for_a3(self):
        policy = OrchestrationPolicy()
        allowed = policy.allowed_actions_for_level("A3")
        assert "modify_files" in allowed

    def test_validate_plan_actions_ok(self):
        policy = OrchestrationPolicy()
        violations = policy.validate_plan_actions(["modify_files", "run_tests"], "A3")
        assert len(violations) == 0

    def test_validate_plan_actions_violation(self):
        policy = OrchestrationPolicy()
        violations = policy.validate_plan_actions(["push_remote", "deploy"], "A3")
        assert len(violations) > 0

    def test_policy_with_custom_approval(self):
        policy = OrchestrationPolicy()
        assert policy.requires_approval("modify_files", "A2") is True
        assert policy.requires_approval("run_tests", "A2") is False
