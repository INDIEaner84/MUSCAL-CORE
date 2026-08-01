from __future__ import annotations

from features.runtime.models import ApprovalPolicy


class TestApprovalPolicy:

    def test_a3_allowed_actions(self):
        policy = ApprovalPolicy.for_level("A3")
        assert policy.is_allowed("modify_files")
        assert policy.is_allowed("run_tests")
        assert policy.is_allowed("create_reports")
        assert policy.is_allowed("inspect_system")
        assert policy.is_allowed("read_only")

    def test_a3_denied_actions(self):
        policy = ApprovalPolicy.for_level("A3")
        assert not policy.is_allowed("push_remote")
        assert not policy.is_allowed("modify_authority")
        assert not policy.is_allowed("delete_history")
        assert not policy.is_allowed("change_adr")
        assert not policy.is_allowed("deploy")

    def test_a0_read_only(self):
        policy = ApprovalPolicy.for_level("A0")
        assert policy.is_allowed("read_only")
        assert policy.is_allowed("inspect_system")
        assert not policy.is_allowed("modify_files")
        assert not policy.is_allowed("run_tests")
        assert not policy.is_allowed("push_remote")

    def test_a5_all_actions(self):
        policy = ApprovalPolicy.for_level("A5")
        assert policy.is_allowed("modify_files")
        assert policy.is_allowed("push_remote")
        assert policy.is_allowed("deploy")
        assert not policy.is_allowed("nonexistent_action")

    def test_confirmation_required_a3(self):
        policy = ApprovalPolicy.for_level("A3")
        assert policy.needs_confirmation("push_remote")
        assert policy.needs_confirmation("deploy")
        assert not policy.needs_confirmation("modify_files")
        assert not policy.needs_confirmation("run_tests")

    def test_confirmation_required_a5(self):
        policy = ApprovalPolicy.for_level("A5")
        assert policy.needs_confirmation("deploy")
        assert policy.needs_confirmation("modify_authority")
        assert policy.needs_confirmation("delete_history")
        assert policy.needs_confirmation("change_adr")

    def test_custom_policy(self):
        policy = ApprovalPolicy(
            autonomy_level="CUSTOM",
            allowed_actions={"read_only", "run_tests"},
            denied_actions={"modify_files", "push_remote"},
            requires_confirmation={"deploy"},
        )
        assert policy.is_allowed("read_only")
        assert policy.is_allowed("run_tests")
        assert not policy.is_allowed("modify_files")
        assert not policy.is_allowed("push_remote")
        assert not policy.is_allowed("deploy")
        assert policy.needs_confirmation("deploy")

    def test_invalid_action_category(self):
        try:
            ApprovalPolicy(
                autonomy_level="TEST",
                allowed_actions={"invalid_action"},
            )
            assert False, "Should have raised ValueError"
        except ValueError:
            pass

    def test_conflicting_allowed_denied(self):
        try:
            ApprovalPolicy(
                autonomy_level="TEST",
                allowed_actions={"modify_files"},
                denied_actions={"modify_files"},
            )
            assert False, "Should have raised ValueError"
        except ValueError:
            pass

    def test_unknown_action_denied(self):
        policy = ApprovalPolicy.for_level("A3")
        assert not policy.is_allowed("nonexistent")

    def test_a2_requires_confirmation_for_modify(self):
        policy = ApprovalPolicy.for_level("A2")
        assert policy.needs_confirmation("modify_files")
        assert not policy.needs_confirmation("run_tests")
        assert not policy.is_allowed("push_remote")

    def test_a4_approval_policy(self):
        policy = ApprovalPolicy.for_level("A4")
        assert policy.is_allowed("modify_files")
        assert policy.is_allowed("push_remote")
        assert not policy.is_allowed("modify_authority")
        assert policy.needs_confirmation("deploy")

    def test_to_dict(self):
        policy = ApprovalPolicy.for_level("A3")
        d = policy.to_dict()
        assert d["approval_policy"]["autonomy_level"] == "A3"
        assert "modify_files" in d["approval_policy"]["allowed_actions"]
        assert "push_remote" in d["approval_policy"]["denied_actions"]
        assert "deploy" in d["approval_policy"]["requires_confirmation"]

    def test_to_dict_a0(self):
        policy = ApprovalPolicy.for_level("A0")
        d = policy.to_dict()
        assert d["approval_policy"]["autonomy_level"] == "A0"
        assert d["approval_policy"]["allowed_actions"] == ["inspect_system", "read_only"]
