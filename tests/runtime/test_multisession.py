from __future__ import annotations

from features.runtime.session_manager import SessionManager


class TestMultisessionCoordination:

    def test_two_tasks_two_sessions(self):
        mgr = SessionManager()
        s1 = mgr.create_session(task_id="task-A", project_id="/repo")
        s2 = mgr.create_session(task_id="task-B", project_id="/repo")
        assert s1.task_id == "task-A"
        assert s2.task_id == "task-B"
        assert s1.session_id != s2.session_id

    def test_lookup_session_by_task(self):
        mgr = SessionManager()
        mgr.create_session(task_id="task-A", project_id="/repo")
        mgr.create_session(task_id="task-A", project_id="/repo")
        results = mgr.lookup_by_task("task-A")
        assert len(results) == 2

    def test_lookup_session_by_execution(self):
        mgr = SessionManager()
        s1 = mgr.create_session(task_id="task-A", project_id="/repo")
        s2 = mgr.create_session(task_id="task-B", project_id="/repo")
        results = mgr.lookup_by_execution(s1.execution_id)
        assert len(results) == 1
        assert results[0].session_id == s1.session_id

    def test_prevent_duplicate_active_execution(self):
        mgr = SessionManager()
        mgr.create_session(task_id="task-A", project_id="/repo")
        assert mgr.has_active_execution("task-A")

    def test_allow_new_after_completion(self):
        mgr = SessionManager()
        s1 = mgr.create_session(task_id="task-A", project_id="/repo")
        mgr.complete_session(s1.session_id)
        mgr.create_session(task_id="task-A", project_id="/repo")
        active = mgr.list_active_sessions()
        assert len(active) == 1

    def test_isolation_between_tasks(self):
        mgr = SessionManager()
        s_a = mgr.create_session(task_id="task-A", project_id="/repo")
        s_b = mgr.create_session(task_id="task-B", project_id="/repo")
        mgr.complete_session(s_a.session_id)
        assert mgr.has_active_execution("task-B")
        assert not mgr.has_active_execution("task-A")

    def test_list_active_sessions_multiple(self):
        mgr = SessionManager()
        mgr.create_session(task_id="task-A", project_id="/repo")
        mgr.create_session(task_id="task-B", project_id="/repo")
        mgr.create_session(task_id="task-C", project_id="/repo")
        active = mgr.list_active_sessions()
        assert len(active) == 3
