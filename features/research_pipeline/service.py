"""Research Pipeline - orchestration service.

The approved flow:

    1. Receive ResearchRequest
    2. If not force_refresh: check Research Memory
    3. If a valid cached result exists: return it          (source="research_memory")
    4. Otherwise: select provider (registry)
    5. Execute provider (adapter normalizes output)
    6. Persist result into Research Memory
    7. Return ResearchResult

The service stays provider-agnostic: no provider is imported here; providers
come from the registry (see interfaces.py / registry.py).
"""

from __future__ import annotations

from .config import get_config
from .interfaces import ResearchProvider
from .models import ResearchRequest, ResearchResult
from .registry import get_default_registry


def _build_default_memory():
    """Lazily build Research Memory (import happens at first use, not import)."""
    from features.research_memory import ResearchMemoryService

    return ResearchMemoryService()


class ResearchPipelineService:

    def __init__(self, registry=None, memory=None, config=None) -> None:
        self._registry = registry if registry is not None else get_default_registry()
        self._memory = memory
        self._config = config if config is not None else get_config()
        self._owns_memory = memory is None

    @property
    def memory(self):
        if self._memory is None:
            self._memory = _build_default_memory()
        return self._memory

    # -- main entry ------------------------------------------------------

    async def research(self, request: ResearchRequest) -> ResearchResult:
        if not request.force_refresh:
            cached = self.memory.get_cached_research(request.question, request.context)
            if cached is not None:
                return self._record_to_result(cached)

        provider = self._select_provider(request)
        result = await provider.research(request)
        self._persist(request, result)
        return result

    # -- helpers ---------------------------------------------------------

    def _select_provider(self, request: ResearchRequest) -> ResearchProvider:
        name = request.metadata.get("provider") or self._config.default_provider
        return self._registry.get(name)

    def _persist(self, request: ResearchRequest, result: ResearchResult) -> None:
        self.memory.save_research(
            request.question,
            context=request.context,
            payload={
                "facts": result.facts,
                "analysis": result.analysis,
                "options": result.options,
                "recommendation": result.recommendation,
                "confidence": result.confidence.lower(),
                "sources": result.sources,
            },
            domain=request.metadata.get("domain") or "",
        )

    @staticmethod
    def _record_to_result(record) -> ResearchResult:
        """Rebuild a ResearchResult from a cached memory ResearchRecord."""
        return ResearchResult(
            source="research_memory",
            facts=list(record.facts),
            analysis=getattr(record, "analysis", ""),
            options=list(record.options),
            recommendation=getattr(record, "recommendation", ""),
            confidence=str(getattr(record, "confidence", "low")).lower(),
            sources=[s.to_dict() if hasattr(s, "to_dict") else s for s in (record.sources or [])],
            warnings=[],
            timestamp=record.updated_at,
        )