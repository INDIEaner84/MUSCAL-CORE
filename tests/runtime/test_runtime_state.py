from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory

from runtime.event_store import EventStore

from features.runtime.runtime_state import RuntimeStateProjection
from features.runtime.observability import RuntimeObservability
from features.runtime.models import Session, Checkpoint


class TestRuntimeStateProjection:

    def _make_store(self) -> EventStore:
        return EventStore(Path(self._tmpdir.name) / "test_state.db")

    def setup_method(self):
        self._tmpdir = TemporaryDirectory()
        self._store = self._make_store()

    def teardown_method(self):
        self._store.close()
        self._tmpdir.cleanup()

    def test_compute_no_store(self):
        proj = RuntimeStateProjection(event_store=None)
        state = proj.compute()
        assert state.health == "unknown"
        assert state.active_sessions == []

    def test_compute_empty_store(self):
        proj = RuntimeStateProjection(self._store)
        state = proj.compute()
        assert state.health == "healthy"
        assert state.active_sessions == []

    def test_compute_with_active_session(self):
        obs = RuntimeObservability(self._store)
        session = Session(
            session_id="s1", execution_id="e1", task_id="t1",
            project_id="p1", opencode_session_id=None,
            status="CREATED", created_at="now", updated_at="now",
        )
        obs.emit_session_created(session)
        proj = RuntimeStateProjection(self._store)
        state = proj.compute()
        assert len(state.active_sessions) == 1
        assert state.active_sessions[0]["id"] == "s1"

    def test_compute_with_completed_session(self):
        obs = RuntimeObservability(self._store)
        session = Session(
            session_id="s1", execution_id="e1", task_id="t1",
            project_id="p1", opencode_session_id=None,
            status="CREATED", created_at="now", updated_at="now",
        )
        obs.emit_session_created(session)
        session.status = "COMPLETED"
        obs.emit_session_updated(session)
        proj = RuntimeStateProjection(self._store)
        state = proj.compute()
        assert len(state.active_sessions) == 0

    def test_compute_healthy(self):
        proj = RuntimeStateProjection(self._store)
        state = proj.compute()
        assert state.health == "healthy"

    def test_get_health(self):
        proj = RuntimeStateProjection(self._store)
        health = proj.get_health()
        assert health == "healthy"

    def test_runtime_state_to_dict(self):
        proj = RuntimeStateProjection(self._store)
        state = proj.compute()
        d = state.to_dict()
        assert "runtime" in d
        assert d["runtime"]["health"] == "healthy"

    def test_last_event_empty(self):
        proj = RuntimeStateProjection(self._store)
        state = proj.compute()
        assert state.last_event is None

    def test_failed_executions_count(self):
        obs = RuntimeObservability(self._store)
        obs.emit_execution_failed("exec-001", task_id="t1", error="fail")
        obs.emit_execution_failed("exec-002", task_id="t1", error="fail")
        proj = RuntimeStateProjection(self._store)
        state = proj.compute()
        assert state.failed_executions == 2

    def test_interrupted_sessions_count(self):
        obs = RuntimeObservability(self._store)
        session = Session(
            session_id="s1", execution_id="e1", task_id="t1",
            project_id="p1", opencode_session_id=None,
            status="INTERRUPTED", created_at="now", updated_at="now",
        )
        obs.emit_session_created(session)
        session.status = "INTERRUPTED"
        obs.emit_session_updated(session)
        proj = RuntimeStateProjection(self._store)
        state = proj.compute()
        assert state.interrupted_sessions >= 1

    def test_recovery_status_none(self):
        proj = RuntimeStateProjection(self._store)
        state = proj.compute()
        assert state.recovery_status == "none"

    def test_health_degraded_by_interrupted(self):
        obs = RuntimeObservability(self._store)
        session = Session(
            session_id="s1", execution_id="e1", task_id="t1",
            project_id="p1", opencode_session_id=None,
            status="INTERRUPTED", created_at="now", updated_at="now",
        )
        obs.emit_session_created(session)
        session.status = "INTERRUPTED"
        obs.emit_session_updated(session)
        proj = RuntimeStateProjection(self._store)
        state = proj.compute()
        assert state.health == "degraded"

    def test_event_lag_present(self):
        obs = RuntimeObservability(self._store)
        obs.emit_started()
        proj = RuntimeStateProjection(self._store)
        state = proj.compute()
        assert state.event_lag >= 0.0
