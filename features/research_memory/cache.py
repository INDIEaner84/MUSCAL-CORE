"""Research Memory - retrieval cache (v1: deterministic hash, no embeddings).

The cache is the only place that decides "is a stored record fresh enough to
serve". It cooperates with the MREIL metrics registry but stays decoupled from
any concrete research provider.
"""

from __future__ import annotations

import time

from .config import get_config
from .models import (
    RecordStatus,
    ResearchRecord,
    now_iso,
    research_hash,
)
from .repository import ResearchMemoryRepository

_UPDATEABLE_STATUSES = {"new", "reviewed", "accepted"}


class ResearchMemoryCache:

    def __init__(
        self,
        repository: ResearchMemoryRepository | None = None,
        metrics=None,
    ) -> None:
        self._repo = repository if repository is not None else ResearchMemoryRepository()
        self._metrics = metrics  # optional MREIL tracker (injected by the service)

    @property
    def repository(self) -> ResearchMemoryRepository:
        return self._repo

    # -- public API ------------------------------------------------------

    def get(self, query: str, context: str = "", _ttl_override: int | None = None) -> ResearchRecord | None:
        hsh = research_hash(query, context)
        started = time.monotonic()
        record = self._repo.find_by_hash(hsh)
        elapsed_ms = (time.monotonic() - started) * 1000.0

        if record is None or record.status not in _UPDATEABLE_STATUSES:
            self._notify_miss(elapsed_ms)
            return None
        if not self._is_fresh(record, _ttl_override):
            self._notify_miss(elapsed_ms)
            return None

        self._notify_hit(elapsed_ms)
        return record

    def put(
        self,
        payload: dict,
        query: str,
        context: str = "",
        domain: str = "",
        ttl: int | None = None,
        status: str = "new",
    ) -> ResearchRecord:
        """Store a fresh payload under the deterministic key for (query, context).

        If a record with the same hash already exists it is updated in place
        (same id) instead of appending a second row - a question maps to one
        living record.
        """
        hsh = research_hash(query, context)
        existing = self._repo.find_by_hash(hsh)
        record = ResearchRecord(
            id=existing.id if existing else "",
            created_at=existing.created_at if existing else "",
            query=query,
            context=context,
            domain=domain,
            facts=list(payload.get("facts", []) or []),
            options=list(payload.get("options", []) or []),
            analysis=payload.get("analysis", "") or "",
            recommendation=payload.get("recommendation", "") or "",
            confidence=str(payload.get("confidence", "low")),
            status=status,
            hash=hsh,
            ttl=ttl,
        )
        sources = payload.get("sources", []) or []
        from .models import Source

        record.sources = [
            s if isinstance(s, Source) else Source.from_dict(s) for s in sources
        ]
        self._repo.save(record)
        return record

    def mark_status(
        self, record_id: str, status: RecordStatus
    ) -> ResearchRecord | None:
        return self._repo.update_status(record_id, status)

    # -- freshness -------------------------------------------------------

    def is_fresh(self, record: ResearchRecord, ttl_override: int | None = None) -> bool:
        return self._is_fresh(record, ttl_override)

    def _is_fresh(self, record: ResearchRecord, ttl_override: int | None) -> bool:
        ttl = ttl_override if ttl_override is not None else (record.ttl if record.ttl is not None else get_config().ttl_seconds)
        if ttl is None:
            return True
        return record.age_seconds <= ttl

    # -- metrics ---------------------------------------------------------

    def _notify_hit(self, elapsed_ms: float) -> None:
        if self._metrics is not None:
            self._metrics.record_cache_hit(elapsed_ms)

    def _notify_miss(self, elapsed_ms: float) -> None:
        if self._metrics is not None:
            self._metrics.record_cache_miss(elapsed_ms)