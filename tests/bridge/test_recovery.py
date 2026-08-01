from __future__ import annotations

from features.bridge.recovery import RecoveryHandler, RecoveryAction, RecoveryEvent
from features.bridge.opencode_adapter import OpenCodeAdapter, OpenCodeResult


class TestRecovery:

    def test_completed_execution_needs_no_recovery(self):
        adapter = OpenCodeAdapter()
        handler = RecoveryHandler(adapter=adapter)
        result = OpenCodeResult(
            status="completed", return_code=0,
            duration=1.0, stdout="ok", stderr="",
            session_reference="ses_001",
        )
        event = handler.handle(result, "exec-001", "test message")
        assert event.recovered is True
        assert event.original_status == "completed"

    def test_timeout_triggers_retry(self):
        adapter = OpenCodeAdapter(timeout=60)
        handler = RecoveryHandler(adapter=adapter, max_retries=1)
        result = OpenCodeResult(
            status="timeout", return_code=None,
            duration=30.0, stdout="", stderr="timeout",
            session_reference=None,
        )
        event = handler.handle(result, "exec-002", "test message")
        assert event.recovery_action.strategy == "retry"
        assert "timeout" in event.original_status

    def test_not_found_triggers_report_failure(self):
        adapter = OpenCodeAdapter(opencode_path="/nonexistent")
        handler = RecoveryHandler(adapter=adapter)
        result = OpenCodeResult(
            status="not-found", return_code=None,
            duration=0.1, stdout="", stderr="not found",
            session_reference=None,
        )
        event = handler.handle(result, "exec-003", "test")
        assert event.recovery_action.strategy == "report_failure"
        assert event.recovered is False

    def test_determine_strategy(self):
        adapter = OpenCodeAdapter()
        handler = RecoveryHandler(adapter=adapter)

        timeout = OpenCodeResult(status="timeout", return_code=None, duration=30, stdout="", stderr="", session_reference=None)
        assert handler._determine_strategy(timeout) == "retry"

        failed = OpenCodeResult(status="failed", return_code=1, duration=5, stdout="", stderr="error", session_reference="ses_001")
        assert handler._determine_strategy(failed) == "resume_session"

        failed_no_session = OpenCodeResult(status="failed", return_code=1, duration=5, stdout="", stderr="error", session_reference=None)
        assert handler._determine_strategy(failed_no_session) == "retry"

        not_found = OpenCodeResult(status="not-found", return_code=None, duration=0.1, stdout="", stderr="", session_reference=None)
        assert handler._determine_strategy(not_found) == "report_failure"

    def test_recovery_action_dataclass(self):
        action = RecoveryAction(strategy="retry", description="Retrying execution")
        assert action.strategy == "retry"
        assert action.retry_count == 0
        assert action.max_retries == 3

    def test_recovery_event_to_dict(self):
        action = RecoveryAction(strategy="retry", description="test")
        event = RecoveryEvent(
            execution_id="exec-004",
            original_status="timeout",
            recovery_action=action,
            recovered=False,
        )
        d = event.to_dict()
        assert d["recovery_event"]["execution_id"] == "exec-004"
        assert d["recovery_event"]["recovery_action"]["strategy"] == "retry"
        assert d["recovery_event"]["recovered"] is False

    def test_get_recovery_history(self):
        adapter = OpenCodeAdapter()
        handler = RecoveryHandler(adapter=adapter)
        result = OpenCodeResult(
            status="completed", return_code=0,
            duration=1.0, stdout="ok", stderr="",
            session_reference="ses_001",
        )
        handler.handle(result, "exec-005", "test")
        history = handler.get_recovery_history()
        assert len(history) == 1
        assert history[0].execution_id == "exec-005"
