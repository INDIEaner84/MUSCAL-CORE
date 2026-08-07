"""Research Memory - MREIL metric placeholders.

MREIL = Memory Retrieval Evaluation & Intelligence Level.

These are PLACEHOLDER metrics for the future Knowledge Foundation integration.
Today the tracker only records cache/server counters (hits, misses, refreshes,
latency); the semantic layers (relevance scoring, deduplication gain, retrieval
latency across the Knowledge Foundation) are stubbed here and documented in
``docs/engineering/D-MC-RM-001-research-memory.md``.

Import-safe: stdlib only, no heavy dependencies, no Core imports.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class MREILMetrics:
    """In-memory counters + placeholders backing MREIL (v1)."""

    total_queries: int = 0
    cache_hits: int = 0
    cache_misses: int = 0
    refreshes: int = 0
    promotions: int = 0
    invalidations: int = 0
    exports: int = 0
    items_stored: int = 0

    # Latency placeholders (ms); populated by the service/cache layer.
    total_lookup_ms: float = 0.0
    lookup_count: int = 0

    # Knowledge Foundation placeholders (future).
    retrieval_relevance: float = 0.0
    dedup_ratio: float = 0.0

    def record_cache_hit(self, lookup_ms: float = 0.0) -> None:
        self.cache_hits += 1
        self.total_queries += 1
        self._record_lookup(lookup_ms)

    def record_cache_miss(self, lookup_ms: float = 0.0) -> None:
        self.cache_misses += 1
        self.total_queries += 1
        self._record_lookup(lookup_ms)

    def _record_lookup(self, lookup_ms: float) -> None:
        self.total_lookup_ms += lookup_ms
        self.lookup_count += 1

    def record_refresh(self) -> None:
        self.refreshes += 1

    def record_promotion(self) -> None:
        self.promotions += 1

    def record_invalidation(self) -> None:
        self.invalidations += 1

    def record_export(self) -> None:
        self.exports += 1

    def record_stored(self, n: int = 1) -> None:
        self.items_stored += n

    @property
    def hit_rate(self) -> float:
        total = self.cache_hits + self.cache_misses
        if total == 0:
            return 0.0
        return round(self.cache_hits / total, 4)

    @property
    def avg_lookup_ms(self) -> float:
        if self.lookup_count == 0:
            return 0.0
        return round(self.total_lookup_ms / self.lookup_count, 2)

    def to_dict(self) -> dict:
        """Serializable MREIL snapshot (the placeholder contract)."""
        return {
            "mreil": "Memory Retrieval Evaluation & Relevance Index",
            "version": "v1-placeholders",
            "total_queries": self.total_queries,
            "cache_hits": self.cache_hits,
            "cache_misses": self.cache_misses,
            "hit_rate": self.hit_rate,
            "refreshes": self.refreshes,
            "promotions": self.promotions,
            "invalidations": self.invalidations,
            "exports": self.exports,
            "items_stored": self.items_stored,
            "avg_lookup_ms": self.avg_lookup_ms,
            "total_lookup_ms": round(self.total_lookup_ms, 2),
            "knowledge_foundation": {
                "retrieval_relevance": self.retrieval_relevance,
                "dedup_ratio": self.dedup_ratio,
                "status": "placeholder",
            },
        }


_default_metrics: MREILMetrics | None = None


def get_default_metrics() -> MREILMetrics:
    global _default_metrics
    if _default_metrics is None:
        _default_metrics = MREILMetrics()
    return _default_metrics