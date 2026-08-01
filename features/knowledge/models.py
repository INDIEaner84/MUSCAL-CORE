from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Optional


class EvidenceLevel(Enum):
    VERIFIED = "VERIFIED"
    OBSERVED = "OBSERVED"
    INFERRED = "INFERRED"
    PROPOSED = "PROPOSED"
    UNKNOWN = "UNKNOWN"


class KnowledgeState(Enum):
    CANDIDATE = "CANDIDATE"
    VALIDATED = "VALIDATED"
    REJECTED = "REJECTED"
    SUPERSEDED = "SUPERSEDED"


KNOWLEDGE_EVENTS = frozenset({
    "knowledge.candidate.created",
    "knowledge.candidate.validated",
    "knowledge.candidate.rejected",
    "knowledge.entry.updated",
    "knowledge.retrieval.requested",
})


@dataclass
class KnowledgeCandidate:
    id: str
    source_execution_id: str
    source_task_id: str
    project: str
    category: str
    problem: str
    solution: str
    evidence: str
    verification: str
    confidence: float
    evidence_level: EvidenceLevel = EvidenceLevel.UNKNOWN
    state: KnowledgeState = KnowledgeState.CANDIDATE
    reuse_conditions: str = ""
    limitations: str = ""
    created_at: str = ""

    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now(timezone.utc).isoformat()
        if isinstance(self.evidence_level, str):
            self.evidence_level = EvidenceLevel(self.evidence_level)
        if isinstance(self.state, str):
            self.state = KnowledgeState(self.state)

    def to_dict(self) -> dict:
        return {
            "knowledge_candidate": {
                "id": self.id,
                "source_execution_id": self.source_execution_id,
                "source_task_id": self.source_task_id,
                "project": self.project,
                "category": self.category,
                "problem": self.problem,
                "solution": self.solution,
                "evidence": self.evidence,
                "verification": self.verification,
                "confidence": self.confidence,
                "evidence_level": self.evidence_level.value,
                "state": self.state.value,
                "reuse_conditions": self.reuse_conditions,
                "limitations": self.limitations,
                "created_at": self.created_at,
            }
        }


@dataclass
class KnowledgeEntry:
    knowledge_id: str
    candidate_id: str
    entry: dict
    stored_at: str = ""

    def __post_init__(self):
        if not self.stored_at:
            self.stored_at = datetime.now(timezone.utc).isoformat()

    def to_dict(self) -> dict:
        return {
            "knowledge_entry": {
                "knowledge_id": self.knowledge_id,
                "candidate_id": self.candidate_id,
                "entry": self.entry,
                "stored_at": self.stored_at,
            }
        }


@dataclass
class KnowledgeMatch:
    entry: dict
    relevance: float
    confidence: float
    evidence: str
    source_execution: str

    def to_dict(self) -> dict:
        return {
            "knowledge_match": {
                "entry": self.entry,
                "relevance": self.relevance,
                "confidence": self.confidence,
                "evidence": self.evidence,
                "source_execution": self.source_execution,
            }
        }
