"""Browser Intelligence - MCP gateway registration.

Registers the research capability as a tool in the existing MUSCAL
interface gateway (features/interface_gateway/MCPGateway) and the Unified
Tool Runtime registry (features/tools), without touching Core.

All imports are lazy and guarded: if the gateway is not importable the
registration degrades to a no-op with a status report.
"""

from __future__ import annotations

TOOL_SCHEMA = {
    "tool_id": "browser_intelligence.research",
    "name": "Browser Research",
    "category": "research",
    "risk_level": "medium",
    "required_autonomy": "A3",
    "requires_confirmation": False,
    "capabilities": [
        {"name": "web_research", "description": "LLM-driven web research with browser-use"},
        {"name": "source_collection", "description": "Collect and verify web sources"},
    ],
}


def register_research_tool(mcp_gateway=None):
    """Register the research tool. Returns a status dict, never raises."""
    status = {"registered": False, "gateway": "unavailable", "error": ""}
    try:
        from ..interface_gateway.mcp_gateway import MCPGateway

        gateway = mcp_gateway or MCPGateway()
        gateway.register_tool(TOOL_SCHEMA)
        status.update({"registered": True, "gateway": "mcp_gateway"})
    except Exception as exc:  # pragma: no cover - graceful degradation
        status["error"] = str(exc)
    return status


def unregister_research_tool(mcp_gateway=None):
    status = {"unregistered": False, "gateway": "unavailable", "error": ""}
    try:
        from ..interface_gateway.mcp_gateway import MCPGateway

        gateway = mcp_gateway or MCPGateway()
        # MCPGateway keeps a private dict; remove if present, otherwise no-op
        for tool_id in list(gateway._mcp_tools.keys()):
            if tool_id == TOOL_SCHEMA["tool_id"]:
                gateway._mcp_tools.pop(tool_id, None)
        status.update({"unregistered": True, "gateway": "mcp_gateway"})
    except Exception as exc:  # pragma: no cover
        status["error"] = str(exc)
    return status
