"""Browser Intelligence - MCP server tests.

Covers:
- MCP tool registration and schema
- request/response validation
- ResearchService integration (with an injected fake and via the real class)
- MCP gateway registration compatibility

Import-safe: the MUSCAL plugin loader imports every .py under features/, so this
file must not raise at module level on a system python without the venv deps.
"""

try:
    import pytest
except ImportError:  # pragma: no cover - plugin loader runs without pytest
    pytest = None

try:
    import mcp  # noqa: F401

    HAS_MCP = True
except Exception:
    HAS_MCP = False

try:
    import mcp.server.fastmcp  # noqa: F401

    HAS_FASTMCP = True
except Exception:
    HAS_FASTMCP = False

if pytest is not None:
    pytestmark = pytest.mark.skipif(
        not (HAS_MCP and HAS_FASTMCP), reason="mcp SDK not installed"
    )

from features.browser_intelligence import ResearchFindings, Source  # noqa: E402
from features.browser_intelligence.mcp_server import (  # noqa: E402
    TOOL_ID,
    TOOL_NAME,
    build_constraints,
    create_server,
    findings_to_payload,
    register_with_gateway,
    run_research,
)


def _canned_findings():
    return ResearchFindings(
        question="test question",
        facts=["fact one", "fact two"],
        analysis="Engineering interpretation.",
        options=["option a"],
        recommendation="recommended action",
        confidence="High",
        warnings=["looks like captcha"],
        sources=[Source(url="https://example.com", title="Example")],
    )


class _FakeService:
    """Records the arguments ResearchService would receive."""

    def __init__(self):
        self.calls = []
        self.findings = _canned_findings()

    def research(self, question, topic="", constraints=None):
        self.calls.append((question, topic, constraints))
        return self.findings


def test_tool_registration_and_schema():
    import asyncio

    async def _check():
        server = create_server()
        tools = [t for t in await server.list_tools() if t.name == TOOL_NAME]
        assert len(tools) == 1
        schema = tools[0].inputSchema
        assert schema["required"] == ["question"]
        props = schema.get("properties", {})
        assert "question" in props
        assert "context" in props
        assert "depth" in props
        return tools[0]

    tool = asyncio.run(_check())
    assert tool.name == TOOL_ID
    assert TOOL_ID == "browser_intelligence.research"


def test_run_research_requires_question():
    import pytest as _pytest

    with _pytest.raises(ValueError):
        run_research({})
    with _pytest.raises(ValueError):
        run_research({"question": "   "})


def test_run_research_validates_depth():
    import pytest as _pytest

    with _pytest.raises(ValueError):
        run_research({"question": "x", "depth": "ultra"})


def test_run_research_maps_inputs_to_service():
    service = _FakeService()
    result = run_research(
        {"question": "How does MCP stdio work?", "context": "OpenCode", "depth": "deep"},
        service=service,
    )

    assert service.calls, "expected the service to be invoked"
    question, topic, constraints = service.calls[0]
    assert question == "How does MCP stdio work?"
    assert topic == "OpenCode"
    assert len(constraints) > 0

    for key in ("facts", "analysis", "options", "recommendation", "confidence", "warnings"):
        assert key in result, f"missing output key: {key}"
    assert result["facts"]
    assert result["confidence"] in ("low", "medium", "high", "Low", "Medium", "High")
    assert "sources" in result


def test_build_constraints_by_depth():
    assert build_constraints("standard") == []
    assert build_constraints("quick") and build_constraints("deep")


def test_run_research_uses_real_researchservice():
    from unittest import mock

    findings = _canned_findings()
    with mock.patch(
        "features.browser_intelligence.research_service.ResearchService.research",
        return_value=findings,
    ) as patched:
        result = run_research({"question": "q?", "depth": "standard"})

    patched.assert_called_once()
    args, kwargs = patched.call_args
    assert args[0] == "q?"
    assert kwargs.get("topic", "") == ""
    for key in ("facts", "analysis", "options", "recommendation", "confidence", "warnings"):
        assert key in result


def test_findings_to_payload_shape():
    payload = findings_to_payload(_canned_findings())
    assert set(
        ("facts", "analysis", "options", "recommendation", "confidence", "warnings")
    ) <= set(payload.keys())
    assert payload["facts"][0] == "fact one"
    assert payload["warnings"] == ["looks like captcha"]
    assert payload["confidence"] == "High"


def test_gateway_registration_compatible():
    result = register_with_gateway()
    assert isinstance(result, dict)
    assert "registered" in result