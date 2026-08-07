"""Research Pipeline - MCP stdio server (OpenCode tool).

Exposes one orchestrated tool:

    research.execute
        input:  { question (required), context?, depth? }
        output: { facts, analysis, options, recommendation, confidence,
                  sources, warnings }

Run:
    .venv/bin/python -m features.research_pipeline.mcp_server
"""

from __future__ import annotations

import asyncio
import sys

from .models import ResearchRequest, ResearchResult
from .service import ResearchPipelineService

TOOL_NAME = "research.execute"
TOOL_DESCRIPTION = (
    "Execute research end to end: serve from Research Memory when a fresh "
    "result exists, otherwise run the configured research provider "
    "(browser_intelligence) and persist the result for reuse."
)


def run_execute(payload: dict, service: ResearchPipelineService | None = None) -> dict:
    """Validate + run the pipeline synchronously (MCP tools are sync)."""
    payload = payload or {}
    question = payload.get("question")
    if not isinstance(question, str) or not question.strip():
        raise ValueError("Parameter 'question' is required and must be a non-empty string")

    request = ResearchRequest(
        question=question.strip(),
        context=payload.get("context") or "",
        depth=payload.get("depth") or "standard",
        force_refresh=bool(payload.get("force_refresh")),
        metadata=payload.get("metadata") or {},
    )
    service = service or ResearchPipelineService()
    result = asyncio.run(service.research(request))
    return _result_payload(result)


def _result_payload(result: ResearchResult) -> dict:
    return {
        "facts": list(result.facts),
        "analysis": result.analysis or "",
        "options": list(result.options),
        "recommendation": result.recommendation or "",
        "confidence": (result.confidence or "low").lower(),
        "sources": list(result.sources),
        "warnings": list(result.warnings),
    }


def create_server(service: ResearchPipelineService | None = None):
    """Build the FastMCP server (lazy import keeps the plugin loader safe)."""
    from mcp.server.fastmcp import FastMCP

    server = FastMCP(
        "research-pipeline",
        instructions=(
            "Research pipeline: end-to-end research with memory. Use "
            "research.execute with a concrete question and optional context "
            "and depth (quick/standard/deep). Repeated questions are served "
            "from Research Memory unless force_refresh is true."
        ),
    )

    _svc = service

    @server.tool(name=TOOL_NAME, description=TOOL_DESCRIPTION)
    def research_execute(
        question: str,
        context: str = "",
        depth: str = "standard",
        force_refresh: bool = False,
    ) -> dict:
        return run_execute(
            {
                "question": question,
                "context": context,
                "depth": depth,
                "force_refresh": force_refresh,
            },
            _svc,
        )

    return server


def main(argv=None) -> int:
    server = create_server()
    server.run()
    return 0


if __name__ == "__main__":
    sys.exit(main())