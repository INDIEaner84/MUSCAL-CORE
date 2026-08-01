from __future__ import annotations

import time
import uuid
from typing import Any, Optional

from .models import KnowledgeMatch, KnowledgeState


class KnowledgeRetriever:

    def __init__(self, writer: Optional[Any] = None,
                 memory_adapter: Optional[Any] = None,
                 event_emitter: Optional[Any] = None):
        self._writer = writer
        self._memory = memory_adapter
        self._events = event_emitter

    def retrieve_relevant(self, task_context: str, top_k: int = 3) -> list[KnowledgeMatch]:
        context_lower = task_context.lower()
        words = [w.strip(".,!?;:") for w in context_lower.split() if len(w) > 3]

        candidates = []
        if self._writer is not None and hasattr(self._writer, 'list_entries'):
            candidates = self._writer.list_entries()
        elif self._memory is not None and hasattr(self._memory, 'search'):
            raw = self._memory.search(task_context, limit=top_k * 2)
            if isinstance(raw, list):
                candidates = raw
            elif isinstance(raw, dict):
                candidates = raw.get("store", raw.get("results", []))

        scored = []
        for entry in candidates:
            if not isinstance(entry, dict):
                continue
            ke = entry.get("knowledge_entry", entry)
            inner = ke.get("entry", ke) if isinstance(ke, dict) else ke
            entry_data = inner if isinstance(inner, dict) else ke
            candidate_data = inner.get("knowledge_candidate", inner) if isinstance(inner, dict) else {}

            text = " ".join(str(v) for v in candidate_data.values() if isinstance(v, str)).lower()
            match_count = sum(1 for w in words if w in text)
            if match_count == 0:
                continue

            relevance = match_count / max(len(words), 1)
            confidence = candidate_data.get("confidence", 0.5)
            state_str = candidate_data.get("state", "")

            if state_str and state_str != KnowledgeState.VALIDATED.value:
                relevance *= 0.5

            scored.append((relevance, entry_data, candidate_data))

        scored.sort(key=lambda x: x[0], reverse=True)
        results = scored[:top_k]

        self._emit_retrieval_event(task_context, len(results))

        matches = []
        for relevance, entry_data, candidate_data in results:
            matches.append(KnowledgeMatch(
                entry=entry_data,
                relevance=round(relevance, 2),
                confidence=candidate_data.get("confidence", 0.5),
                evidence=candidate_data.get("evidence", ""),
                source_execution=candidate_data.get("source_execution_id", ""),
            ))
        return matches

    def _emit_retrieval_event(self, context: str, result_count: int) -> None:
        if self._events is not None and hasattr(self._events, 'emit'):
            self._events.emit(
                "knowledge.retrieval.requested",
                {"context": context[:500], "result_count": result_count},
            )
