from __future__ import annotations

from typing import Any, Optional

from .models import ToolDefinition, ToolCapability, ToolResult


DEFAULT_BROWSER_TOOL = ToolDefinition(
    tool_id="browser.navigate",
    name="Browser Navigate",
    category="browser",
    capabilities=[
        ToolCapability("web_navigation", "Navigate to URLs"),
    ],
    risk_level="medium",
    required_autonomy="A3",
    requires_confirmation=False,
    provider="browser",
)


class BrowserTool:

    @property
    def definition(self) -> ToolDefinition:
        return DEFAULT_BROWSER_TOOL

    def navigate(self, url: str) -> ToolResult:
        return ToolResult(
            tool_id="browser.navigate",
            action="navigate",
            success=False,
            error="Browser navigation not yet implemented — interface only",
        )

    def screenshot(self, url: str) -> ToolResult:
        return ToolResult(
            tool_id="browser.screenshot",
            action="screenshot",
            success=False,
            error="Browser screenshot not yet implemented — interface only",
        )
