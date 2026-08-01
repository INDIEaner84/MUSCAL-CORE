from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional


class MemoryType(str, Enum):
    EPISODIC = "EPISODIC"
    SEMANTIC = "SEMANTIC"
    PROCEDURAL = "PROCEDURAL"
    DECISION = "DECISION"
    EXPERIENCE = "EXPERIENCE"
    CONTEXT = "CONTEXT"


MEMORY_TYPES = frozenset({t.value for t in MemoryType})


class LifecycleState(str, Enum):
    NEW = "NEW"
    CLASSIFIED = "CLASSIFIED"
    VALIDATED = "VALIDATED"
    PROMOTED = "PROMOTED"
    ARCHIVED = "ARCHIVED"


LIFECYCLE_STATES = frozenset({s.value for s in LifecycleState})

LIFECYCLE_TRANSITIONS: dict[str, set[str]] = {
    "NEW": {"CLASSIFIED"},
    "CLASSIFIED": {"VALIDATED"},
    "VALIDATED": {"PROMOTED", "ARCHIVED"},
    "PROMOTED": {"ARCHIVED"},
    "ARCHIVED": set(),
}


@dataclass
class MemoryImportanceScore:
    frequency: float = 0.0
    success_impact: float = 0.0
    recency: float = 0.0
    confidence: float = 0.0
    future_usefulness: float = 0.0
    verification_level: float = 0.0
    total: float = 0.0

    def compute_total(self) -> float:
        self.total = round(
            self.frequency * 0.15
            + self.success_impact * 0.25
            + self.recency * 0.15
            + self.confidence * 0.15
            + self.future_usefulness * 0.15
            + self.verification_level * 0.15,
            4,
        )
        return self.total

    def to_dict(self) -> dict:
        return {
            "memory_importance": {
                "frequency": self.frequency,
                "success_impact": self.success_impact,
                "recency": self.recency,
                "confidence": self.confidence,
                "future_usefulness": self.future_usefulness,
                "verification_level": self.verification_level,
                "total": self.total if self.total else self.compute_total(),
            }
        }


@dataclass
class MemoryEntry:
    id: str
    memory_type: MemoryType
    content: dict
    source: str
    timestamp: str = ""
    confidence: float = 0.5
    importance: Optional[MemoryImportanceScore] = None
    references: list[str] = field(default_factory=list)
    provenance: dict = field(default_factory=dict)

    def __post_init__(self):
        if not self.id:
            raise ValueError("MemoryEntry.id is required")
        if self.content is None:
            raise ValueError("MemoryEntry.content is required")
        if not self.source:
            raise ValueError("MemoryEntry.source is required")
        if not self.timestamp:
            self.timestamp = datetime.now(timezone.utc).isoformat()
        if isinstance(self.memory_type, str):
            self.memory_type = MemoryType(self.memory_type)
        self.confidence = max(0.0, min(1.0, self.confidence))
        if "lifecycle_state" not in self.provenance:
            self.provenance["lifecycle_state"] = "NEW"
            self.provenance["lifecycle_updated_at"] = self.timestamp

    @property
    def lifecycle_state(self) -> str:
        return self.provenance.get("lifecycle_state", "NEW")

    def transition_lifecycle(self, new_state: str) -> tuple[bool, str]:
        current = self.lifecycle_state
        allowed = LIFECYCLE_TRANSITIONS.get(current, set())
        if new_state not in allowed:
            return False, f"Cannot transition from {current} to {new_state}"
        self.provenance["lifecycle_state"] = new_state
        self.provenance["lifecycle_updated_at"] = datetime.now(timezone.utc).isoformat()
        return True, f"Transitioned from {current} to {new_state}"

    def to_dict(self) -> dict:
        return {
            "memory_entry": {
                "id": self.id,
                "memory_type": self.memory_type.value,
                "content": self.content,
                "source": self.source,
                "timestamp": self.timestamp,
                "confidence": self.confidence,
                "importance": self.importance.to_dict() if self.importance else None,
                "references": self.references,
                "provenance": self.provenance,
                "lifecycle_state": self.lifecycle_state,
            }
        }


@dataclass
class UnifiedMemoryContext:
    experiences: list[MemoryEntry] = field(default_factory=list)
    knowledge: list[dict] = field(default_factory=list)
    decisions: list[MemoryEntry] = field(default_factory=list)
    previous_solutions: list[MemoryEntry] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    execution_id: str = ""

    def to_dict(self) -> dict:
        return {
            "unified_memory_context": {
                "experiences": [e.to_dict() for e in self.experiences],
                "knowledge": self.knowledge,
                "decisions": [d.to_dict() for d in self.decisions],
                "previous_solutions": [s.to_dict() for s in self.previous_solutions],
                "warnings": self.warnings,
                "execution_id": self.execution_id,
                "experience_count": len(self.experiences),
                "decision_count": len(self.decisions),
                "solution_count": len(self.previous_solutions),
            }
        }
