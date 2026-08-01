from __future__ import annotations

from features.runtime.checkpoint_manager import CheckpointManager


class TestCheckpointManager:

    def test_create_checkpoint(self):
        mgr = CheckpointManager()
        cp = mgr.create_checkpoint(
            execution_id="exec-001",
            task_id="task-001",
            project="muscal-core",
            git_commit="abc1234",
            session_id="session-001",
        )
        assert cp.checkpoint_id is not None
        assert cp.execution_id == "exec-001"
        assert cp.task_id == "task-001"
        assert cp.git_commit == "abc1234"
        assert cp.session_id == "session-001"

    def test_create_checkpoint_with_state_reference(self):
        mgr = CheckpointManager()
        cp = mgr.create_checkpoint(
            execution_id="exec-001",
            task_id="task-001",
            project="muscal-core",
            git_commit="abc1234",
            session_id="session-001",
            state_reference="pre:abc1234",
        )
        assert cp.state_reference == "pre:abc1234"

    def test_get_checkpoint(self):
        mgr = CheckpointManager()
        created = mgr.create_checkpoint(
            execution_id="exec-001", task_id="task-001",
            project="muscal-core", git_commit="abc1234",
            session_id="session-001",
        )
        fetched = mgr.get_checkpoint(created.checkpoint_id)
        assert fetched is not None
        assert fetched.checkpoint_id == created.checkpoint_id

    def test_get_checkpoint_not_found(self):
        mgr = CheckpointManager()
        assert mgr.get_checkpoint("nonexistent") is None

    def test_list_checkpoints(self):
        mgr = CheckpointManager()
        mgr.create_checkpoint(
            execution_id="exec-001", task_id="task-001",
            project="muscal-core", git_commit="abc",
            session_id="session-001",
        )
        mgr.create_checkpoint(
            execution_id="exec-001", task_id="task-001",
            project="muscal-core", git_commit="def",
            session_id="session-001",
        )
        all_cps = mgr.list_checkpoints()
        assert len(all_cps) == 2

    def test_list_checkpoints_filtered(self):
        mgr = CheckpointManager()
        mgr.create_checkpoint(
            execution_id="exec-001", task_id="task-001",
            project="muscal-core", git_commit="abc",
            session_id="session-001",
        )
        mgr.create_checkpoint(
            execution_id="exec-002", task_id="task-002",
            project="muscal-core", git_commit="def",
            session_id="session-002",
        )
        filtered = mgr.list_checkpoints(execution_id="exec-001")
        assert len(filtered) == 1
        assert filtered[0].execution_id == "exec-001"

    def test_latest_checkpoint(self):
        mgr = CheckpointManager()
        mgr.create_checkpoint(
            execution_id="exec-001", task_id="task-001",
            project="muscal-core", git_commit="abc",
            session_id="session-001",
        )
        cp2 = mgr.create_checkpoint(
            execution_id="exec-001", task_id="task-001",
            project="muscal-core", git_commit="def",
            session_id="session-001",
        )
        latest = mgr.latest_checkpoint("exec-001")
        assert latest is not None
        assert latest.checkpoint_id == cp2.checkpoint_id

    def test_latest_checkpoint_no_match(self):
        mgr = CheckpointManager()
        latest = mgr.latest_checkpoint("nonexistent")
        assert latest is None

    def test_clear(self):
        mgr = CheckpointManager()
        mgr.create_checkpoint(
            execution_id="exec-001", task_id="task-001",
            project="muscal-core", git_commit="abc",
            session_id="session-001",
        )
        assert len(mgr.list_checkpoints()) == 1
        mgr.clear()
        assert len(mgr.list_checkpoints()) == 0

    def test_checkpoint_to_dict(self):
        mgr = CheckpointManager()
        cp = mgr.create_checkpoint(
            execution_id="exec-001", task_id="task-001",
            project="muscal-core", git_commit="abc1234",
            session_id="session-001",
            state_reference="pre:abc1234",
        )
        d = cp.to_dict()
        assert d["checkpoint"]["git_commit"] == "abc1234"
        assert d["checkpoint"]["state_reference"] == "pre:abc1234"
        assert d["checkpoint"]["execution_id"] == "exec-001"

    def test_mark_checkpoint_unavailable(self):
        mgr = CheckpointManager()
        cp = mgr.create_checkpoint(
            execution_id="exec-001", task_id="task-001",
            project="muscal-core", git_commit="abc",
            session_id="session-001",
        )
        updated = mgr.mark_checkpoint_unavailable(cp.checkpoint_id)
        assert updated is not None
        assert updated.status == "unavailable"

    def test_mark_checkpoint_unavailable_not_found(self):
        mgr = CheckpointManager()
        result = mgr.mark_checkpoint_unavailable("nonexistent")
        assert result is None

    def test_recover_checkpoints_no_store(self):
        mgr = CheckpointManager()
        count = mgr.recover_checkpoints()
        assert count == 0

    def test_checkpoint_invalid_status_raises(self):
        from features.runtime.models import Checkpoint
        try:
            Checkpoint(
                checkpoint_id="c1", execution_id="e1", task_id="t1",
                project="p1", git_commit="abc", session_id="s1",
                timestamp="now", status="INVALID",
            )
            assert False, "Should have raised ValueError"
        except ValueError:
            pass
