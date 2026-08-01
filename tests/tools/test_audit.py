from __future__ import annotations

from features.tools.audit import ToolAudit
from features.tools.models import ToolResult, ApprovalRequest, ApprovalState


class TestToolAudit:

    def test_record_request(self):
        audit = ToolAudit()
        audit.record_request("filesystem.read", "read")
        history = audit.get_history()
        assert len(history) == 1
        assert history[0]["event"] == "tool.requested"

    def test_record_approved(self):
        audit = ToolAudit()
        audit.record_approved("t1", "write")
        history = audit.get_history()
        assert history[0]["event"] == "tool.approved"

    def test_record_denied(self):
        audit = ToolAudit()
        audit.record_denied("t1", "write", "not allowed")
        history = audit.get_history()
        assert history[0]["reason"] == "not allowed"

    def test_record_execution(self):
        audit = ToolAudit()
        result = ToolResult(tool_id="t1", action="read", success=True, output="data")
        audit.record_execution("t1", "read", result, 1.5)
        history = audit.get_history()
        assert history[0]["event"] == "tool.executed"
        assert history[0]["duration"] == 1.5

    def test_record_failure(self):
        audit = ToolAudit()
        audit.record_failure("t1", "write", "error!", 2.0)
        history = audit.get_history()
        assert history[0]["event"] == "tool.failed"
        assert history[0]["error"] == "error!"

    def test_get_history_filtered(self):
        audit = ToolAudit()
        audit.record_request("t1", "read")
        audit.record_request("t2", "write")
        h = audit.get_history(tool_id="t1")
        assert len(h) == 1

    def test_clear(self):
        audit = ToolAudit()
        audit.record_request("t1", "read")
        audit.clear()
        assert len(audit.get_history()) == 0

    def test_record_approval_created(self):
        audit = ToolAudit()
        req = ApprovalRequest(
            request_id="r1", tool_id="t1", action="write",
            risk="low", reason="test", requested_by="user",
        )
        audit.record_approval_created(req)
        history = audit.get_history()
        assert history[0]["event"] == "tool.approval_created"
        assert history[0]["request_id"] == "r1"
