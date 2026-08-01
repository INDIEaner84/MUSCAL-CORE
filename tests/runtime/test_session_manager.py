from __future__ import annotations

import uuid

from features.runtime.session_manager import SessionManager
from features.runtime.models import Session


class TestSessionManager:

    def test_create_session(self):
        mgr = SessionManager()
        session = mgr.create_session(task_id="task-001", project_id="/test/repo")
        assert session.session_id is not None
        assert session.task_id == "task-001"
        assert session.project_id == "/test/repo"
        assert session.status == "CREATED"
        assert session.last_checkpoint is None

    def test_create_session_with_opencode_session(self):
        mgr = SessionManager()
        session = mgr.create_session(
            task_id="task-001", project_id="/test/repo",
            opencode_session_id="ses_abc123",
        )
        assert session.opencode_session_id == "ses_abc123"

    def test_update_session(self):
        mgr = SessionManager()
        session = mgr.create_session(task_id="task-001", project_id="/test/repo")
        updated = mgr.update_session(session.session_id, "RUNNING")
        assert updated is not None
        assert updated.status == "RUNNING"
        assert updated.updated_at != session.created_at

    def test_update_session_not_found(self):
        mgr = SessionManager()
        result = mgr.update_session("nonexistent", "COMPLETED")
        assert result is None

    def test_invalid_state_raises(self):
        mgr = SessionManager()
        session = mgr.create_session(task_id="task-001", project_id="/test/repo")
        try:
            mgr.update_session(session.session_id, "INVALID_STATE")
            assert False, "Should have raised ValueError"
        except ValueError:
            pass

    def test_complete_session(self):
        mgr = SessionManager()
        session = mgr.create_session(task_id="task-001", project_id="/test/repo")
        completed = mgr.complete_session(session.session_id)
        assert completed is not None
        assert completed.status == "COMPLETED"

    def test_fail_session(self):
        mgr = SessionManager()
        session = mgr.create_session(task_id="task-001", project_id="/test/repo")
        failed = mgr.fail_session(session.session_id)
        assert failed is not None
        assert failed.status == "FAILED"

    def test_get_session(self):
        mgr = SessionManager()
        created = mgr.create_session(task_id="task-001", project_id="/test/repo")
        fetched = mgr.get_session(created.session_id)
        assert fetched is not None
        assert fetched.session_id == created.session_id

    def test_get_session_not_found(self):
        mgr = SessionManager()
        assert mgr.get_session("nonexistent") is None

    def test_list_active_sessions(self):
        mgr = SessionManager()
        s1 = mgr.create_session(task_id="task-001", project_id="/test/repo")
        s2 = mgr.create_session(task_id="task-002", project_id="/test/repo")
        mgr.complete_session(s1.session_id)
        active = mgr.list_active_sessions()
        assert len(active) == 1
        assert active[0].session_id == s2.session_id

    def test_lookup_by_task(self):
        mgr = SessionManager()
        mgr.create_session(task_id="task-001", project_id="/test/repo")
        mgr.create_session(task_id="task-001", project_id="/test/repo")
        results = mgr.lookup_by_task("task-001")
        assert len(results) == 2

    def test_lookup_by_execution(self):
        mgr = SessionManager()
        session = mgr.create_session(task_id="task-001", project_id="/test/repo")
        results = mgr.lookup_by_execution(session.execution_id)
        assert len(results) == 1

    def test_has_active_execution(self):
        mgr = SessionManager()
        mgr.create_session(task_id="task-001", project_id="/test/repo")
        assert mgr.has_active_execution("task-001")

    def test_has_active_execution_after_complete(self):
        mgr = SessionManager()
        session = mgr.create_session(task_id="task-001", project_id="/test/repo")
        mgr.complete_session(session.session_id)
        assert not mgr.has_active_execution("task-001")

    def test_clear(self):
        mgr = SessionManager()
        mgr.create_session(task_id="task-001", project_id="/test/repo")
        assert len(mgr.all_sessions()) == 1
        mgr.clear()
        assert len(mgr.all_sessions()) == 0

    def test_session_to_dict(self):
        mgr = SessionManager()
        session = mgr.create_session(
            task_id="task-001", project_id="/test/repo",
            opencode_session_id="ses_001",
        )
        d = session.to_dict()
        assert d["session"]["task_id"] == "task-001"
        assert d["session"]["opencode_session_id"] == "ses_001"
        assert d["session"]["status"] == "CREATED"

    def test_session_invalid_state_raises(self):
        try:
            Session(
                session_id="s1", execution_id="e1", task_id="t1",
                project_id="p1", opencode_session_id=None,
                status="INVALID", created_at="now", updated_at="now",
            )
            assert False, "Should have raised ValueError"
        except ValueError:
            pass

    def test_multiple_sessions_isolation(self):
        mgr = SessionManager()
        s1 = mgr.create_session(task_id="task-001", project_id="/repo1")
        s2 = mgr.create_session(task_id="task-002", project_id="/repo2")
        assert s1.session_id != s2.session_id
        assert s1.execution_id != s2.execution_id

    def test_update_preserves_opencode_session(self):
        mgr = SessionManager()
        session = mgr.create_session(
            task_id="task-001", project_id="/test/repo",
            opencode_session_id="ses_old",
        )
        mgr.update_session(session.session_id, "RUNNING", opencode_session_id="ses_new")
        updated = mgr.get_session(session.session_id)
        assert updated is not None
        assert updated.opencode_session_id == "ses_new"

    def test_interrupt_session(self):
        mgr = SessionManager()
        session = mgr.create_session(task_id="task-001", project_id="/test/repo")
        mgr.update_session(session.session_id, "RUNNING")
        interrupted = mgr.interrupt_session(session.session_id, "Test interruption")
        assert interrupted is not None
        assert interrupted.status == "INTERRUPTED"

    def test_interrupt_session_not_found(self):
        mgr = SessionManager()
        result = mgr.interrupt_session("nonexistent")
        assert result is None

    def test_detect_interrupted(self):
        mgr = SessionManager()
        s1 = mgr.create_session(task_id="task-001", project_id="/test/repo")
        mgr.update_session(s1.session_id, "RUNNING")
        s2 = mgr.create_session(task_id="task-002", project_id="/test/repo")
        mgr.complete_session(s2.session_id)
        interrupted = mgr.detect_interrupted()
        assert len(interrupted) == 1
        assert interrupted[0].session_id == s1.session_id
        assert mgr.get_session(s1.session_id).status == "INTERRUPTED"

    def test_recover_sessions_no_store(self):
        mgr = SessionManager()
        count = mgr.recover_sessions()
        assert count == 0

    def test_session_interrupted_state_valid(self):
        mgr = SessionManager()
        session = mgr.create_session(task_id="task-001", project_id="/test/repo")
        mgr.update_session(session.session_id, "INTERRUPTED")
        assert mgr.get_session(session.session_id).status == "INTERRUPTED"
