from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional


class EvidenceStatus(str, Enum):
    VERIFIED = "VERIFIED"
    INFERRED = "INFERRED"
    MISSING = "MISSING"
    CONFLICT = "CONFLICT"

    def __repr__(self):
        return self.value


class RelationType(str, Enum):
    CAUSES = "CAUSES"
    AUTHORIZES = "AUTHORIZES"
    CONTAINS = "CONTAINS"
    CORRELATES_WITH = "CORRELATES_WITH"
    PRECEDES = "PRECEDES"
    RETRIES = "RETRIES"
    VERIFIES = "VERIFIES"
    PRODUCES = "PRODUCES"
    DERIVES_FROM = "DERIVES_FROM"


@dataclass
class Relation:
    source_id: str
    relation_type: RelationType
    target_id: str
    status: EvidenceStatus
    evidence_source: str
    reason: str = ""

    def to_dict(self) -> dict:
        return {
            "source_id": self.source_id,
            "relation_type": self.relation_type.value,
            "target_id": self.target_id,
            "status": self.status.value,
            "evidence_source": self.evidence_source,
            "reason": self.reason,
        }


@dataclass
class IdentityRecord:
    execution_id: str
    trace_id: str
    span_id: str
    decision_id: str
    receipt_id: str
    verification_id: str

    def to_dict(self) -> dict:
        return {
            "execution_id": self.execution_id,
            "trace_id": self.trace_id,
            "span_id": self.span_id,
            "decision_id": self.decision_id,
            "receipt_id": self.receipt_id,
            "verification_id": self.verification_id,
        }


@dataclass
class GovernanceRecord:
    decision_id: str
    governance_action: str
    decision_status: str
    decision_type: str
    trace_id: str
    span_id: str
    reasoning: str
    made_at: str

    def to_dict(self) -> dict:
        return {
            "decision_id": self.decision_id,
            "governance_action": self.governance_action,
            "decision_status": self.decision_status,
            "decision_type": self.decision_type,
            "trace_id": self.trace_id,
            "span_id": self.span_id,
            "reasoning": self.reasoning,
            "made_at": self.made_at,
        }


@dataclass
class ExecutionRecord:
    execution_id: str
    tool_name: str
    success: bool
    execution_time: float
    correlation_id: str
    trace_id: str
    span_id: str
    decision_id: str
    receipt_id: str
    integrity_hash: str
    integrity_valid: bool
    finalized: bool
    agent_id: str = ""
    model_id: str = ""

    def to_dict(self) -> dict:
        return {
            "execution_id": self.execution_id,
            "tool_name": self.tool_name,
            "success": self.success,
            "execution_time": self.execution_time,
            "correlation_id": self.correlation_id,
            "trace_id": self.trace_id,
            "span_id": self.span_id,
            "decision_id": self.decision_id,
            "receipt_id": self.receipt_id,
            "integrity_hash": self.integrity_hash,
            "integrity_valid": self.integrity_valid,
            "finalized": self.finalized,
            "agent_id": self.agent_id,
            "model_id": self.model_id,
        }


@dataclass
class VerificationRecord:
    verification_id: str
    execution_id: str
    receipt_id: str
    verifier_id: str
    status: str
    decision_id: str

    def to_dict(self) -> dict:
        return {
            "verification_id": self.verification_id,
            "execution_id": self.execution_id,
            "receipt_id": self.receipt_id,
            "verifier_id": self.verifier_id,
            "status": self.status,
            "decision_id": self.decision_id,
        }


@dataclass
class GraphNodeRecord:
    node_id: str
    node_type: str
    payload: dict[str, Any]
    timestamp: float

    def to_dict(self) -> dict:
        return {
            "node_id": self.node_id,
            "node_type": self.node_type,
            "timestamp": self.timestamp,
        }


@dataclass
class GraphEdgeRecord:
    source_id: str
    target_id: str
    edge_type: str
    payload: dict[str, Any]

    def to_dict(self) -> dict:
        return {
            "source_id": self.source_id,
            "target_id": self.target_id,
            "edge_type": self.edge_type,
        }


@dataclass
class CausalGraph:
    nodes: list[GraphNodeRecord] = field(default_factory=list)
    edges: list[GraphEdgeRecord] = field(default_factory=list)
    relations: list[Relation] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "nodes": [n.to_dict() for n in self.nodes],
            "edges": [e.to_dict() for e in self.edges],
            "relations": [r.to_dict() for r in self.relations],
        }


@dataclass
class CompletenessSummary:
    verified: int = 0
    inferred: int = 0
    missing: int = 0
    conflict: int = 0

    def to_dict(self) -> dict:
        return {
            "VERIFIED": self.verified,
            "INFERRED": self.inferred,
            "MISSING": self.missing,
            "CONFLICT": self.conflict,
            "total": self.verified + self.inferred + self.missing + self.conflict,
        }


@dataclass
class IntegrityStatus:
    execution_id_consistent: EvidenceStatus = EvidenceStatus.MISSING
    trace_id_consistent: EvidenceStatus = EvidenceStatus.MISSING
    span_id_consistent: EvidenceStatus = EvidenceStatus.MISSING
    decision_id_consistent: EvidenceStatus = EvidenceStatus.MISSING
    receipt_integrity_valid: EvidenceStatus = EvidenceStatus.MISSING
    verification_consistent: EvidenceStatus = EvidenceStatus.MISSING
    decision_db_consistent: EvidenceStatus = EvidenceStatus.MISSING
    no_orphan_execution: EvidenceStatus = EvidenceStatus.MISSING
    no_orphan_decision: EvidenceStatus = EvidenceStatus.MISSING
    no_cross_trace: EvidenceStatus = EvidenceStatus.MISSING
    findings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "execution_id_consistent": self.execution_id_consistent.value,
            "trace_id_consistent": self.trace_id_consistent.value,
            "span_id_consistent": self.span_id_consistent.value,
            "decision_id_consistent": self.decision_id_consistent.value,
            "receipt_integrity_valid": self.receipt_integrity_valid.value,
            "verification_consistent": self.verification_consistent.value,
            "decision_db_consistent": self.decision_db_consistent.value,
            "no_orphan_execution": self.no_orphan_execution.value,
            "no_orphan_decision": self.no_orphan_decision.value,
            "no_cross_trace": self.no_cross_trace.value,
            "findings": self.findings,
        }


@dataclass
class SemanticTruthStatus:
    provenance_integrity: EvidenceStatus = EvidenceStatus.MISSING
    semantic_truth: str = "NOT ESTABLISHED"
    reason: str = "Provenance integrity does not imply semantic truth"

    def to_dict(self) -> dict:
        return {
            "provenance_integrity": self.provenance_integrity.value,
            "semantic_truth": self.semantic_truth,
            "reason": self.reason,
        }


@dataclass
class ReconstructionReport:
    identity: Optional[IdentityRecord] = None
    governance: Optional[GovernanceRecord] = None
    execution: Optional[ExecutionRecord] = None
    verification: Optional[VerificationRecord] = None
    causal_graph: Optional[CausalGraph] = None
    completeness: CompletenessSummary = field(default_factory=CompletenessSummary)
    integrity: IntegrityStatus = field(default_factory=IntegrityStatus)
    semantic_truth: SemanticTruthStatus = field(default_factory=SemanticTruthStatus)
    relations: list[Relation] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "identity": self.identity.to_dict() if self.identity else None,
            "governance": self.governance.to_dict() if self.governance else None,
            "execution": self.execution.to_dict() if self.execution else None,
            "verification": self.verification.to_dict() if self.verification else None,
            "causal_graph": self.causal_graph.to_dict() if self.causal_graph else None,
            "completeness": self.completeness.to_dict(),
            "integrity": self.integrity.to_dict(),
            "semantic_truth": self.semantic_truth.to_dict(),
            "relations": [r.to_dict() for r in self.relations],
        }
