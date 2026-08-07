"""Shared fixtures for research_pipeline tests."""

import pytest

from features.research_memory import (
    ResearchMemoryCache,
    ResearchMemoryRepository,
    ResearchMemoryService,
)
from features.research_memory.storage import ResearchMemoryStore
from features.research_pipeline.models import ResearchResult


@pytest.fixture
def memory_service(tmp_path):
    store = ResearchMemoryStore(str(tmp_path / "pipeline.db"))
    repo = ResearchMemoryRepository(store)
    cache = ResearchMemoryCache(repository=repo)
    return ResearchMemoryService(cache=cache)


@pytest.fixture
def fake_provider():
    class FakeProvider:
        name = "fake"

        def __init__(self):
            self.calls = 0

        async def research(self, request):
            self.calls += 1
            return ResearchResult(
                source=self.name,
                facts=[f"fresh fact for {request.question}"],
                analysis="fresh analysis",
                options=["option-a"],
                recommendation="do fresh research",
                confidence="high",
                sources=[{"url": "https://example.com", "title": "Example"}],
                warnings=[],
            )

    return FakeProvider()