"""Research Pipeline - browser_intelligence adapter tests."""

import pytest

from features.research_pipeline.adapters.browser_intelligence import (
    BrowserIntelligenceAdapter,
)
from features.research_pipeline.interfaces import ResearchProviderError
from features.research_pipeline.models import ResearchRequest


def _request(question="what is browser-use?", context="python", depth="deep"):
    return ResearchRequest(question=question, context=context, depth=depth)


# -- request mapping ---------------------------------------------------


@pytest.mark.asyncio
async def test_request_reaches_backend_and_maps_to_result():
    received = []

    async def backend(request):
        received.append(request)
        return {"facts": ["x"], "analysis": "y"}

    adapter = BrowserIntelligenceAdapter(research_fn=backend)
    result = await adapter.research(_request())

    assert received, "backend must be invoked"
    assert received[0].question == "what is browser-use?"
    assert received[0].context == "python"
    assert result.source == "browser_intelligence"


@pytest.mark.asyncio
async def test_sync_backend_is_supported():
    def backend(request):
        return {"FACTS": ["sync-fact"], "ANALYSIS": "sync-analysis"}

    adapter = BrowserIntelligenceAdapter(research_fn=backend)
    result = await adapter.research(_request())
    assert result.facts == ["sync-fact"]


# -- result mapping ----------------------------------------------------


@pytest.mark.asyncio
async def test_uppercase_result_keys_are_normalized():
    async def backend(request):
        return {
            "FACTS": ["a", "b"],
            "ANALYSIS": "the analysis",
            "OPTIONS": ["opt-1"],
            "RECOMMENDATION": "rec-1",
            "CONFIDENCE": "High",
            "SOURCES": [
                {"url": "https://a.example", "title": "A"},
                {"url": "https://b.example", "title": "B"},
            ],
            "WARNINGS": ["warn"],
        }

    adapter = BrowserIntelligenceAdapter(research_fn=backend)
    result = await adapter.research(_request())

    assert result.facts == ["a", "b"]
    assert result.analysis == "the analysis"
    assert result.options == ["opt-1"]
    assert result.recommendation == "rec-1"
    assert result.confidence == "high"
    assert len(result.sources) == 2
    assert result.sources[0]["url"] == "https://a.example"
    assert result.warnings == ["warn"]


@pytest.mark.asyncio
async def test_object_result_is_normalized():
    class Findings:
        def to_dict(self):
            return {"facts": ["obj"], "confidence": "Medium", "sources": []}

    async def backend(request):
        return Findings()

    adapter = BrowserIntelligenceAdapter(research_fn=backend)
    result = await adapter.research(_request())
    assert result.facts == ["obj"]
    assert result.confidence == "medium"


# -- error handling ----------------------------------------------------


@pytest.mark.asyncio
async def test_backend_error_becomes_provider_error():
    async def backend(request):
        raise RuntimeError("boom")

    adapter = BrowserIntelligenceAdapter(research_fn=backend)
    with pytest.raises(ResearchProviderError) as exc_info:
        await adapter.research(_request())
    assert "browser_intelligence" in str(exc_info.value)


@pytest.mark.asyncio
async def test_empty_result_raises_provider_error():
    async def backend(request):
        return None

    adapter = BrowserIntelligenceAdapter(research_fn=backend)
    with pytest.raises(ResearchProviderError):
        await adapter.research(_request())