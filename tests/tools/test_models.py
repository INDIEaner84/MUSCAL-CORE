from __future__ import annotations

from features.tools.models import (
    ToolDefinition, ToolCapability, ApprovalRequest, ApprovalState, ToolResult,
)


class TestToolModels:

    def test_tool_capability(self):
        c = ToolCapability("file_read", "Read files")
        assert c.name == "file_read"
        d = c.to_dict()
        assert d["tool_capability"]["name"] == "file_read"

    def test_tool_definition(self):
        cap = ToolCapability("file_read", "Read files")
        t = ToolDefinition(
            tool_id="filesystem.read", name="Read", category="filesystem",
            capabilities=[cap], risk_level="low", required_autonomy="A1",
            requires_confirmation=False, provider="builtin",
        )
        assert t.tool_id == "filesystem.read"
        d = t.to_dict()
        assert d["tool_definition"]["risk_level"] == "low"

    def test_approval_request_defaults(self):
        req = ApprovalRequest(
            request_id="r1", tool_id="filesystem.write", action="write",
            risk="medium", reason="need to modify", requested_by="agent1",
        )
        assert req.state == ApprovalState.PENDING
        assert req.created_at != ""

    def test_approval_request_to_dict(self):
        req = ApprovalRequest(
            request_id="r1", tool_id="t1", action="write",
            risk="high", reason="test", requested_by="user",
        )
        d = req.to_dict()
        assert d["approval_request"]["state"] == "PENDING"

    def test_approval_state_enum(self):
        assert ApprovalState.PENDING.value == "PENDING"
        assert ApprovalState.APPROVED.value == "APPROVED"
        assert ApprovalState.DENIED.value == "DENIED"
        assert ApprovalState.EXPIRED.value == "EXPIRED"

    def test_tool_result_success(self):
        r = ToolResult(tool_id="t1", action="read", success=True, output="content")
        assert r.success is True
        d = r.to_dict()
        assert d["tool_result"]["output"] == "content"

    def test_tool_result_failure(self):
        r = ToolResult(tool_id="t1", action="write", success=False, error="permission denied")
        assert r.success is False
        d = r.to_dict()
        assert "permission denied" in d["tool_result"]["error"]
