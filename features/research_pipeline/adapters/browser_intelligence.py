"""Research Pipeline - Browser Intelligence adapter.

Translates a ResearchRequest into the existing Browser Intelligence
``ResearchService`` API, invokes it, and normalizes the result to
``ResearchResult``.

This adapter contains NO browser logic: browser-use / Chromium / Ollama wiring
stays in ``features/browser_intelligence``. Purpose of the extra seam is to
keep the pipeline layer decoupled from any concrete provider implementation.
"""

from __future__ import annotations

import asyncio
import inspect

from ..interfaces import ResearchProvider, ResearchProviderError
from ..models import ResearchRequest, ResearchResult, resolve_constraints


class BrowserIntelligenceAdapter(ResearchProvider):
    name = "browser_intelligence"

    def __init__(
        self,
        research_fn=None,
        provider_name: str = "browser_intelligence",
    ) -> None:
        """``research_fn`` is injectable for tests; defaults to the live service."""
        self._research_fn = research_fn
        self._provider_label = provider_name

    # -- interface -------------------------------------------------------

    async def research(self, request: ResearchRequest) -> ResearchResult:
        try:
            if self._research_fn is None:
                raw = await self._default_research_async(request)
            else:
                fn = self._research_fn
                if inspect.iscoroutinefunction(fn):
                    raw = await fn(request)
                else:
                    raw = await asyncio.to_thread(fn, request)
            return self._normalize(request, raw)
        except ResearchProviderError:
            raise
        except Exception as exc:  # pragma: no cover - defensive boundary
            raise ResearchProviderError(
                f"{self.name} failed: {type(exc).__name__}: {exc}"
            ) from exc

    # -- translation -----------------------------------------------------

    @staticmethod
    def _constraints_for(request: ResearchRequest) -> list:
        constraints = resolve_constraints(request.depth)
        extra = request.metadata.get("constraints", []) or []
        return list(dict.fromkeys(constraints + list(extra)))

    async def _default_research_async(self, request: ResearchRequest) -> dict:
        from features.browser_intelligence import ResearchService

        findings = await ResearchService().research_async(
            request.question,
            topic=request.context,
            constraints=self._constraints_for(request),
        )
        return findings.to_dict() if hasattr(findings, "to_dict") else findings

    # -- normalization ---------------------------------------------------

    def _normalize(self, request: ResearchRequest, raw) -> ResearchResult:
        """Normalize provider output (dict or object) into ResearchResult."""
        if raw is None:
            raise ResearchProviderError(f"{self.name} returned no data")
        payload = raw.to_dict() if hasattr(raw, "to_dict") else (raw if isinstance(raw, dict) else {})
        return ResearchResult(
            source=self._provider_label,
            facts=list(payload.get("facts") or payload.get("FACTS") or []),
            analysis=str(payload.get("analysis") or payload.get("ANALYSIS") or ""),
            options=list(payload.get("options") or payload.get("OPTIONS") or []),
            recommendation=str(payload.get("recommendation") or payload.get("RECOMMENDATION") or ""),
            confidence=str(payload.get("confidence") or payload.get("CONFIDENCE") or "low").lower(),
            sources=self._normalize_sources(payload.get("sources") or payload.get("SOURCES") or []),
            warnings=list(payload.get("warnings") or payload.get("WARNINGS") or []),
        )

    @staticmethod
    def _normalize_sources(raw_sources) -> list:
        out = []
        for item in raw_sources or []:
            if isinstance(item, dict):
                out.append(item)
            elif hasattr(item, "to_dict"):
                out.append(item.to_dict())
            else:  # pragma: no cover - unexpected source type
                out.append({"url": str(item)})
        return out