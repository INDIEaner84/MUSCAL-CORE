from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory

from runtime.event_store import EventStore

from features.runtime.observability import RuntimeObservability
from features.runtime.models import Session, Checkpoint, RUNTIME_EVENTS


class TestRuntimeObservability:

    def _make_store(self) -> EventStore:
        return EventStore(Path(self._tmpdir.name) / "test_obs.db")

    def setup_method(self):
        self._tmpdir = TemporaryDirectory()
        self._store = self._make_store()

    def teardown_method(self):
        self._store.close()
        self._tmpdir.cleanup()

    def test_emit_event(self):
        obs = RuntimeObservability(self._store)
        seq = obs.emit(
            "runtime.started",
            {"message": "test"},
            execution_id="exec-001",
            correlation_id="corr-001",
        )
        assert seq is not None
        assert seq > 0

    def test_emit_invalid_topic_raises(self):
        obs = RuntimeObservability(self._store)
        try:
            obs.emit("invalid.topic", {}, execution_id="exec-001")
            assert False, "Should have raised ValueError"
        except ValueError:
            pass

    def test_emit_started(self):
        obs = RuntimeObservability(self._store)
        seq = obs.emit_started(correlation_id="corr-001")
        assert seq is not None

    def test_emit_session_created(self):
        obs = RuntimeObservability(self._store)
        session = Session(
            session_id="s1", execution_id="e1", task_id="t1",
            project_id="p1", opencode_session_id=None,
            status="CREATED", created_at="now", updated_at="now",
        )
        seq = obs.emit_session_created(session)
        assert seq is not None

    def test_emit_session_updated(self):
        obs = RuntimeObservability(self._store)
        session = Session(
            session_id="s1", execution_id="e1", task_id="t1",
            project_id="p1", opencode_session_id=None,
            status="RUNNING", created_at="now", updated_at="now",
        )
        seq = obs.emit_session_updated(session)
        assert seq is not None

    def test_emit_checkpoint_created(self):
        obs = RuntimeObservability(self._store)
        cp = Checkpoint(
            checkpoint_id="c1", execution_id="e1", task_id="t1",
            project="p1", git_commit="abc", session_id="s1",
            timestamp="now",
        )
        seq = obs.emit_checkpoint_created(cp)
        assert seq is not None

    def test_emit_execution_started(self):
        obs = RuntimeObservability(self._store)
        seq = obs.emit_execution_started("exec-001", task_id="t1", session_id="s1")
        assert seq is not None

    def test_emit_execution_completed(self):
        obs = RuntimeObservability(self._store)
        seq = obs.emit_execution_completed("exec-001", task_id="t1", session_id="s1")
        assert seq is not None

    def test_emit_execution_failed(self):
        obs = RuntimeObservability(self._store)
        seq = obs.emit_execution_failed("exec-001", task_id="t1", session_id="s1", error="oops")
        assert seq is not None

    def test_emit_recovery_started(self):
        obs = RuntimeObservability(self._store)
        seq = obs.emit_recovery_started("exec-001", task_id="t1", session_id="s1", strategy="retry")
        assert seq is not None

    def test_event_replayable(self):
        obs = RuntimeObservability(self._store)
        obs.emit_started(correlation_id="corr-test")
        events = self._store.replay(topic="runtime.started")
        assert len(events) == 1
        assert events[0]["payload"]["message"] == "Runtime initialized"

    def test_no_store_returns_none(self):
        obs = RuntimeObservability(event_store=None)
        seq = obs.emit_started()
        assert seq is None

    def test_emit_session_restored(self):
        obs = RuntimeObservability(self._store)
        session = Session(
            session_id="s1", execution_id="e1", task_id="t1",
            project_id="p1", opencode_session_id=None,
            status="INTERRUPTED", created_at="now", updated_at="now",
        )
        seq = obs.emit_session_restored(session)
        assert seq is not None

    def test_emit_execution_interrupted(self):
        obs = RuntimeObservability(self._store)
        seq = obs.emit_execution_interrupted("exec-001", task_id="t1", session_id="s1", reason="crash")
        assert seq is not None

    def test_emit_recovery_completed(self):
        obs = RuntimeObservability(self._store)
        seq = obs.emit_recovery_completed("exec-001", task_id="t1", session_id="s1", result="ok")
        assert seq is not None

    def test_all_runtime_events_known(self):
        expected = {
            "runtime.started",
            "runtime.session.created",
            "runtime.session.updated",
            "runtime.session.restored",
            "runtime.checkpoint.created",
            "runtime.checkpoint.restored",
            "runtime.execution.started",
            "runtime.execution.completed",
            "runtime.execution.failed",
            "runtime.execution.interrupted",
            "runtime.recovery.started",
            "runtime.recovery.completed",
            "runtime.health.changed",
        }
        assert RUNTIME_EVENTS == expected
