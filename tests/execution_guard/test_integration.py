from __future__ import annotations

from pathlib import Path

from features.execution_guard.guard import ExecutionGuard
from features.execution_guard.models import AutonomyLevel, GuardDecision
from features.execution_guard.policy import AutonomyPolicy
from features.execution_guard.rollback import RollbackInfo


class TestIntegration:

    def test_full_guard_flow_clean(self):
        guard = ExecutionGuard(autonomy_level=AutonomyLevel.A3_MODIFY_AND_TEST)

        pre = guard.pre_check(task_id="int-1", project_id="int-project", path=Path("."))
        assert pre.allowed is True

        post = guard.post_check(pre, path=Path("."))
        assert post.pre_snapshot.commit == post.post_snapshot.commit

        rb = guard.get_current_rollback()
        assert rb is not None
        assert rb.available is True

    def test_policy_guard_interaction(self):
        policy = AutonomyPolicy(level=AutonomyLevel.A3_MODIFY_AND_TEST)
        guard = ExecutionGuard(policy=policy)

        pre = guard.pre_check(task_id="int-2", project_id="int-project", path=Path("."))
        assert pre.allowed is True

        assert guard._policy.can("modify_code") is True
        assert guard._policy.can("push_external") is False

    def test_rollback_from_guard(self):
        guard = ExecutionGuard()
        pre = guard.pre_check(task_id="int-3", project_id="int-project", path=Path("."))
        guard.post_check(pre, path=Path("."))

        rb = guard.get_current_rollback()
        assert rb is not None
        assert rb.available is True
        assert rb.method == "git_commit_reference"

    def test_rollback_not_available_factory(self):
        rb = RollbackInfo.not_available()
        assert rb.available is False
        d = rb.to_dict()
        assert d["rollback"]["available"] is False

    def test_a0_guard_blocks_execution(self):
        guard = ExecutionGuard(autonomy_level=AutonomyLevel.A0_OBSERVE)
        pre = guard.pre_check(task_id="int-4", project_id="int-project", path=Path("."))
        assert pre.allowed is False
        assert pre.approval_status == GuardDecision.BLOCK

    def test_a3_guard_allows_with_warning_on_dirty(
        self, tmp_path: Path
    ):
        import subprocess
        repo = tmp_path / "dirty_guard"
        repo.mkdir()
        subprocess.run(["git", "init"], cwd=repo, capture_output=True)
        subprocess.run(["git", "config", "user.email", "t@t"], cwd=repo, capture_output=True)
        subprocess.run(["git", "config", "user.name", "t"], cwd=repo, capture_output=True)
        (repo / "f.txt").write_text("hello")
        subprocess.run(["git", "add", "."], cwd=repo, capture_output=True)
        subprocess.run(["git", "commit", "-m", "init"], cwd=repo, capture_output=True)
        (repo / "f.txt").write_text("changed")

        guard = ExecutionGuard(autonomy_level=AutonomyLevel.A3_MODIFY_AND_TEST)
        pre = guard.pre_check(task_id="int-5", project_id="int-project", path=repo)
        assert pre.allowed is True
        assert pre.approval_status == GuardDecision.ALLOW_WITH_WARNING
