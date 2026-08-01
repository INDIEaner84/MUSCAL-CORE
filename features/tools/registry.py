from __future__ import annotations

from typing import Any, Optional

from .models import ToolDefinition, ToolCapability


DEFAULT_TOOLS: list[ToolDefinition] = [
    ToolDefinition(
        tool_id="filesystem.read",
        name="Read File",
        category="filesystem",
        capabilities=[ToolCapability("file_read", "Read file contents")],
        risk_level="low", required_autonomy="A1", requires_confirmation=False, provider="builtin",
    ),
    ToolDefinition(
        tool_id="filesystem.write",
        name="Write File",
        category="filesystem",
        capabilities=[ToolCapability("file_write", "Write or modify file contents")],
        risk_level="medium", required_autonomy="A3", requires_confirmation=False, provider="builtin",
    ),
    ToolDefinition(
        tool_id="opencode.execute",
        name="Execute OpenCode Task",
        category="opencode",
        capabilities=[ToolCapability("code_analysis", "Analyze and modify code"),
                      ToolCapability("task_execution", "Execute software engineering tasks")],
        risk_level="high", required_autonomy="A3", requires_confirmation=False, provider="opencode",
    ),
    ToolDefinition(
        tool_id="desktop.click",
        name="Desktop Click",
        category="desktop",
        capabilities=[ToolCapability("ui_interaction", "Click UI elements")],
        risk_level="high", required_autonomy="A4", requires_confirmation=True, provider="desktop",
    ),
    ToolDefinition(
        tool_id="desktop.type",
        name="Desktop Type",
        category="desktop",
        capabilities=[ToolCapability("ui_interaction", "Type text into UI elements")],
        risk_level="high", required_autonomy="A4", requires_confirmation=True, provider="desktop",
    ),
    ToolDefinition(
        tool_id="browser.navigate",
        name="Browser Navigate",
        category="browser",
        capabilities=[ToolCapability("web_navigation", "Navigate to URLs")],
        risk_level="medium", required_autonomy="A3", requires_confirmation=False, provider="browser",
    ),
    ToolDefinition(
        tool_id="browser.screenshot",
        name="Browser Screenshot",
        category="browser",
        capabilities=[ToolCapability("web_capture", "Capture browser screenshots")],
        risk_level="low", required_autonomy="A2", requires_confirmation=False, provider="browser",
    ),
    ToolDefinition(
        tool_id="filesystem.list",
        name="List Directory",
        category="filesystem",
        capabilities=[ToolCapability("file_discovery", "List directory contents")],
        risk_level="low", required_autonomy="A1", requires_confirmation=False, provider="builtin",
    ),
    ToolDefinition(
        tool_id="filesystem.search",
        name="Search Files",
        category="filesystem",
        capabilities=[ToolCapability("file_search", "Search files by pattern")],
        risk_level="low", required_autonomy="A1", requires_confirmation=False, provider="builtin",
    ),
    ToolDefinition(
        tool_id="opencode.inspect",
        name="Inspect with OpenCode",
        category="opencode",
        capabilities=[ToolCapability("code_analysis", "Analyze code structure and quality")],
        risk_level="low", required_autonomy="A1", requires_confirmation=False, provider="opencode",
    ),
]


class ToolRegistry:

    def __init__(self, tools: Optional[list[ToolDefinition]] = None):
        self._tools: dict[str, ToolDefinition] = {}
        for t in (tools or DEFAULT_TOOLS):
            self._tools[t.tool_id] = t

    def register_tool(self, tool: ToolDefinition) -> None:
        self._tools[tool.tool_id] = tool

    def get_tool(self, tool_id: str) -> Optional[ToolDefinition]:
        return self._tools.get(tool_id)

    def list_tools(self, category: Optional[str] = None) -> list[ToolDefinition]:
        if category:
            return [t for t in self._tools.values() if t.category == category]
        return list(self._tools.values())

    def find_capability(self, capability_name: str) -> list[ToolDefinition]:
        return [t for t in self._tools.values()
                if any(c.name == capability_name for c in t.capabilities)]
