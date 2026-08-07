"""Research Pipeline - MCP server tests (registration, schema, response)."""

import asyncio

import pytest

from features.research_pipeline import ResearchPipelineService
from features.research_pipeline.mcp_server import (
    TOOL_NAME,
    create_server,
    run_execute,
)
from features.research_pipeline.models import ResearchResult
from features.research_pipeline.registry import ResearchProviderRegistry

HAS_MCP = True
try:
    import mcp  # noqa: F401
except Exception:
    HAS_MCP = False

pytestmark = pytest.mark.skipif(not HAS_MCP, reason="mcp SDK not installed")


def test_tool_registration():
    async def _check():
        server = create_server()
        tools = [t for t in await server.list_tools() if t.name == TOOL_NAME]
        return tools

    tools = asyncio.run(_check())
    assert len(tools) == 1
    assert tools[0].name == "research.execute"


def test_tool_schema():
    async def _check():
        server = create_server()
        tools = await server.list_tools()
        return [t.inputSchema for t in tools if t.name == TOOL_NAME][0]

    schema = asyncio.run(_check())
    assert schema["required"] == ["question"]
    props = schema.get("properties", {})
    assert "question" in props
    assert "context" in props
    assert "depth" in props


def test_validation_requires_question(memory_service):
    with pytest.raises(ValueError):
        run_execute({}, None)
    with pytest.raises(ValueError):
        run_execute({"question": ""}, None)


def test_validation_rejects_unknown_depth(memory_service):
    with pytest.raises(ValueError):
        run_execute({"question": "q", "depth": "extreme"}, None)


def test_response_schema(memory_service, fake_provider):
    registry = ResearchProviderRegistry()
    registry.register_instance("fake", fake_provider)
    svc = ResearchPipelineService(registry=registry, memory=memory_service)

    payload = run_execute(
        {"question": "mcp response", "context": "ctx", "metadata": {"provider": "fake"}},
        svc,
    )

    for key in ("facts", "analysis", "options", "recommendation", "confidence", "sources", "warnings"):
        assert key in payload, f"missing output key: {key}"
    assert payload["facts"] == ["fresh fact for mcp response"]
    assert payload["confidence"] == "high"
    assert isinstance(payload["sources"], list)


def test_response_uses_cache_on_repeat(memory_service, fake_provider):
    registry = ResearchProviderRegistry()
    registry.register_instance("fake", fake_provider)
    svc = ResearchPipelineService(registry=registry, memory=memory_service)

    first = run_execute(
        {"question": "cached again", "context": "c", "metadata": {"provider": "fake"}},
        svc,
    )
    second = run_execute(
        {"question": "cached again", "context": "c", "metadata": {"provider": "fake"}},
        svc,
    )

    assert fake_provider.calls == 1
    assert first["facts"] == second["facts"]