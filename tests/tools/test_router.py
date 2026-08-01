from __future__ import annotations

from features.tools.router import ToolRouter
from features.tools.models import ToolDefinition, ToolCapability


class TestToolRouter:

    def test_find_tool_for_capability(self):
        router = ToolRouter()
        tool = router.find_tool_for_capability("file_read")
        assert tool is not None
        assert tool.tool_id == "filesystem.read"

    def test_find_tool_not_found(self):
        router = ToolRouter()
        tool = router.find_tool_for_capability("nonexistent")
        assert tool is None

    def test_find_tools_for_task(self):
        router = ToolRouter()
        tools = router.find_tools_for_task(["file_read", "file_write"])
        assert len(tools) >= 2
        assert any(t.tool_id == "filesystem.read" for t in tools)

    def test_find_tools_dedup_same_tool(self):
        router = ToolRouter()
        tools = router.find_tools_for_task(["file_read", "file_read"])
        assert len(tools) == 1
        assert tools[0].tool_id == "filesystem.read"
