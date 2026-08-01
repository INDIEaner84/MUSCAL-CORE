from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, Optional

from .models import KnowledgeCandidate, KnowledgeEntry, KnowledgeState, KNOWLEDGE_EVENTS


class KnowledgeWriter:

    def __init__(self, memory_adapter: Optional[Any] = None,
                 event_emitter: Optional[Any] = None):
        self._memory = memory_adapter
        self._events = event_emitter
        self._store: dict[str, Any] = {}

    def write_candidate(self, candidate: KnowledgeCandidate) -> Optional[str]:
        if candidate.state != KnowledgeState.CANDIDATE:
            candidate.state = KnowledgeState.CANDIDATE
        data = candidate.to_dict()
        storage_key = f"knowledge:candidate:{candidate.id}"
        self._store[storage_key] = data
        if self._memory is not None:
            self._memory.save(storage_key, data)
        self._emit_event("knowledge.candidate.created", candidate)
        return candidate.id

    def write_validated(self, candidate: KnowledgeCandidate) -> Optional[str]:
        candidate.state = KnowledgeState.VALIDATED
        data = candidate.to_dict()
        entry = KnowledgeEntry(
            knowledge_id=str(uuid.uuid4()),
            candidate_id=candidate.id,
            entry=data,
        )
        storage_key = f"knowledge:entry:{entry.knowledge_id}"
        self._store[storage_key] = entry.to_dict()
        if self._memory is not None:
            self._memory.save(storage_key, entry.to_dict())
        self._emit_event("knowledge.candidate.validated", candidate)
        return entry.knowledge_id

    def write_rejected(self, candidate: KnowledgeCandidate) -> Optional[str]:
        candidate.state = KnowledgeState.REJECTED
        data = candidate.to_dict()
        storage_key = f"knowledge:candidate:{candidate.id}"
        self._store[storage_key] = data
        if self._memory is not None:
            self._memory.save(storage_key, data)
        self._emit_event("knowledge.candidate.rejected", candidate)
        return candidate.id

    def get_entry(self, knowledge_id: str) -> Optional[dict]:
        storage_key = f"knowledge:entry:{knowledge_id}"
        entry = self._store.get(storage_key)
        if entry is None and self._memory is not None:
            result = self._memory.retrieve(storage_key)
            if result is not None:
                self._store[storage_key] = result
                return result
        return entry

    def list_candidates(self) -> list[dict]:
        return [v for k, v in self._store.items() if k.startswith("knowledge:candidate:")]

    def list_entries(self) -> list[dict]:
        return [v for k, v in self._store.items() if k.startswith("knowledge:entry:")]

    def _emit_event(self, topic: str, candidate: KnowledgeCandidate) -> None:
        if self._events is not None and hasattr(self._events, 'emit'):
            self._events.emit(
                topic,
                candidate.to_dict(),
                execution_id=candidate.source_execution_id,
                correlation_id=candidate.source_execution_id,
                task_id=candidate.source_task_id,
            )
