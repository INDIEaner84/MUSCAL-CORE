from __future__ import annotations

from pathlib import Path

import pytest

from features.execution_guard.guard import ExecutionGuard, GuardResult
from features.execution_guard.models import AutonomyLevel, GuardDecision


class TestExecutionGuard:

    def test_pre_check_allows_clean_repo(self):
        guard = ExecutionGuard()
        pre = guard.pre_check(task_id="t1", project_id="p1", path=Path("."))
        assert pre.allowed is True
        assert pre.approval_status in (GuardDecision.ALLOW, GuardDecision.ALLOW_WITH_WARNING)

    def test_pre_check_reports_repo_state(self):
        guard = ExecutionGuard()
        pre = guard.pre_check(task_id="t2", project_id="p2", path=Path("."))
        assert pre.snapshot is not None
        assert pre.snapshot.branch is not None
        assert len(pre.snapshot.commit) >= 7

    def test_pre_check_blocks_readonly_level(self):
        guard = ExecutionGuard(autonomy_level=AutonomyLevel.A0_OBSERVE)
        pre = guard.pre_check(task_id="t3", project_id="p3", path=Path("."))
        assert pre.allowed is False
        assert pre.approval_status == GuardDecision.BLOCK

    def test_pre_check_blocks_a1(self):
        guard = ExecutionGuard(autonomy_level=AutonomyLevel.A1_INSPECT)
        pre = guard.pre_check(task_id="t4", project_id="p4", path=Path("."))
        assert pre.allowed is False

    def test_pre_check_blocks_a2(self):
        guard = ExecutionGuard(autonomy_level=AutonomyLevel.A2_PROPOSE)
        pre = guard.pre_check(task_id="t5", project_id="p5", path=Path("."))
        assert pre.allowed is False

    def test_post_check_detects_changes(self):
        guard = ExecutionGuard()
        pre = guard.pre_check(task_id="t6", project_id="p6", path=Path("."))
        post = guard.post_check(pre, path=Path("."))
        assert post.pre_snapshot.commit == post.post_snapshot.commit
        assert isinstance(post.changed_files, list)

    def test_post_check_rollback_available(self):
        guard = ExecutionGuard()
        pre = guard.pre_check(task_id="t7", project_id="p7", path=Path("."))
        post = guard.post_check(pre, path=Path("."))
        rb = guard.get_current_rollback()
        assert rb is not None
        assert rb.available is True

    def test_guard_result_dataclass(self):
        guard = ExecutionGuard()
        pre = guard.pre_check(task_id="t8", project_id="p8", path=Path("."))
        post = guard.post_check(pre, path=Path("."))
        rb = guard.get_current_rollback()
        result = GuardResult(pre=pre, post=post, rollback=rb)
        assert result.pre.task_id == "t8"
        assert result.post is not None
        assert result.rollback is not None

    def test_pre_execution_guard_to_dict(self):
        guard = ExecutionGuard()
        pre = guard.pre_check(task_id="t9", project_id="p9", path=Path("."))
        d = pre.to_dict()
        assert d["pre_execution_guard"]["task_id"] == "t9"
        assert d["pre_execution_guard"]["project_id"] == "p9"
        assert "autonomy_level" in d["pre_execution_guard"]
        assert "approval_status" in d["pre_execution_guard"]
