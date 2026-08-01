from __future__ import annotations

from typing import Any, Optional

from .models import MemoryEntry, UnifiedMemoryContext
from .classifier import MemoryClassifier
from .retriever import MemoryRetriever
from .consolidator import MemoryConsolidator
from .importance import ImportanceEngine
from .metrics import MemoryReuseScore, MemoryImpactScore, KnowledgeTransferScore


class MemoryFabric:

    def __init__(self, classifier: Optional[MemoryClassifier] = None,
                 retriever: Optional[MemoryRetriever] = None,
                 consolidator: Optional[MemoryConsolidator] = None,
                 importance: Optional[ImportanceEngine] = None,
                 reuse_metrics: Optional[MemoryReuseScore] = None,
                 impact_metrics: Optional[MemoryImpactScore] = None,
                 transfer_metrics: Optional[KnowledgeTransferScore] = None,
                 store_provider: Optional[Any] = None,
                 event_emitter: Optional[Any] = None):
        self._classifier = classifier or MemoryClassifier()
        self._retriever = retriever or MemoryRetriever()
        self._importance = importance or ImportanceEngine()
        self._consolidator = consolidator or MemoryConsolidator(
            classifier=self._classifier, importance=self._importance,
        )
        self._reuse_metrics = reuse_metrics or MemoryReuseScore()
        self._impact_metrics = impact_metrics or MemoryImpactScore()
        self._transfer_metrics = transfer_metrics or KnowledgeTransferScore()
        self._store = store_provider
        self._events = event_emitter
        if self._store is not None:
            self._retriever.register_store_provider(self._store)

    def classify(self, source: str, content: dict, *,
                 memory_type_hint: Optional[str] = None) -> list[MemoryEntry]:
        entries = self._classifier.classify(source, content, memory_type_hint=memory_type_hint)
        for entry in entries:
            self._emit("memory.classified", entry)
        return entries

    def classify_event(self, event: dict) -> list[MemoryEntry]:
        entries = self._classifier.classify_event(event)
        for entry in entries:
            self._emit("memory.classified", entry)
        return entries

    def retrieve_context(self, task: Optional[dict] = None,
                         intent: Optional[dict] = None,
                         goal: Optional[dict] = None,
                         domain: Optional[str] = None,
                         constraints: Optional[list[str]] = None,
                         execution_id: str = "",
                         top_k: int = 5) -> UnifiedMemoryContext:
        ctx = self._retriever.retrieve_context(
            task=task, intent=intent, goal=goal,
            domain=domain, constraints=constraints,
            execution_id=execution_id, top_k=top_k,
        )
        self._emit("memory.retrieved", ctx)
        return ctx

    def consolidate(self, raw_source: str, raw_content: dict) -> list[MemoryEntry]:
        return self._consolidator.consolidate(
            raw_source, raw_content,
            store_provider=self._store,
            event_emitter=self._events,
        )

    def promote(self, entry: MemoryEntry) -> Optional[MemoryEntry]:
        return self._consolidator.promote(
            entry,
            store_provider=self._store,
            event_emitter=self._events,
        )

    def score_importance(self, entry: MemoryEntry, *,
                          all_entries: Optional[list[MemoryEntry]] = None) -> Any:
        return self._importance.score(entry, all_entries=all_entries)

    def persist(self, entry: MemoryEntry) -> str:
        if self._store is not None and hasattr(self._store, "save"):
            self._emit("memory.created", entry)
            return self._store.save(entry)
        raise RuntimeError("No store provider configured for persistence")

    def validate_memory(self, entry: MemoryEntry) -> tuple[Optional[MemoryEntry], list[str]]:
        return self._consolidator.validate_memory(
            entry, store_provider=self._store, event_emitter=self._events,
        )

    def archive_memory(self, entry: MemoryEntry) -> Optional[MemoryEntry]:
        return self._consolidator.archive_memory(
            entry, store_provider=self._store, event_emitter=self._events,
        )

    def compute_reuse_score(self, entry: MemoryEntry,
                             retrieval_history: Optional[list[dict]] = None) -> dict:
        return self._reuse_metrics.to_dict(entry, retrieval_history)

    def compute_impact_score(self, entry: MemoryEntry,
                              outcome: Optional[str] = None) -> dict:
        return self._impact_metrics.to_dict(entry, outcome)

    def compute_transfer_score(self, entry: MemoryEntry,
                                source_domain: str = "",
                                target_domain: str = "") -> dict:
        return self._transfer_metrics.to_dict(entry, source_domain, target_domain)

    @property
    def retriever(self) -> MemoryRetriever:
        return self._retriever

    @property
    def classifier(self) -> MemoryClassifier:
        return self._classifier

    @property
    def reuse_metrics(self) -> MemoryReuseScore:
        return self._reuse_metrics

    @property
    def impact_metrics(self) -> MemoryImpactScore:
        return self._impact_metrics

    @property
    def transfer_metrics(self) -> KnowledgeTransferScore:
        return self._transfer_metrics

    def _emit(self, topic: str, data: Any) -> None:
        if self._events is not None and hasattr(self._events, 'emit'):
            payload = data.to_dict() if hasattr(data, 'to_dict') else data
            self._events.emit(
                topic, payload,
                correlation_id=getattr(data, 'id', '') if hasattr(data, 'id') else '',
            )
