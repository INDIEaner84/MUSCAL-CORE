"""Research Memory - MCP server tests (registration, validation, response schema)."""

import sys

import pytest

from features.research_memory import ResearchMemoryService
from features.research_memory.mcp_server import (
    create_server,
    run_get,
    run_promote,
    run_search,
)

HAS_MCP = True
try:
    import mcp  # noqa: F401
except Exception:
    HAS_MCP = False

pytestmark = pytest.mark.skipif(not HAS_MCP, reason="mcp SDK not installed")


@pytest.fixture
def svc(tmp_path):
    from features.research_memory import (
        ResearchMemoryCache,
        ResearchMemoryRepository,
    )
    from features.research_memory.storage import ResearchMemoryStore

    store = ResearchMemoryStore(str(tmp_path / "mcp.db"))
    repo = ResearchMemoryRepository(store)
    cache = ResearchMemoryCache(repository=repo)
    return ResearchMemoryService(cache=cache)


def _seed(svc):
    rec = svc.save_research(
        "how does mcp work",
        payload={
            "facts": ["mcp is a protocol"],
            "recommendation": "use stdio",
            "confidence": "high",
        },
    )
    return rec


# -- tool registration ------------------------------------------------


def test_three_tools_registered():
    import asyncio

    async def _tools():
        server = create_server()
        return [t.name for t in await server.list_tools()]

    names = asyncio.run(_tools())
    assert names == [
        "research_memory.search",
        "research_memory.get",
        "research_memory.promote",
    ]


# -- search -----------------------------------------------------------


def test_search_returns_matching_records(svc):
    rec = _seed(svc)
    result = run_search({"query": "mcp"}, svc)
    assert result["count"] == 1
    assert result["records"][0]["id"] == rec.id
    assert "facts" in result["records"][0]
    assert "hash" in result["records"][0]


def test_search_requires_query(svc):
    with pytest.raises(ValueError):
        run_search({}, svc)


def test_search_empty_result(svc):
    result = run_search({"query": "definitely not present"}, svc)
    assert result["count"] == 0
    assert result["records"] == []


# -- get -------------------------------------------------------------


def test_get_by_id(svc):
    rec = _seed(svc)
    result = run_get({"id": rec.id}, svc)
    assert result["record"] is not None
    assert result["record"]["query"] == "how does mcp work"
    assert result["record"]["confidence"] == "high"
    assert isinstance(result["record"]["sources"], list)


def test_get_unknown_id_returns_none(svc):
    result = run_get({"id": "no-such-id"}, svc)
    assert result["record"] is None


def test_get_requires_id(svc):
    with pytest.raises(ValueError):
        run_get({}, svc)


# -- promote -----------------------------------------------------------


def test_promote_changes_status(svc):
    rec = _seed(svc)
    result = run_promote({"id": rec.id}, svc)
    assert result["record"]["status"] == "accepted"


def test_promote_unknown_id_raises(svc):
    with pytest.raises(ValueError):
        run_promote({"id": "no-such-id"}, svc)


def test_promote_requires_id(svc):
    with pytest.raises(ValueError):
        run_promote({}, svc)