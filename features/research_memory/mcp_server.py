"""Research Memory - MCP stdio server (OpenCode tool).

Exposes three read/manage tools for the stored research memory:

    research_memory.search   (query, domain?, status?, limit?) -> matching records
    research_memory.get      (id) -> single ResearchRecord
    research_memory.promote  (id) -> promote NEW/REVIEWED record to ACCEPTED

Run:
    .venv/bin/python -m features.research_memory.mcp_server
"""

from __future__ import annotations

import sys

from .config import get_config
from .service import ResearchMemoryService

TOOL_PREFIX = "research_memory"

SEARCH_DESCRIPTION = "Search stored research memory records (by keyword in query/context/analysis)."
GET_DESCRIPTION = "Fetch a single stored research record by its id."
PROMOTE_DESCRIPTION = "Promote a research record from NEW/REVIEWED to ACCEPTED (marks it trustworthy)."


def run_search(payload: dict, service: ResearchMemoryService | None = None) -> dict:
    """Validate and execute research_memory.search."""
    payload = payload or {}
    query = payload.get("query", "").strip()
    if not query:
        raise ValueError("Parameter 'query' is required and must be a non-empty string")
    service = service or ResearchMemoryService()
    records = service.search_records(
        keyword=query,
        domain=payload.get("domain") or None,
        status=payload.get("status") or None,
        limit=int(payload.get("limit") or 20),
    )
    return {"count": len(records), "records": [r.to_dict() for r in records]}


def run_get(payload: dict, service: ResearchMemoryService | None = None) -> dict:
    payload = payload or {}
    record_id = payload.get("id", "").strip()
    if not record_id:
        raise ValueError("Parameter 'id' is required and must be a non-empty string")
    service = service or ResearchMemoryService()
    record = service.find_by_id(record_id)
    return {"record": record.to_dict() if record else None}


def run_promote(payload: dict, service: ResearchMemoryService | None = None) -> dict:
    payload = payload or {}
    record_id = payload.get("id", "").strip()
    if not record_id:
        raise ValueError("Parameter 'id' is required and must be a non-empty string")
    service = service or ResearchMemoryService()
    updated = service.promote_candidate(record_id)
    if updated is None:
        raise ValueError(f"Research record '{record_id}' not found")
    return {"record": updated.to_dict()}


def create_server(service: ResearchMemoryService | None = None) -> object:
    """Build the FastMCP server (lazy import keeps the plugin loader safe)."""
    from mcp.server.fastmcp import FastMCP

    server = FastMCP(
        "research-memory",
        instructions=(
            "Research Memory: a persistent, SQLite-backed cache of prior research "
            "findings. Use search/get to inspect stored knowledge, promote to "
            "accept records as trustworthy. Compute new research via the "
            "browser_intelligence.research tool."
        ),
    )

    _svc = service

    @server.tool(name=f"{TOOL_PREFIX}.search", description=SEARCH_DESCRIPTION)
    def research_memory_search(query: str, domain: str = "", status: str = "", limit: int = 20) -> dict:
        return run_search({"query": query, "domain": domain, "status": status, "limit": limit}, _svc)

    @server.tool(name=f"{TOOL_PREFIX}.get", description=GET_DESCRIPTION)
    def research_memory_get(id: str) -> dict:
        return run_get({"id": id}, _svc)

    @server.tool(name=f"{TOOL_PREFIX}.promote", description=PROMOTE_DESCRIPTION)
    def research_memory_promote(id: str) -> dict:
        return run_promote({"id": id}, _svc)

    return server


def main(argv=None) -> int:
    server = create_server()
    server.run()
    return 0


if __name__ == "__main__":
    sys.exit(main())