from __future__ import annotations

from typing import Any, Optional

from .models import ToolDefinition, ToolCapability, ToolResult


DEFAULT_DESKTOP_TOOL = ToolDefinition(
    tool_id="desktop.click",
    name="Desktop Click",
    category="desktop",
    capabilities=[
        ToolCapability("ui_interaction", "Click UI elements"),
    ],
    risk_level="high",
    required_autonomy="A4",
    requires_confirmation=True,
    provider="desktop",
)


class DesktopTool:

    @property
    def definition(self) -> ToolDefinition:
        return DEFAULT_DESKTOP_TOOL

    def click(self, x: int = 0, y: int = 0, selector: str = "") -> ToolResult:
        return ToolResult(
            tool_id="desktop.click",
            action="click",
            success=False,
            error="Desktop click not yet implemented — interface only",
        )

    def type_text(self, text: str, selector: str = "") -> ToolResult:
        return ToolResult(
            tool_id="desktop.type",
            action="type",
            success=False,
            error="Desktop type not yet implemented — interface only",
        )
