"""Research Pipeline - pipeline service tests (cache flow)."""

import pytest

from features.research_pipeline import (
    ResearchPipelineService,
    ResearchRequest,
)
from features.research_pipeline.registry import ResearchProviderRegistry


def _service_with(memory_service, provider, provider_name="fake"):
    registry = ResearchProviderRegistry()
    registry.register_instance(provider_name, provider)
    return ResearchPipelineService(registry=registry, memory=memory_service)


def _request(question, context="", force_refresh=False, provider="fake"):
    return ResearchRequest(
        question=question,
        context=context,
        depth="standard",
        force_refresh=force_refresh,
        metadata={"provider": provider},
    )


# -- cache hit -------------------------------------------------------


@pytest.mark.asyncio
async def test_cache_hit_does_not_call_provider(memory_service, fake_provider):
    memory_service.save_research(
        "cached question",
        context="",
        payload={"facts": ["cached fact"], "recommendation": "use cache"},
    )
    svc = _service_with(memory_service, fake_provider)

    result = await svc.research(_request("cached question"))

    assert fake_provider.calls == 0
    assert result.source == "research_memory"
    assert result.facts == ["cached fact"]


# -- cache miss ------------------------------------------------------


@pytest.mark.asyncio
async def test_cache_miss_calls_provider(memory_service, fake_provider):
    svc = _service_with(memory_service, fake_provider)

    result = await svc.research(_request("brand new question"))

    assert fake_provider.calls == 1
    assert result.source == "fake"
    assert result.facts == ["fresh fact for brand new question"]


@pytest.mark.asyncio
async def test_cache_miss_persists_result(memory_service, fake_provider):
    svc = _service_with(memory_service, fake_provider)

    await svc.research(_request("persist me"))

    stored = memory_service.find_by_query("persist me")
    assert stored is not None
    assert stored.facts == ["fresh fact for persist me"]
    assert stored.recommendation == "do fresh research"
    assert stored.confidence == "high"


# -- refresh ---------------------------------------------------------


@pytest.mark.asyncio
async def test_force_refresh_ignores_cache(memory_service, fake_provider):
    memory_service.save_research(
        "refresh question",
        payload={"facts": ["stale fact"]},
    )
    svc = _service_with(memory_service, fake_provider)

    result = await svc.research(_request("refresh question", force_refresh=True))

    assert fake_provider.calls == 1
    assert result.source == "fake"
    assert result.facts == ["fresh fact for refresh question"]


@pytest.mark.asyncio
async def test_force_refresh_overwrites_memory(memory_service, fake_provider):
    memory_service.save_research(
        "overwrite question",
        payload={"facts": ["old"], "recommendation": "old"},
    )
    svc = _service_with(memory_service, fake_provider)

    await svc.research(_request("overwrite question", force_refresh=True))

    stored = memory_service.find_by_query("overwrite question")
    assert stored.recommendation == "do fresh research"


# -- provider selection ------------------------------------------------


@pytest.mark.asyncio
async def test_unknown_provider_raises(memory_service, fake_provider):
    svc = _service_with(memory_service, fake_provider, provider_name="other")
    with pytest.raises(ValueError):
        await svc.research(_request("x", provider="does-not-exist"))


def test_request_validation():
    with pytest.raises(ValueError):
        ResearchRequest(question="   ")
    with pytest.raises(ValueError):
        ResearchRequest(question="q", depth="ultra")