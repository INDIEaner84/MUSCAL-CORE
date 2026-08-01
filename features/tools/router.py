from __future__ import annotations

from typing import Any, Optional

from .models import ToolDefinition, ToolResult
from .registry import ToolRegistry


class ToolRouter:

    def __init__(self, registry: Optional[ToolRegistry] = None):
        self._registry = registry or ToolRegistry()

    def find_tool_for_capability(self, capability: str) -> Optional[ToolDefinition]:
        tools = self._registry.find_capability(capability)
        if tools:
            return tools[0]
        return None

    def find_tools_for_task(self, capabilities: list[str]) -> list[ToolDefinition]:
        found: list[ToolDefinition] = []
        seen: set[str] = set()
        for cap in capabilities:
            for t in self._registry.find_capability(cap):
                if t.tool_id not in seen:
                    found.append(t)
                    seen.add(t.tool_id)
        return found
