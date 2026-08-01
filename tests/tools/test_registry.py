from __future__ import annotations

from features.tools.registry import ToolRegistry, DEFAULT_TOOLS
from features.tools.models import ToolDefinition, ToolCapability


class TestToolRegistry:

    def test_default_tools_loaded(self):
        registry = ToolRegistry()
        tools = registry.list_tools()
        assert len(tools) == len(DEFAULT_TOOLS)

    def test_get_tool(self):
        registry = ToolRegistry()
        tool = registry.get_tool("filesystem.read")
        assert tool is not None
        assert tool.tool_id == "filesystem.read"

    def test_get_tool_not_found(self):
        registry = ToolRegistry()
        assert registry.get_tool("nonexistent") is None

    def test_register_tool(self):
        registry = ToolRegistry()
        tool = ToolDefinition(
            tool_id="custom.tool", name="Custom", category="custom",
            capabilities=[ToolCapability("custom", "Custom capability")],
            risk_level="low", required_autonomy="A1",
            requires_confirmation=False, provider="test",
        )
        registry.register_tool(tool)
        assert registry.get_tool("custom.tool") is tool

    def test_list_tools_by_category(self):
        registry = ToolRegistry()
        fs_tools = registry.list_tools(category="filesystem")
        assert all(t.category == "filesystem" for t in fs_tools)
        assert len(fs_tools) >= 3

    def test_find_capability(self):
        registry = ToolRegistry()
        tools = registry.find_capability("file_read")
        assert len(tools) >= 1
        assert tools[0].tool_id == "filesystem.read"

    def test_find_capability_not_found(self):
        registry = ToolRegistry()
        tools = registry.find_capability("nonexistent_capability")
        assert len(tools) == 0

    def test_multiple_tools_same_capability(self):
        registry = ToolRegistry()
        tools = registry.find_capability("code_analysis")
        assert len(tools) >= 2

    def test_tool_risk_levels(self):
        registry = ToolRegistry()
        for t in registry.list_tools():
            assert t.risk_level in ("low", "medium", "high")
