from __future__ import annotations

import time
from datetime import datetime, timezone
from typing import Any, Optional

from .models import MemoryEntry, MemoryImportanceScore


class ImportanceEngine:

    def score(self, entry: MemoryEntry, *,
              all_entries: Optional[list[MemoryEntry]] = None) -> MemoryImportanceScore:
        score = MemoryImportanceScore()

        score.frequency = self._compute_frequency(entry, all_entries)
        score.success_impact = self._compute_success_impact(entry)
        score.recency = self._compute_recency(entry)
        score.confidence = self._compute_confidence(entry)
        score.future_usefulness = self._compute_future_usefulness(entry)
        score.verification_level = self._compute_verification_level(entry)
        score.compute_total()

        return score

    def explain(self, entry: MemoryEntry, *,
                all_entries: Optional[list[MemoryEntry]] = None) -> dict:
        score = self.score(entry, all_entries=all_entries)
        factors = []
        factors.append({"factor": "frequency", "value": score.frequency,
                        "weight": 0.15, "contribution": round(score.frequency * 0.15, 4),
                        "reason": self._explain_frequency(entry, all_entries)})
        factors.append({"factor": "success_impact", "value": score.success_impact,
                        "weight": 0.25, "contribution": round(score.success_impact * 0.25, 4),
                        "reason": self._explain_success_impact(entry)})
        factors.append({"factor": "recency", "value": score.recency,
                        "weight": 0.15, "contribution": round(score.recency * 0.15, 4),
                        "reason": self._explain_recency(entry)})
        factors.append({"factor": "confidence", "value": score.confidence,
                        "weight": 0.15, "contribution": round(score.confidence * 0.15, 4),
                        "reason": f"Entry confidence is {entry.confidence}"})
        factors.append({"factor": "future_usefulness", "value": score.future_usefulness,
                        "weight": 0.15, "contribution": round(score.future_usefulness * 0.15, 4),
                        "reason": f"MemoryType {entry.memory_type.value} has base usefulness {score.future_usefulness}"})
        factors.append({"factor": "verification_level", "value": score.verification_level,
                        "weight": 0.15, "contribution": round(score.verification_level * 0.15, 4),
                        "reason": self._explain_verification(entry)})
        return {
            "total": score.total,
            "factors": factors,
        }

    def _explain_frequency(self, entry: MemoryEntry,
                            all_entries: Optional[list[MemoryEntry]]) -> str:
        if not all_entries or not entry.references:
            return "No reference data — default frequency 0.1"
        count = sum(1 for e in all_entries if self._is_similar(e, entry))
        return f"Found {count} similar entries out of {len(all_entries)}"

    def _explain_success_impact(self, entry: MemoryEntry) -> str:
        content = self._flatten(entry.content)
        if any(w in content for w in ("success", "completed", "passed", "resolved")):
            return "Content indicates success outcome"
        if any(w in content for w in ("failed", "error", "crash", "rejected")):
            return "Content indicates failure outcome"
        return "No clear success/failure signal — default 0.4"

    def _explain_recency(self, entry: MemoryEntry) -> str:
        try:
            dt = datetime.fromisoformat(entry.timestamp)
            age_hours = (datetime.now(timezone.utc) - dt).total_seconds() / 3600
            return f"Entry is {age_hours:.1f} hours old — recency {max(0.0, 1.0 - (age_hours / 720.0)):.4f}"
        except (ValueError, TypeError):
            return "Cannot parse timestamp — default recency 0.3"

    def _explain_verification(self, entry: MemoryEntry) -> str:
        prov = entry.provenance or {}
        if any(k in prov for k in ("passed", "verified", "validated")):
            return "Provenance indicates verification passed"
        if any(k in prov for k in ("observed", "inferred")):
            return "Provenance indicates observed or inferred status"
        return "No verification data — default 0.2"

    def _compute_frequency(self, entry: MemoryEntry,
                            all_entries: Optional[list[MemoryEntry]]) -> float:
        if not all_entries or not entry.references:
            return 0.1
        count = sum(1 for e in all_entries if self._is_similar(e, entry))
        return min(1.0, count / max(len(all_entries), 1))

    def _compute_success_impact(self, entry: MemoryEntry) -> float:
        content = self._flatten(entry.content)
        if any(w in content for w in ("success", "completed", "passed", "resolved")):
            return 0.9
        if any(w in content for w in ("failed", "error", "crash", "rejected")):
            return 0.7
        return 0.4

    def _compute_recency(self, entry: MemoryEntry) -> float:
        try:
            dt = datetime.fromisoformat(entry.timestamp)
            age_hours = (datetime.now(timezone.utc) - dt).total_seconds() / 3600
            return max(0.0, 1.0 - (age_hours / 720.0))
        except (ValueError, TypeError):
            return 0.3

    def _compute_confidence(self, entry: MemoryEntry) -> float:
        return min(1.0, entry.confidence)

    def _compute_future_usefulness(self, entry: MemoryEntry) -> float:
        mt = entry.memory_type
        usefulness_map = {
            "PROCEDURAL": 0.9,
            "SEMANTIC": 0.85,
            "DECISION": 0.75,
            "EXPERIENCE": 0.7,
            "EPISODIC": 0.5,
            "CONTEXT": 0.4,
        }
        return usefulness_map.get(mt.value, 0.5)

    def _compute_verification_level(self, entry: MemoryEntry) -> float:
        prov = entry.provenance or {}
        if any(k in prov for k in ("passed", "verified", "validated")):
            return 0.9
        if any(k in prov for k in ("observed", "inferred")):
            return 0.5
        return 0.2

    def _is_similar(self, a: MemoryEntry, b: MemoryEntry) -> bool:
        return a.memory_type == b.memory_type

    def _flatten(self, content: dict) -> str:
        return " ".join(str(v) for v in content.values() if isinstance(v, (str, int, float)))
