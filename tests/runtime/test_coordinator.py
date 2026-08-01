from __future__ import annotations

from pathlib import Path

from features.runtime.coordinator import RuntimeCoordinator, RuntimeOutput
from features.runtime.models import RuntimeConfig
from features.bridge.task_contract import TaskContract


class TestRuntimeCoordinator:

    def test_coordinator_execute_help(self):
        coord = RuntimeCoordinator()
        output = coord.execute("--help")
        assert output.session_id is not None
        assert output.checkpoint_id is not None
        assert output.status in ("completed", "failed")

    def test_coordinator_creates_session(self):
        coord = RuntimeCoordinator()
        output = coord.execute("--help")
        session = coord.sessions.get_session(output.session_id)
        assert session is not None
        assert session.status in ("COMPLETED", "FAILED")

    def test_coordinator_creates_checkpoint(self):
        coord = RuntimeCoordinator()
        output = coord.execute("--help")
        assert output.checkpoint_id is not None
        cp = coord.checkpoints.get_checkpoint(output.checkpoint_id)
        assert cp is not None

    def test_coordinator_with_task_contract(self):
        coord = RuntimeCoordinator()
        task = TaskContract(id="coord-test-001", project="muscal-core", objective="test")
        output = coord.execute("--help", task=task)
        assert output.status in ("completed", "failed")

    def test_coordinator_get_state(self):
        coord = RuntimeCoordinator()
        coord.execute("--help")
        state = coord.get_state()
        assert state.health in ("healthy", "unknown")

    def test_coordinator_properties(self):
        coord = RuntimeCoordinator()
        assert coord.sessions is not None
        assert coord.checkpoints is not None
        assert coord.observability is not None

    def test_coordinator_to_dict(self):
        output = RuntimeOutput(
            session_id="s1",
            checkpoint_id="c1",
            bridge_output=None,
            status="completed",
        )
        d = output.to_dict()
        assert d["runtime_output"]["session_id"] == "s1"
        assert d["runtime_output"]["status"] == "completed"

    def test_coordinator_with_workdir(self):
        coord = RuntimeCoordinator()
        output = coord.execute("--help", workdir=Path.cwd())
        assert output.session_id is not None

    def test_coordinator_two_executions(self):
        coord = RuntimeCoordinator()
        o1 = coord.execute("--help")
        o2 = coord.execute("--help")
        assert o1.session_id != o2.session_id
        assert len(coord.sessions.all_sessions()) == 2

    def test_execution_tracking(self):
        coord = RuntimeCoordinator()
        coord.execute("--help")
        sessions = coord.sessions.all_sessions()
        assert len(sessions) >= 1
        for s in sessions:
            assert s.execution_id is not None

    def test_coordinator_errors_empty_on_success(self):
        coord = RuntimeCoordinator()
        output = coord.execute("--help")
        if output.status == "completed":
            assert len(output.errors) == 0

    def test_coordinator_recover_runtime(self):
        coord = RuntimeCoordinator()
        result = coord.recover_runtime()
        assert result.sessions_recovered >= 0
        assert result.status == "completed"

    def test_recovery_result_to_dict(self):
        from features.runtime.coordinator import RecoveryResult
        rr = RecoveryResult(sessions_recovered=5, checkpoints_recovered=3, interrupted_sessions=1, status="completed")
        d = rr.to_dict()
        assert d["recovery_result"]["sessions_recovered"] == 5
        assert d["recovery_result"]["checkpoints_recovered"] == 3
        assert d["recovery_result"]["status"] == "completed"

    def test_coordinator_get_approval_policy(self):
        coord = RuntimeCoordinator()
        policy = coord.get_approval_policy("A3")
        assert policy.is_allowed("modify_files")
        assert not policy.is_allowed("push_remote")
        assert policy.autonomy_level == "A3"
