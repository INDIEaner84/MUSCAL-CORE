from __future__ import annotations

from features.tools.policy import ToolPolicy
from features.tools.models import ToolDefinition, ToolCapability


class TestToolPolicy:

    def _make_tool(self, tool_id="filesystem.read", risk="low", autonomy="A1", confirm=False):
        return ToolDefinition(
            tool_id=tool_id, name="Test", category="filesystem",
            capabilities=[ToolCapability("test", "test")],
            risk_level=risk, required_autonomy=autonomy,
            requires_confirmation=confirm, provider="builtin",
        )

    def test_allowed_tool_a1_read(self):
        policy = ToolPolicy()
        tool = self._make_tool("filesystem.read", autonomy="A1")
        allowed, _ = policy.check(tool, "A1")
        assert allowed is True

    def test_denied_tool_a0_write(self):
        policy = ToolPolicy()
        tool = self._make_tool("filesystem.write", autonomy="A3")
        allowed, _ = policy.check(tool, "A0")
        assert allowed is False

    def test_allowed_tool_a3_write(self):
        policy = ToolPolicy()
        tool = self._make_tool("filesystem.write", autonomy="A3")
        allowed, _ = policy.check(tool, "A3")
        assert allowed is True

    def test_requires_confirmation_returns_false(self):
        policy = ToolPolicy()
        tool = self._make_tool("desktop.click", autonomy="A4", confirm=True)
        allowed, _ = policy.check(tool, "A4")
        assert allowed is False

    def test_is_tool_allowed_low_autonomy(self):
        policy = ToolPolicy()
        tool = self._make_tool("desktop.click", autonomy="A4")
        assert policy.is_tool_allowed(tool, "A2") is False

    def test_is_tool_allowed_sufficient(self):
        policy = ToolPolicy()
        tool = self._make_tool("desktop.click", autonomy="A4")
        assert policy.is_tool_allowed(tool, "A4") is True

    def test_denial_message_contains_tool_id(self):
        policy = ToolPolicy()
        tool = self._make_tool("desktop.click", autonomy="A4")
        allowed, reason = policy.check(tool, "A0")
        assert allowed is False
        assert "desktop.click" in reason
