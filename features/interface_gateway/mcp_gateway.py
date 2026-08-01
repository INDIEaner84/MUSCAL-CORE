from __future__ import annotations

from typing import Any, Optional

from ..tools.registry import ToolRegistry
from ..tools.models import ToolDefinition, ToolCapability


class MCPGateway:

    def __init__(self, tool_registry: Optional[ToolRegistry] = None):
        self._tool_registry = tool_registry or ToolRegistry()
        self._mcp_tools: dict[str, dict[str, Any]] = {}

    def discover_tools(self, endpoint: str = "") -> list[dict[str, Any]]:
        return [
            {"name": t.name, "tool_id": t.tool_id, "category": t.category, "risk_level": t.risk_level}
            for t in self._tool_registry.list_tools()
        ]

    def register_tool(self, schema: dict[str, Any]) -> dict[str, Any]:
        tool_id = schema.get("tool_id", "")
        if not tool_id:
            raise ValueError("Missing 'tool_id' in schema")
        if tool_id in self._mcp_tools:
            raise ValueError(f"Tool '{tool_id}' already registered")
        required = {"tool_id", "name", "category"}
        missing = required - set(schema.keys())
        if missing:
            raise ValueError(f"Missing required fields: {missing}")
        self._mcp_tools[tool_id] = schema
        td = ToolDefinition(
            tool_id=tool_id,
            name=schema["name"],
            category=schema.get("category", "mcp"),
            capabilities=[
                ToolCapability(c["name"], c.get("description", ""))
                for c in schema.get("capabilities", [])
            ],
            risk_level=schema.get("risk_level", "medium"),
            required_autonomy=schema.get("required_autonomy", "A3"),
            requires_confirmation=schema.get("requires_confirmation", False),
            provider="mcp",
        )
        self._tool_registry.register_tool(td)
        return {"tool_id": tool_id, "status": "registered"}

    def validate_schema(self, schema: dict[str, Any]) -> dict[str, Any]:
        errors = []
        if "tool_id" not in schema:
            errors.append("Missing 'tool_id'")
        if "name" not in schema:
            errors.append("Missing 'name'")
        if "category" not in schema:
            errors.append("Missing 'category'")
        for cap in schema.get("capabilities", []):
            if "name" not in cap:
                errors.append("Capability missing 'name'")
        return {"valid": len(errors) == 0, "errors": errors}

    def route_request(self, tool_id: str, action: str, params: Optional[dict] = None) -> dict[str, Any]:
        if tool_id not in self._mcp_tools:
            raise ValueError(f"MCP tool '{tool_id}' not registered")
        return {"tool_id": tool_id, "action": action, "params": params or {}, "routed": True}

    def list_mcp_tools(self) -> list[dict[str, Any]]:
        return list(self._mcp_tools.values())
