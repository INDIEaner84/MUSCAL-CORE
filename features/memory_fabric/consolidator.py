from __future__ import annotations

from typing import Any, Optional

from .models import MemoryEntry, MemoryType
from .classifier import MemoryClassifier
from .importance import ImportanceEngine


class MemoryConsolidator:

    def __init__(self, classifier: Optional[MemoryClassifier] = None,
                 importance: Optional[ImportanceEngine] = None):
        self._classifier = classifier or MemoryClassifier()
        self._importance = importance or ImportanceEngine()

    def validate_entry(self, entry: MemoryEntry) -> tuple[bool, list[str]]:
        reasons = []
        if not entry.id:
            reasons.append("Missing id")
        if not entry.content:
            reasons.append("Missing content")
        if not entry.source:
            reasons.append("Missing source")
        if entry.confidence < 0.0 or entry.confidence > 1.0:
            reasons.append(f"Confidence out of range: {entry.confidence}")
        if entry.importance and (entry.importance.total < 0.0 or entry.importance.total > 1.0):
            reasons.append(f"Importance total out of range: {entry.importance.total}")
        return len(reasons) == 0, reasons

    def consolidate(self, raw_source: str, raw_content: dict, *,
                    store_provider: Optional[Any] = None,
                    event_emitter: Optional[Any] = None) -> list[MemoryEntry]:
        step = "classification"
        try:
            entries = self._classifier.classify(raw_source, raw_content)
            step = "validation"
            validated = []
            for entry in entries:
                is_valid, reasons = self.validate_entry(entry)
                if not is_valid:
                    entry.provenance["validation_errors"] = reasons
                validated.append(entry)
            step = "importance"
            for entry in validated:
                importance = self._importance.score(entry, all_entries=[])
                entry.importance = importance
            step = "storage"
            stored = []
            for entry in validated:
                if store_provider is not None and hasattr(store_provider, 'save_entry'):
                    store_provider.save_entry(entry)
                stored.append(entry)
                self._emit(event_emitter, "memory.consolidated", entry)
            return stored
        except Exception as exc:
            self._emit(event_emitter, "memory.consolidated",
                       {"error": str(exc), "step": step, "source": raw_source})
            raise

    def promote(self, entry: MemoryEntry, *,
                store_provider: Optional[Any] = None,
                event_emitter: Optional[Any] = None) -> Optional[MemoryEntry]:
        if entry.importance and entry.importance.total >= 0.7:
            entry.confidence = min(1.0, entry.confidence + 0.1)
            trans_ok, reason = entry.transition_lifecycle("PROMOTED")
            if trans_ok:
                entry.provenance["promotion_reason"] = reason
            if store_provider is not None and hasattr(store_provider, 'save_entry'):
                store_provider.save_entry(entry)
            self._emit(event_emitter, "memory.promoted", entry)
            return entry
        return None

    def promote_memory(self, entry: MemoryEntry, *,
                       store_provider: Optional[Any] = None,
                       event_emitter: Optional[Any] = None) -> Optional[MemoryEntry]:
        return self.promote(entry, store_provider=store_provider,
                            event_emitter=event_emitter)

    def archive_memory(self, entry: MemoryEntry, *,
                       store_provider: Optional[Any] = None,
                       event_emitter: Optional[Any] = None) -> Optional[MemoryEntry]:
        trans_ok, reason = entry.transition_lifecycle("ARCHIVED")
        if not trans_ok:
            return None
        entry.provenance["archive_reason"] = reason
        if store_provider is not None and hasattr(store_provider, 'save_entry'):
            store_provider.save_entry(entry)
        self._emit(event_emitter, "memory.lifecycle.changed", entry)
        return entry

    def validate_memory(self, entry: MemoryEntry, *,
                        store_provider: Optional[Any] = None,
                        event_emitter: Optional[Any] = None) -> tuple[Optional[MemoryEntry], list[str]]:
        is_valid, reasons = self.validate_entry(entry)
        if is_valid:
            if entry.lifecycle_state == "CLASSIFIED":
                trans_ok, _ = entry.transition_lifecycle("VALIDATED")
                if trans_ok:
                    entry.provenance["validation_timestamp"] = (
                        __import__("datetime").datetime.now(
                            __import__("datetime").timezone.utc
                        ).isoformat()
                    )
            if store_provider is not None and hasattr(store_provider, 'save_entry'):
                store_provider.save_entry(entry)
            self._emit(event_emitter, "memory.validation.completed", entry)
            return entry, []
        self._emit(event_emitter, "memory.validation.started",
                   {"entry_id": entry.id, "reasons": reasons})
        return None, reasons

    def _emit(self, emitter: Optional[Any], topic: str, data: Any) -> None:
        if emitter is not None and hasattr(emitter, 'emit'):
            payload = data.to_dict() if hasattr(data, 'to_dict') else data
            emitter.emit(topic, payload, correlation_id=getattr(data, 'id', ''))
