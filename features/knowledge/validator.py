from __future__ import annotations

from typing import Optional

from .models import KnowledgeCandidate, KnowledgeState, EvidenceLevel


class KnowledgeValidator:

    def validate(self, candidate: KnowledgeCandidate) -> tuple[bool, list[str]]:
        reasons: list[str] = []

        if not candidate.source_execution_id:
            reasons.append("Missing source_execution_id — provenance required")
        if not candidate.source_task_id:
            reasons.append("Missing source_task_id — provenance required")
        if not candidate.problem or len(candidate.problem) < 5:
            reasons.append("Problem statement too short or missing")
        if not candidate.solution or len(candidate.solution) < 5:
            reasons.append("Solution too short or missing")
        if not candidate.evidence or candidate.evidence == "No verification report available":
            reasons.append("Evidence missing or unavailable")
        if candidate.confidence < 0.1:
            reasons.append(f"Confidence too low: {candidate.confidence}")
        if candidate.evidence_level == EvidenceLevel.UNKNOWN:
            reasons.append("Evidence level is UNKNOWN — cannot validate")
        if candidate.state == KnowledgeState.REJECTED:
            reasons.append("Candidate is already rejected")

        is_valid = len(reasons) == 0
        return is_valid, reasons

    def evaluate(self, candidate: KnowledgeCandidate) -> KnowledgeState:
        is_valid, reasons = self.validate(candidate)
        if candidate.state == KnowledgeState.REJECTED:
            return KnowledgeState.REJECTED
        if candidate.state == KnowledgeState.SUPERSEDED:
            return KnowledgeState.SUPERSEDED
        if is_valid:
            return KnowledgeState.VALIDATED
        return KnowledgeState.CANDIDATE
