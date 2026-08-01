from __future__ import annotations
import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class OutcomeStatus(str, Enum):
    SUCCESS = "SUCCESS"
    PARTIAL = "PARTIAL"
    FAILURE = "FAILURE"
    UNKNOWN = "UNKNOWN"


class EvidenceStatus(str, Enum):
    VERIFIED = "VERIFIED"
    INFERRED = "INFERRED"
    MISSING = "MISSING"
    CONFLICT = "CONFLICT"


_OUTCOME_TRANSITIONS: Dict[OutcomeStatus, List[OutcomeStatus]] = {
    OutcomeStatus.UNKNOWN: [OutcomeStatus.SUCCESS, OutcomeStatus.PARTIAL, OutcomeStatus.FAILURE],
    OutcomeStatus.SUCCESS: [OutcomeStatus.PARTIAL, OutcomeStatus.FAILURE],
    OutcomeStatus.PARTIAL: [OutcomeStatus.SUCCESS, OutcomeStatus.FAILURE],
    OutcomeStatus.FAILURE: [],
}

_EVIDENCE_NO_ESCALATION: Dict[EvidenceStatus, List[EvidenceStatus]] = {
    EvidenceStatus.VERIFIED: [EvidenceStatus.VERIFIED],
    EvidenceStatus.INFERRED: [EvidenceStatus.INFERRED, EvidenceStatus.VERIFIED],
    EvidenceStatus.MISSING: [EvidenceStatus.MISSING, EvidenceStatus.INFERRED, EvidenceStatus.VERIFIED],
    EvidenceStatus.CONFLICT: [EvidenceStatus.CONFLICT, EvidenceStatus.VERIFIED],
}


def merge_outcome_statuses(statuses: List[OutcomeStatus]) -> OutcomeStatus:
    if OutcomeStatus.FAILURE in statuses:
        return OutcomeStatus.FAILURE
    if OutcomeStatus.PARTIAL in statuses:
        return OutcomeStatus.PARTIAL
    if OutcomeStatus.SUCCESS in statuses:
        if OutcomeStatus.UNKNOWN in statuses:
            return OutcomeStatus.PARTIAL
        return OutcomeStatus.SUCCESS
    return OutcomeStatus.UNKNOWN


def resolve_evidence_status(statuses: List[EvidenceStatus]) -> EvidenceStatus:
    # Precedence: CONFLICT > VERIFIED > INFERRED > MISSING
    if EvidenceStatus.CONFLICT in statuses:
        return EvidenceStatus.CONFLICT
    if EvidenceStatus.VERIFIED in statuses:
        return EvidenceStatus.VERIFIED
    if EvidenceStatus.INFERRED in statuses:
        return EvidenceStatus.INFERRED
    return EvidenceStatus.MISSING


@dataclass
class OutcomeRecord:
    outcome_id: str = ""
    execution_id: str = ""
    trace_id: str = ""
    decision_id: str = ""
    intended_outcome: OutcomeStatus = OutcomeStatus.UNKNOWN
    observed_outcome: OutcomeStatus = OutcomeStatus.UNKNOWN
    verified_outcome: OutcomeStatus = OutcomeStatus.UNKNOWN
    outcome_status: OutcomeStatus = OutcomeStatus.UNKNOWN
    evidence_status: EvidenceStatus = EvidenceStatus.MISSING
    source: str = "unknown"
    source_id: str = ""
    created_at: float = 0.0
    updated_at: float = 0.0
    provenance: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    _finalized: bool = False
    _integrity_hash: str = ""

    def __post_init__(self):
        if not self.outcome_id:
            self.outcome_id = str(uuid.uuid4())
        if not self.created_at:
            self.created_at = time.time()
        if not self.updated_at:
            self.updated_at = self.created_at
        self._resolve_status()

    def _resolve_status(self) -> None:
        self.outcome_status = merge_outcome_statuses([
            self.intended_outcome,
            self.observed_outcome,
            self.verified_outcome,
        ])
        has_observed = self.observed_outcome != OutcomeStatus.UNKNOWN
        has_verified = self.verified_outcome != OutcomeStatus.UNKNOWN
        if has_observed and has_verified and self.observed_outcome != self.verified_outcome:
            self.evidence_status = EvidenceStatus.CONFLICT
        elif has_verified:
            self.evidence_status = EvidenceStatus.VERIFIED
        elif has_observed:
            if self.source != "unknown":
                self.evidence_status = EvidenceStatus.INFERRED
            else:
                self.evidence_status = EvidenceStatus.MISSING
        else:
            self.evidence_status = EvidenceStatus.MISSING

    def update_observed(self, outcome: OutcomeStatus, source: str = "", source_id: str = "") -> None:
        if self._finalized:
            raise ValueError("cannot mutate finalized OutcomeRecord")
        self.observed_outcome = outcome
        if source:
            self.source = source
        if source_id:
            self.source_id = source_id
        self.updated_at = time.time()
        self._resolve_status()

    def update_verified(self, outcome: OutcomeStatus, source: str = "", source_id: str = "") -> None:
        if self._finalized:
            raise ValueError("cannot mutate finalized OutcomeRecord")
        self.verified_outcome = outcome
        if source:
            self.source = source
        if source_id:
            self.source_id = source_id
        self.updated_at = time.time()
        self._resolve_status()

    def finalize(self) -> None:
        if self._finalized:
            return
        self._finalized = True
        import hashlib
        import json
        raw = (
            str(self.outcome_id) + "|" +
            str(self.execution_id) + "|" +
            str(self.trace_id) + "|" +
            str(self.decision_id) + "|" +
            str(self.intended_outcome.value) + "|" +
            str(self.observed_outcome.value) + "|" +
            str(self.verified_outcome.value) + "|" +
            str(self.outcome_status.value) + "|" +
            str(self.evidence_status.value) + "|" +
            str(self.source) + "|" +
            str(self.created_at) + "|" +
            json.dumps(self.provenance, sort_keys=True, default=str)
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
            "outcome_id": self.outcome_id,
            "execution_id": self.execution_id,
            "trace_id": self.trace_id,
            "decision_id": self.decision_id,
            "intended_outcome": self.intended_outcome.value,
            "observed_outcome": self.observed_outcome.value,
            "verified_outcome": self.verified_outcome.value,
            "outcome_status": self.outcome_status.value,
            "evidence_status": self.evidence_status.value,
            "source": self.source,
            "source_id": self.source_id,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "provenance": self.provenance,
            "metadata": self.metadata,
            "finalized": self._finalized,
            "integrity_hash": self._integrity_hash,
        }

    @staticmethod
    def from_dict(d: Dict[str, Any]) -> "OutcomeRecord":
        rec = OutcomeRecord(
            outcome_id=d.get("outcome_id", ""),
            execution_id=d.get("execution_id", ""),
            trace_id=d.get("trace_id", ""),
            decision_id=d.get("decision_id", ""),
            intended_outcome=OutcomeStatus(d.get("intended_outcome", "UNKNOWN")),
            observed_outcome=OutcomeStatus(d.get("observed_outcome", "UNKNOWN")),
            verified_outcome=OutcomeStatus(d.get("verified_outcome", "UNKNOWN")),
            source=d.get("source", "unknown"),
            source_id=d.get("source_id", ""),
            created_at=d.get("created_at", 0.0),
            updated_at=d.get("updated_at", 0.0),
            provenance=d.get("provenance", {}),
            metadata=d.get("metadata", {}),
        )
        rec._finalized = d.get("finalized", False)
        rec._integrity_hash = d.get("integrity_hash", "")
        rec._resolve_status()
        return rec
