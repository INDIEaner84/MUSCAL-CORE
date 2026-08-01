from __future__ import annotations

from typing import Any, Optional

from .models import MemoryEntry, UnifiedMemoryContext


class MemoryRetriever:

    def __init__(self):
        self._store_provider = None

    def register_store_provider(self, provider: Any) -> None:
        self._store_provider = provider

    def retrieve_context(self, task: Optional[dict] = None,
                         intent: Optional[dict] = None,
                         goal: Optional[dict] = None,
                         domain: Optional[str] = None,
                         constraints: Optional[list[str]] = None,
                         execution_id: str = "",
                         top_k: int = 5) -> UnifiedMemoryContext:
        context = UnifiedMemoryContext(execution_id=execution_id)
        query = self._build_query(task, intent, goal, domain, constraints)

        all_entries = self._fetch_all_entries()
        sorted_entries = self._sort_by_priority(all_entries, query)

        for entry in sorted_entries:
            self._classify_entry(entry, context, query, top_k)

        warnings = self._generate_warnings(context, constraints)
        context.warnings.extend(warnings)

        return context

    def _build_query(self, task: Optional[dict], intent: Optional[dict],
                      goal: Optional[dict], domain: Optional[str],
                      constraints: Optional[list[str]]) -> str:
        parts = []
        if task:
            parts.extend(str(v) for v in task.values() if isinstance(v, (str, int, float)))
        if intent:
            parts.append(intent.get("intent", {}).get("goal", ""))
        if goal:
            parts.append(goal.get("goal", {}).get("description", ""))
        if domain:
            parts.append(domain)
        if constraints:
            parts.extend(constraints)
        return " ".join(parts).lower()

    def _fetch_all_entries(self) -> list[MemoryEntry]:
        if self._store_provider is not None:
            if hasattr(self._store_provider, 'list_entries'):
                return self._store_provider.list_entries()
            if hasattr(self._store_provider, 'search'):
                raw = self._store_provider.search("", limit=100)
                return raw if isinstance(raw, list) else []
        return []

    def _sort_by_priority(self, entries: list[MemoryEntry], query: str) -> list[MemoryEntry]:
        def priority_key(entry: MemoryEntry) -> tuple:
            verified = 0
            if entry.provenance:
                if any(k in entry.provenance for k in ("passed", "verified", "validated")):
                    verified = 2
                elif any(k in entry.provenance for k in ("observed", "inferred")):
                    verified = 1
            success = 0
            text = self._flatten_text(entry.content)
            if any(w in text for w in ("success", "completed", "passed", "resolved")):
                success = 1
            relevance = self._relevance_score(entry, query)
            recency_val = 0.0
            if entry.timestamp:
                try:
                    from datetime import datetime, timezone
                    dt = datetime.fromisoformat(entry.timestamp)
                    recency_val = dt.timestamp()
                except (ValueError, TypeError):
                    recency_val = 0.0
            return (-verified, -success, -relevance, -recency_val)
        return sorted(entries, key=priority_key)

    def _flatten_text(self, content: dict) -> str:
        return " ".join(str(v) for v in content.values() if isinstance(v, (str, int, float)))

    def _classify_entry(self, entry: MemoryEntry, context: UnifiedMemoryContext,
                         query: str, top_k: int) -> None:
        mt = entry.memory_type
        relevance = self._relevance_score(entry, query)
        if relevance <= 0:
            return
        if mt.value == "EPISODIC" and len(context.experiences) < top_k:
            context.experiences.append(entry)
        elif mt.value == "DECISION" and len(context.decisions) < top_k:
            context.decisions.append(entry)
        elif mt.value in ("PROCEDURAL", "EXPERIENCE") and len(context.previous_solutions) < top_k:
            if hasattr(entry, 'id'):
                context.previous_solutions.append(entry)

    def _relevance_score(self, entry: MemoryEntry, query: str) -> float:
        if not query:
            return 0.1
        text = self._flatten_text(entry.content)
        text = text.lower()
        words = query.split()
        matches = sum(1 for w in words if w in text)
        return matches / max(len(words), 1)

    def _generate_warnings(self, context: UnifiedMemoryContext,
                            constraints: Optional[list[str]]) -> list[str]:
        warnings = []
        total = (len(context.experiences) + len(context.decisions)
                 + len(context.previous_solutions))
        if total == 0:
            warnings.append("No prior memory entries found for this context")
        return warnings
