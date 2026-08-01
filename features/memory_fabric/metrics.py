from __future__ import annotations

from typing import Any, Optional

from .models import MemoryEntry, UnifiedMemoryContext


class MemoryReuseScore:

    def compute(self, entry: MemoryEntry, retrieval_history: Optional[list[dict]] = None) -> float:
        if not retrieval_history:
            ref_count = len(entry.references) if entry.references else 0
            return min(1.0, ref_count / 10.0)
        matches = [h for h in retrieval_history if h.get("memory_id") == entry.id]
        return min(1.0, len(matches) / 10.0)

    def to_dict(self, entry: MemoryEntry,
                retrieval_history: Optional[list[dict]] = None) -> dict:
        score = self.compute(entry, retrieval_history)
        return {
            "memory_reuse": {
                "memory_id": entry.id,
                "reuse_score": score,
                "reference_count": len(entry.references) if entry.references else 0,
            }
        }


class MemoryImpactScore:

    def compute(self, entry: MemoryEntry, outcome: Optional[str] = None) -> float:
        if outcome:
            if outcome == "success":
                return 1.0
            if outcome == "partial":
                return 0.5
            if outcome == "failure":
                return 0.0
        base = 0.5
        content = self._flatten(entry.content)
        if any(w in content for w in ("success", "completed", "passed", "resolved")):
            base += 0.3
        if any(w in content for w in ("failed", "error", "crash")):
            base -= 0.2
        if entry.importance and entry.importance.total > 0.5:
            base += 0.2
        return max(0.0, min(1.0, base))

    def to_dict(self, entry: MemoryEntry, outcome: Optional[str] = None) -> dict:
        score = self.compute(entry, outcome)
        return {
            "memory_impact": {
                "memory_id": entry.id,
                "impact_score": score,
                "memory_type": entry.memory_type.value,
            }
        }

    def _flatten(self, content: dict) -> str:
        return " ".join(str(v) for v in content.values() if isinstance(v, (str, int, float)))


class KnowledgeTransferScore:

    def compute(self, entry: MemoryEntry,
                source_domain: str = "",
                target_domain: str = "") -> float:
        if not source_domain and not target_domain:
            mt = entry.memory_type
            type_scores = {
                "SEMANTIC": 0.85,
                "PROCEDURAL": 0.75,
                "DECISION": 0.65,
                "EXPERIENCE": 0.6,
                "EPISODIC": 0.4,
                "CONTEXT": 0.3,
            }
            return type_scores.get(mt.value, 0.5)
        if source_domain and target_domain:
            source_words = set(source_domain.lower().split())
            target_words = set(target_domain.lower().split())
            if source_words and target_words:
                overlap = len(source_words & target_words)
                total = len(source_words | target_words)
                domain_similarity = overlap / max(total, 1)
                return min(1.0, 0.5 + domain_similarity * 0.5)
        return 0.5

    def to_dict(self, entry: MemoryEntry,
                source_domain: str = "",
                target_domain: str = "") -> dict:
        score = self.compute(entry, source_domain, target_domain)
        return {
            "knowledge_transfer": {
                "memory_id": entry.id,
                "transfer_score": score,
                "source_domain": source_domain,
                "target_domain": target_domain,
            }
        }
