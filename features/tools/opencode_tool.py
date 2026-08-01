from __future__ import annotations

from typing import Any, Optional

from .models import ToolDefinition, ToolCapability, ToolResult
from ..bridge.opencode_adapter import OpenCodeAdapter


DEFAULT_OPENCODE_TOOL = ToolDefinition(
    tool_id="opencode.execute",
    name="Execute OpenCode Task",
    category="opencode",
    capabilities=[
        ToolCapability("code_analysis", "Analyze and modify code"),
        ToolCapability("task_execution", "Execute software engineering tasks"),
    ],
    risk_level="high",
    required_autonomy="A3",
    requires_confirmation=False,
    provider="opencode",
)


class OpenCodeTool:

    def __init__(self, adapter: Optional[OpenCodeAdapter] = None):
        self._adapter = adapter or OpenCodeAdapter()

    @property
    def definition(self) -> ToolDefinition:
        return DEFAULT_OPENCODE_TOOL

    def execute(self, message: str, workdir: Optional[str] = None,
                session: Optional[str] = None,
                model: Optional[str] = None,
                agent: Optional[str] = None) -> ToolResult:
        from pathlib import Path
        wd = Path(workdir) if workdir else None
        result = self._adapter.execute(
            message=message,
            workdir=wd,
            session=session,
            model=model,
            agent=agent,
        )
        return ToolResult(
            tool_id="opencode.execute",
            action="execute",
            success=result.status == "completed",
            output={
                "status": result.status,
                "stdout": result.stdout[:2000] if result.stdout else "",
                "session_reference": result.session_reference,
            },
            error=result.stderr if result.status != "completed" else "",
            duration=result.duration,
        )
