"""Browser Intelligence - minimal end-to-end test.

Runs a real research question through Browser-Use and asserts the structured
output contract. Requires the project venv (browser-use) and network access.

Run:
    .venv/bin/python -m pytest features/browser_intelligence/tests/ -v

Import-safe: the MUSCAL plugin loader imports every .py under features/, so
this file must not raise at module level when running on the system python.
"""

try:
    import pytest
except ImportError:  # pragma: no cover - plugin loader runs without pytest
    pytest = None

try:
    import browser_use  # noqa: F401

    HAS_BROWSER_USE = True
except Exception:
    HAS_BROWSER_USE = False

if pytest is not None:
    pytestmark = pytest.mark.skipif(
        not HAS_BROWSER_USE, reason="browser-use not installed"
    )

from features.browser_intelligence import ResearchService  # noqa: E402

QUESTION = "What are the installation requirements of the browser-use library?"


def test_research_returns_structured_findings():
    if pytest is None or not HAS_BROWSER_USE:
        return
    findings = ResearchService().research(QUESTION)

    assert findings.question
    assert findings.facts, "expected at least one fact"
    assert not findings.empty

    data = findings.to_dict()
    for key in ("FACTS", "ANALYSIS", "OPTIONS", "RECOMMENDATION", "CONFIDENCE"):
        assert key in data, f"missing output section: {key}"

    assert data["CONFIDENCE"] in ("Low", "Medium", "High")
    assert findings.to_markdown().startswith("FACTS:")


def test_registration_does_not_crash():
    from features.browser_intelligence.mcp_registration import register_research_tool

    result = register_research_tool()
    assert isinstance(result, dict)
    assert "registered" in result