"""Browser Intelligence — MCP stdio server (OpenCode tool).

Exposes the existing `ResearchService` as the MCP tool `browser_intelligence.research`
so OpenCode and other MCP clients can trigger targeted web research and receive
structured findings. The server is a thin adapter: it reuses the service, models
and provider stack unchanged and adds no browser logic of its own.

Run:
    .venv/bin/python -m features.browser_intelligence.mcp_server

Tool input:
    {
        "question": str,        # required
        "context":  str = "",   # optional research topic/context
        "depth":    str = "standard"  # "quick" | "standard" | "deep"
    }

Tool output:
    {
        "facts": [...], "analysis": str, "options": [...],
        "recommendation": str, "confidence": str, "warnings": [...]
    }
    plus "sources" and "question" for traceability.
"""

from __future__ import annotations

import sys

from .mcp_registration import TOOL_SCHEMA

TOOL_ID = TOOL_SCHEMA["tool_id"]
TOOL_NAME = TOOL_ID  # "browser_intelligence.research"
TOOL_DESCRIPTION = (
    "Run targeted web research and return structured findings "
    "(FACTS / ANALYSIS / OPTIONS / RECOMMENDATION / CONFIDENCE plus sources). "
    "Uses Browser-Use + local Ollama."
)

ALLOWED_DEPTHS = ("quick", "standard", "deep")

_DEPTH_CONSTRAINTS = {
    "quick": ["answer concisely", "keep research to the first reliable source"],
    "standard": [],
    "deep": ["research multiple sources", "cross-check claims", "cover alternatives"],
}


def build_constraints(depth: str) -> list:
    """Translate a depth level into provider constraint hints."""
    return list(_DEPTH_CONSTRAINTS.get(depth, []))


def findings_to_payload(findings) -> dict:
    """Map a ResearchFindings object to the MCP tool output shape."""
    return {
        "facts": list(getattr(findings, "facts", []) or []),
        "analysis": getattr(findings, "analysis", "") or "",
        "options": list(getattr(findings, "options", []) or []),
        "recommendation": getattr(findings, "recommendation", "") or "",
        "confidence": getattr(findings, "confidence", "Low") or "Low",
        "warnings": list(getattr(findings, "warnings", []) or []),
        "sources": [s.to_dict() for s in getattr(findings, "sources", []) or []],
    }


def run_research(payload: dict, service=None) -> dict:
    """Validate a research request and execute it through ResearchService.

    `service` is injectable for tests; defaults to the real service.
    Raises ValueError on invalid input.
    """
    payload = payload or {}
    question = payload.get("question")
    if not isinstance(question, str) or not question.strip():
        raise ValueError("Parameter 'question' is required and must be a non-empty string")

    context = payload.get("context") or ""
    depth = payload.get("depth") or "standard"
    if depth not in ALLOWED_DEPTHS:
        raise ValueError(f"Parameter 'depth' must be one of {list(ALLOWED_DEPTHS)}; got {depth!r}")

    if service is None:
        from .research_service import ResearchService

        service = ResearchService()

    findings = service.research(
        question.strip(),
        topic=context.strip() if context else "",
        constraints=build_constraints(depth),
    )
    return findings_to_payload(findings)


def register_with_gateway(gateway=None) -> dict:
    """Register this tool in the existing MUSCAL interface gateway.

    Thin wrapper over `mcp_registration.register_research_tool` so the MCP
    server and the gateway registration stay in sync. Never raises.
    """
    from .mcp_registration import register_research_tool

    return register_research_tool(gateway)


def create_server():
    """Build the FastMCP server (lazy import keeps the plugin loader safe)."""
    from mcp.server.fastmcp import FastMCP

    server = FastMCP(
        "browser-intelligence",
        instructions=(
            "Browser intelligence: targeted web research for development. "
            "Use the research tool with a concrete question and an optional "
            "context and depth (quick/standard/deep)."
        ),
    )

    @server.tool(name=TOOL_NAME, description=TOOL_DESCRIPTION)
    def browser_intelligence_research(
        question: str,
        context: str = "",
        depth: str = "standard",
    ) -> dict:
        return run_research({"question": question, "context": context, "depth": depth})

    return server


def main(argv=None) -> int:
    server = create_server()
    server.run()
    return 0


if __name__ == "__main__":
    sys.exit(main())