"""Research Memory - ResearchMemoryService.

Orchestrates the cache-aside flow WITHOUT knowing anything about Browser
Intelligence (or any other concrete provider): an injected ``ResearchPipeline``
is the only way fresh research is computed. This keeps the memory subsystem
independent, decoupled and future Provider-agnostic.
"""

from __future__ import annotations

from .cache import ResearchMemoryCache
from .config import get_config
from .metrics import get_default_metrics
from .models import (
    RecordStatus,
    ResearchRecord,
    research_hash,
)
from .pipeline import FunctionResearchPipeline, ResearchPipeline, normalize_payload
from .repository import ResearchMemoryRepository


class ResearchMemoryService:

    def __init__(
        self,
        config=None,
        cache: ResearchMemoryCache | None = None,
        metrics=None,
    ) -> None:
        self.config = config or get_config()
        self._metrics = metrics if metrics is not None else get_default_metrics()
        repo = getattr(cache, "repository", None) or ResearchMemoryRepository()
        self._cache = cache if cache is not None else ResearchMemoryCache(repository=repo, metrics=self._metrics)

    # -- cache primitives --------------------------------------------

    def get_cached_research(self, query: str, context: str = "") -> ResearchRecord | None:
        if not query or not query.strip():
            return None
        return self._cache.get(query, context)

    def should_refresh(
        self, query: str, context: str = "", age_budget_seconds: int | None = None
    ) -> bool:
        """Returns True when executing fresh research is warranted.

        age_budget_seconds overrides the record/config TTL check (>0 forces
        refresh when the newest record is older than the budget).
        """
        record = self._cache.get(query, context)  # serves only updateable+fresh
        if record is None:
            return True
        if not self._cache.is_fresh(record, age_budget_seconds):
            return True
        return False

    # -- write / lifecycle -------------------------------------------------

    def save_research(
        self,
        query: str,
        context: str = "",
        payload: dict | None = None,
        domain: str = "",
        ttl: int | None = None,
        status: str = "new",
    ) -> ResearchRecord:
        payload = normalize_payload(payload or {})
        record = self._cache.put(
            payload=payload,
            query=query,
            context=context,
            domain=domain,
            ttl=ttl,
            status=status,
        )
        if self._metrics is not None:
            self._metrics.record_stored()
        return record

    def promote_candidate(self, record_id: str) -> ResearchRecord | None:
        """Change status NEW/REVIEWED -> ACCEPTED (v1 promotion flow)."""
        record = self._cache.repository.get(record_id)
        if record is None:
            return None
        if record.status not in ("new", "reviewed"):
            return record
        updated = self._cache.mark_status(record_id, RecordStatus.ACCEPTED)
        if self._metrics is not None:
            self._metrics.record_promotion()
        return updated

    def invalidate(self, record_id: str) -> ResearchRecord | None:
        """Mark a record OBSOLETE (soft-delete; nothing is destroyed)."""
        updated = self._cache.mark_status(record_id, RecordStatus.OBSOLETE)
        if updated is not None and self._metrics is not None:
            self._metrics.record_invalidation()
        return updated

    def archive(self, record_id: str) -> ResearchRecord | None:
        """Move a record to ARCHIVED (kept for history, not served as cache)."""
        return self._cache.mark_status(record_id, RecordStatus.ARCHIVED)

    def forget(self, record_id: str) -> bool:
        """Hard-delete a record."""
        return self._cache.repository.delete(record_id)

    # -- lookup -------------------------------------------------------

    def find_by_id(self, record_id: str) -> ResearchRecord | None:
        return self._cache.repository.get(record_id)

    def find_by_query(self, query: str, context: str = "") -> ResearchRecord | None:
        return self._cache.repository.find_by_hash(research_hash(query, context))

    def list_recent(self, limit: int = 20) -> list[ResearchRecord]:
        return self._cache.repository.list_recent(limit)

    def search_records(
        self,
        keyword: str | None = None,
        domain: str | None = None,
        status: str | None = None,
        limit: int = 20,
    ) -> list[ResearchRecord]:
        return self._cache.repository.find(keyword, domain, status, limit)

    # -- pipeline-driven execution (the integration seam) ---------------

    def execute(
        self,
        query: str,
        pipeline: ResearchPipeline,
        context: str = "",
        domain: str = "",
        force_refresh: bool = False,
        ttl: int | None = None,
        **opts,
    ) -> ResearchRecord:
        """Cache-aside: return fresh memory or compute via the pipeline + store.

        This is the ONLY place Research Memory talks to an external research
        pipeline, always through the abstract contract - never by importing a
        concrete provider.
        """
        if not force_refresh:
            cached = self.get_cached_research(query, context)
            if cached is not None:
                return cached

        if not hasattr(pipeline, "research"):
            pipeline = FunctionResearchPipeline(pipeline)
        payload = pipeline.research(query, context=context, **opts)
        record = self.save_research(
            query, context=context, payload=payload, domain=domain, ttl=ttl
        )
        if self._metrics is not None:
            self._metrics.record_refresh()
        return record

    # -- metrics snapshot --------------------------------------------------

    def mreil_snapshot(self) -> dict:
        return self._metrics.to_dict()