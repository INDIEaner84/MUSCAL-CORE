from __future__ import annotations

from pathlib import Path

from features.bridge.session_continuity import SessionContinuityTracker
from features.bridge.project_scanner import ProjectScanner, GitStatus, ProjectContext
from features.bridge.task_contract import TaskContract


class TestSessionContinuity:

    def _make_context(self) -> ProjectContext:
        return ProjectContext(
            root=Path("/test/repo"),
            repository="test",
            branch="main",
            commit="abc1234",
            git=GitStatus(dirty=False, modified_count=0, untracked_count=0),
            scan_timestamp="2026-07-28T12:00:00",
            scan_status="ok",
        )

    def _make_task(self) -> TaskContract:
        return TaskContract(id="task-001", project="test", objective="do something")

    def test_record_execution(self):
        tracker = SessionContinuityTracker()
        record = tracker.record_execution(
            project=self._make_context(),
            task=self._make_task(),
            opencode_session="ses_001",
        )
        assert record.bridge_execution_id is not None
        assert record.opencode_session_id == "ses_001"
        assert record.status == "completed"

    def test_get_last_execution(self):
        tracker = SessionContinuityTracker()
        r1 = tracker.record_execution(
            project=self._make_context(), task=self._make_task(),
            opencode_session="ses_001",
        )
        r2 = tracker.record_execution(
            project=self._make_context(), task=self._make_task(),
            opencode_session="ses_002",
        )
        last = tracker.get_last_execution()
        assert last is not None
        assert last.bridge_execution_id == r2.bridge_execution_id

    def test_get_execution_by_id(self):
        tracker = SessionContinuityTracker()
        r1 = tracker.record_execution(
            project=self._make_context(), task=self._make_task(),
            opencode_session="ses_001",
        )
        found = tracker.get_execution(r1.bridge_execution_id)
        assert found is not None
        assert found.bridge_execution_id == r1.bridge_execution_id

    def test_get_execution_not_found(self):
        tracker = SessionContinuityTracker()
        found = tracker.get_execution("nonexistent")
        assert found is None

    def test_update_next_action(self):
        tracker = SessionContinuityTracker()
        r1 = tracker.record_execution(
            project=self._make_context(), task=self._make_task(),
            opencode_session="ses_001",
        )
        tracker.update_next_action(r1.bridge_execution_id, "Review results")
        updated = tracker.get_execution(r1.bridge_execution_id)
        assert updated is not None
        assert updated.next_action == "Review results"

    def test_clear_history(self):
        tracker = SessionContinuityTracker()
        tracker.record_execution(
            project=self._make_context(), task=self._make_task(),
            opencode_session="ses_001",
        )
        assert len(tracker.get_history()) == 1
        tracker.clear_history()
        assert len(tracker.get_history()) == 0

    def test_execution_record_to_dict(self):
        tracker = SessionContinuityTracker()
        r1 = tracker.record_execution(
            project=self._make_context(), task=self._make_task(),
            opencode_session="ses_001",
        )
        d = r1.to_dict()
        assert "execution_record" in d
        assert d["execution_record"]["opencode_session_id"] == "ses_001"
        assert d["execution_record"]["project_identity"]["branch"] == "main"
