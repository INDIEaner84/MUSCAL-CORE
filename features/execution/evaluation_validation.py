from __future__ import annotations
import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class ValidationResult(str, Enum):
    CONFIRMED = "CONFIRMED"
    REFUTED = "REFUTED"
    PARTIALLY_CONFIRMED = "PARTIALLY_CONFIRMED"
    INCONCLUSIVE = "INCONCLUSIVE"


@dataclass
class EvaluationValidation:
    validation_id: str = ""
    evaluation_id: str = ""
    execution_id: str = ""
    trace_id: str = ""
    span_id: str = ""
    decision_id: str = ""
    agent_id: str = ""
    model_id: str = ""
    outcome_id: str = ""
    validation_result: ValidationResult = ValidationResult.INCONCLUSIVE
    rationale: str = ""
    evidence: List[Dict[str, Any]] = field(default_factory=list)
    created_at: float = 0.0
    provenance: Dict[str, Any] = field(default_factory=dict)
    _finalized: bool = False
    _integrity_hash: str = ""

    def __post_init__(self):
        if not self.validation_id:
            self.validation_id = str(uuid.uuid4())
        if not self.created_at:
            self.created_at = time.time()

    def finalize(self) -> None:
        if self._finalized:
            return
        self._finalized = True
        import hashlib
        import json
        raw = (
            str(self.validation_id) + "|" +
            str(self.evaluation_id) + "|" +
            str(self.execution_id) + "|" +
            str(self.trace_id) + "|" +
            str(self.span_id) + "|" +
            str(self.decision_id) + "|" +
            str(self.agent_id) + "|" +
            str(self.model_id) + "|" +
            str(self.outcome_id) + "|" +
            str(self.validation_result.value) + "|" +
            str(self.rationale) + "|" +
            str(self.created_at)
        )
        self._integrity_hash = hashlib.sha256(raw.encode()).hexdigest()

    @property
    def finalized(self) -> bool:
        return self._finalized

    @property
    def integrity_hash(self) -> str:
        return self._integrity_hash

    def verify_integrity(self) -> bool:
        if not self._finalized:
            return False
        saved_hash = self._integrity_hash
        self._finalized = False
        self._integrity_hash = ""
        self.finalize()
        return self._integrity_hash == saved_hash

    def to_dict(self) -> Dict[str, Any]:
        return {
            "validation_id": self.validation_id,
            "evaluation_id": self.evaluation_id,
            "execution_id": self.execution_id,
            "trace_id": self.trace_id,
            "span_id": self.span_id,
            "decision_id": self.decision_id,
            "agent_id": self.agent_id,
            "model_id": self.model_id,
            "outcome_id": self.outcome_id,
            "validation_result": self.validation_result.value,
            "rationale": self.rationale,
            "evidence": self.evidence,
            "created_at": self.created_at,
            "provenance": self.provenance,
            "finalized": self._finalized,
            "integrity_hash": self._integrity_hash,
        }

    @staticmethod
    def from_dict(d: Dict[str, Any]) -> "EvaluationValidation":
        v = EvaluationValidation(
            validation_id=d.get("validation_id", ""),
            evaluation_id=d.get("evaluation_id", ""),
            execution_id=d.get("execution_id", ""),
            trace_id=d.get("trace_id", ""),
            span_id=d.get("span_id", ""),
            decision_id=d.get("decision_id", ""),
            agent_id=d.get("agent_id", ""),
            model_id=d.get("model_id", ""),
            outcome_id=d.get("outcome_id", ""),
            validation_result=ValidationResult(d.get("validation_result", "INCONCLUSIVE")),
            rationale=d.get("rationale", ""),
            evidence=d.get("evidence", []),
            created_at=d.get("created_at", 0.0),
            provenance=d.get("provenance", {}),
        )
        v._finalized = d.get("finalized", False)
        v._integrity_hash = d.get("integrity_hash", "")
        return v
