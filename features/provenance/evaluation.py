import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Optional

from features.provenance.models import (
    EvidenceStatus,
    ReconstructionReport,
    RelationType,
)

log = logging.getLogger("muscal.provenance.evaluation")


class EvaluationLevel(str, Enum):
    GOOD = "GOOD"
    ACCEPTABLE = "ACCEPTABLE"
    BAD = "BAD"
    UNKNOWN = "UNKNOWN"


class OutcomeState(str, Enum):
    SUCCESS = "SUCCESS"
    PARTIAL = "PARTIAL"
    FAILURE = "FAILURE"
    UNKNOWN = "UNKNOWN"


class CausalAssessment(str, Enum):
    CAUSALLY_SUPPORTED = "CAUSALLY_SUPPORTED"
    TEMPORALLY_ASSOCIATED = "TEMPORALLY_ASSOCIATED"
    CORRELATED = "CORRELATED"
    INFERRED = "INFERRED"
    UNKNOWN = "UNKNOWN"


@dataclass
class EvidenceRef:
    source_id: str
    relation_type: str
    status: str
    evidence_source: str
    reason: str

    def to_dict(self) -> dict:
        return {
            "source_id": self.source_id,
            "relation_type": self.relation_type,
            "status": self.status,
            "evidence_source": self.evidence_source,
            "reason": self.reason,
        }


@dataclass
class EvaluationClaim:
    claim_id: str
    target_id: str
    criterion: str
    conclusion: str
    evidence: list[EvidenceRef] = field(default_factory=list)
    evidence_status: str = "MISSING"
    rationale: str = ""
    uncertainty: str = ""
    conflicts: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "claim_id": self.claim_id,
            "target_id": self.target_id,
            "criterion": self.criterion,
            "conclusion": self.conclusion,
            "evidence": [e.to_dict() for e in self.evidence],
            "evidence_status": self.evidence_status,
            "rationale": self.rationale,
            "uncertainty": self.uncertainty,
            "conflicts": self.conflicts,
        }


@dataclass
class DecisionQuality:
    authority_compliance: EvaluationLevel = EvaluationLevel.UNKNOWN
    policy_compliance: EvaluationLevel = EvaluationLevel.UNKNOWN
    evidence_sufficiency: EvaluationLevel = EvaluationLevel.UNKNOWN
    provenance_completeness: EvaluationLevel = EvaluationLevel.UNKNOWN
    decision_consistency: EvaluationLevel = EvaluationLevel.UNKNOWN
    overall: EvaluationLevel = EvaluationLevel.UNKNOWN

    def to_dict(self) -> dict:
        return {
            "authority_compliance": self.authority_compliance.value,
            "policy_compliance": self.policy_compliance.value,
            "evidence_sufficiency": self.evidence_sufficiency.value,
            "provenance_completeness": self.provenance_completeness.value,
            "decision_consistency": self.decision_consistency.value,
            "overall": self.overall.value,
        }


@dataclass
class ExecutionQuality:
    execution_success: EvaluationLevel = EvaluationLevel.UNKNOWN
    policy_compliance: EvaluationLevel = EvaluationLevel.UNKNOWN
    trust_boundary_compliance: EvaluationLevel = EvaluationLevel.UNKNOWN
    provenance_integrity: EvaluationLevel = EvaluationLevel.UNKNOWN
    verification_result: EvaluationLevel = EvaluationLevel.UNKNOWN
    latency: EvaluationLevel = EvaluationLevel.UNKNOWN
    resource_efficiency: EvaluationLevel = EvaluationLevel.UNKNOWN
    overall: EvaluationLevel = EvaluationLevel.UNKNOWN

    def to_dict(self) -> dict:
        return {
            "execution_success": self.execution_success.value,
            "policy_compliance": self.policy_compliance.value,
            "trust_boundary_compliance": self.trust_boundary_compliance.value,
            "provenance_integrity": self.provenance_integrity.value,
            "verification_result": self.verification_result.value,
            "latency": self.latency.value,
            "resource_efficiency": self.resource_efficiency.value,
            "overall": self.overall.value,
        }


@dataclass
class CausalEvaluation:
    decision_to_execution: CausalAssessment = CausalAssessment.UNKNOWN
    execution_to_outcome: CausalAssessment = CausalAssessment.UNKNOWN
    trace_containment: CausalAssessment = CausalAssessment.UNKNOWN
    overall: CausalAssessment = CausalAssessment.UNKNOWN

    def to_dict(self) -> dict:
        return {
            "decision_to_execution": self.decision_to_execution.value,
            "execution_to_outcome": self.execution_to_outcome.value,
            "trace_containment": self.trace_containment.value,
            "overall": self.overall.value,
        }


@dataclass
class MetaEvaluation:
    evaluation_id: str
    execution_id: str
    trace_id: str
    decision_id: str
    agent_id: str = ""
    model_id: str = ""
    decision_quality: DecisionQuality = field(default_factory=DecisionQuality)
    execution_quality: ExecutionQuality = field(default_factory=ExecutionQuality)
    outcome_quality: OutcomeState = OutcomeState.UNKNOWN
    outcome_record_id: str = ""
    causal_assessment: CausalEvaluation = field(default_factory=CausalEvaluation)
    claims: list[EvaluationClaim] = field(default_factory=list)
    observations: list[str] = field(default_factory=list)
    interpretations: list[str] = field(default_factory=list)
    uncertainties: list[str] = field(default_factory=list)
    conflicts: list[str] = field(default_factory=list)
    validation_artifacts: list[dict] = field(default_factory=list)
    rationale: str = ""
    generated_at: str = ""
    read_only: bool = True

    def to_dict(self) -> dict:
        return {
            "evaluation_id": self.evaluation_id,
            "execution_id": self.execution_id,
            "trace_id": self.trace_id,
            "decision_id": self.decision_id,
            "agent_id": self.agent_id,
            "model_id": self.model_id,
            "decision_quality": self.decision_quality.to_dict(),
            "execution_quality": self.execution_quality.to_dict(),
            "outcome_quality": self.outcome_quality.value,
            "outcome_record_id": self.outcome_record_id,
            "causal_assessment": self.causal_assessment.to_dict(),
            "claims": [c.to_dict() for c in self.claims],
            "observations": self.observations,
            "interpretations": self.interpretations,
            "uncertainties": self.uncertainties,
            "conflicts": self.conflicts,
            "validation_artifacts": self.validation_artifacts,
            "rationale": self.rationale,
            "generated_at": self.generated_at,
            "read_only": self.read_only,
        }


class MetaEvaluator:

    def __init__(self, utr=None, db_path: Optional[Path] = None,
                 graph_state=None, event_bus=None,
                 validation_store=None):
        from features.provenance.resolver import ProvenanceResolver
        self._resolver = ProvenanceResolver(
            utr=utr, db_path=db_path,
            graph_state=graph_state, event_bus=event_bus,
        )
        self._validation_store = validation_store

    def set_utr(self, utr) -> None:
        self._resolver.set_utr(utr)

    def set_db_path(self, db_path: Path) -> None:
        self._resolver.set_db_path(db_path)

    def set_validation_store(self, store) -> None:
        self._validation_store = store

    def _validate_outcome_record_binding(
        self, execution_id: str, outcome_record: Any
    ) -> bool:
        rec_eid = getattr(outcome_record, "execution_id", "")
        if rec_eid and rec_eid != execution_id:
            return False
        return True

    def _verify_outcome_record_integrity(self, outcome_record: Any) -> bool:
        finalized = getattr(outcome_record, "finalized", False)
        if not finalized:
            return True
        verify_fn = getattr(outcome_record, "verify_integrity", None)
        if verify_fn is None:
            return False
        try:
            return bool(verify_fn())
        except Exception:
            return False

    def evaluate(self, execution_id: str,
                 outcome_record: Any = None,
                 mreil_metrics: Any = None) -> MetaEvaluation:
        if outcome_record is not None and not self._validate_outcome_record_binding(execution_id, outcome_record):
            outcome_record = None
        if outcome_record is not None and not self._verify_outcome_record_integrity(outcome_record):
            outcome_record = None
        report = self._resolver.resolve_execution(execution_id)
        return self._evaluate_report(execution_id, report,
                                     outcome_record=outcome_record,
                                     mreil_metrics=mreil_metrics)

    def _evaluate_report(self, execution_id: str,
                         report: ReconstructionReport,
                         outcome_record: Any = None,
                         mreil_metrics: Any = None) -> MetaEvaluation:
        eval_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc).isoformat()

        identity = report.identity
        trace_id = identity.trace_id if identity else ""
        decision_id = identity.decision_id if identity else ""
        exec_rec = report.execution
        agent_id = exec_rec.agent_id if exec_rec else ""
        model_id = exec_rec.model_id if exec_rec else ""

        claims: list[EvaluationClaim] = []
        observations: list[str] = []
        interpretations: list[str] = []
        uncertainties: list[str] = []
        conflicts_list: list[str] = []

        if report.relations:
            for r in report.relations:
                ref = EvidenceRef(
                    source_id=r.source_id,
                    relation_type=r.relation_type.value,
                    status=r.status.value,
                    evidence_source=r.evidence_source,
                    reason=r.reason,
                )
                if r.status in (EvidenceStatus.CONFLICT, EvidenceStatus.MISSING):
                    uncertainties.append(
                        f"{r.relation_type.value}: {r.reason} (status={r.status.value})"
                    )
                if r.status == EvidenceStatus.VERIFIED:
                    observations.append(
                        f"{r.source_id} {r.relation_type.value} {r.target_id} "
                        f"[{r.evidence_source}]"
                    )

        if report.relations:
            for r in report.relations:
                if r.status == EvidenceStatus.CONFLICT:
                    conflicts_list.append(
                        f"CONFLICT: {r.reason}"
                    )

        dq = self._evaluate_decision_quality(report, claims)
        eq = self._evaluate_execution_quality(report, claims, mreil_metrics=mreil_metrics)
        oq, outcome_rec_id = self._evaluate_outcome_quality(
            report, claims, outcome_record=outcome_record
        )
        ca = self._evaluate_causal(report, claims)

        span_id = identity.span_id if identity else ""
        validation_artifacts = self._build_validation_artifacts(
            eval_id, execution_id, trace_id, decision_id, outcome_rec_id,
            dq, eq, oq,
            span_id=span_id, agent_id=agent_id, model_id=model_id,
        )

        rationale_parts = []
        rationale_parts.append(
            f"Decision quality: {dq.overall.value}. "
            f"Execution quality: {eq.overall.value}. "
            f"Outcome quality: {oq.value}."
        )
        if outcome_rec_id:
            rationale_parts.append(f"Outcome record: {outcome_rec_id}.")
        if validation_artifacts:
            rationale_parts.append(f"Validation artifacts: {len(validation_artifacts)}.")
        if conflicts_list:
            rationale_parts.append(f"Conflicts detected: {len(conflicts_list)}.")
        if uncertainties:
            rationale_parts.append(f"Uncertainties: {len(uncertainties)}.")

        return MetaEvaluation(
            evaluation_id=eval_id,
            execution_id=execution_id,
            trace_id=trace_id,
            decision_id=decision_id,
            agent_id=agent_id,
            model_id=model_id,
            decision_quality=dq,
            execution_quality=eq,
            outcome_quality=oq,
            outcome_record_id=outcome_rec_id,
            causal_assessment=ca,
            claims=claims,
            observations=observations,
            interpretations=interpretations,
            uncertainties=uncertainties,
            conflicts=conflicts_list,
            validation_artifacts=validation_artifacts,
            rationale=" ".join(rationale_parts),
            generated_at=now,
            read_only=True,
        )

    def _build_validation_artifacts(
        self, eval_id: str, execution_id: str, trace_id: str,
        decision_id: str, outcome_record_id: str,
        decision_quality: DecisionQuality,
        execution_quality: ExecutionQuality,
        outcome_quality: OutcomeState,
        span_id: str = "",
        agent_id: str = "",
        model_id: str = "",
    ) -> list[dict]:
        from features.execution.evaluation_validation import EvaluationValidation, ValidationResult
        from features.execution.outcome import EvidenceStatus
        overrides = [decision_quality.overall, execution_quality.overall,
                     EvaluationLevel(outcome_quality.value) if outcome_quality.value in ("GOOD", "ACCEPTABLE", "BAD", "UNKNOWN") else EvaluationLevel.UNKNOWN]
        if any(l == EvaluationLevel.BAD for l in overrides):
            v_result = ValidationResult.REFUTED
        elif all(l == EvaluationLevel.GOOD for l in overrides):
            v_result = ValidationResult.CONFIRMED
        elif any(l == EvaluationLevel.UNKNOWN for l in overrides):
            v_result = ValidationResult.INCONCLUSIVE
        else:
            v_result = ValidationResult.PARTIALLY_CONFIRMED

        v = EvaluationValidation(
            evaluation_id=eval_id,
            execution_id=execution_id,
            trace_id=trace_id,
            span_id=span_id,
            decision_id=decision_id,
            agent_id=agent_id,
            model_id=model_id,
            outcome_id=outcome_record_id,
            validation_result=v_result,
            rationale=f"Decision: {decision_quality.overall.value}, "
                      f"Execution: {execution_quality.overall.value}, "
                      f"Outcome: {outcome_quality.value}",
        )
        v.finalize()
        artifact = v.to_dict()
        if self._validation_store is not None:
            try:
                self._validation_store.store(artifact)
            except Exception:
                pass
        return [artifact]

    def _add_claim(self, claims: list[EvaluationClaim], target_id: str,
                   criterion: str, conclusion: str,
                   evidence: list[EvidenceRef],
                   rationale: str = "",
                   uncertainty: str = "",
                   conflicts: list[str] | None = None) -> None:
        evidence_status = EvidenceStatus.MISSING.value
        if evidence:
            from features.provenance.classifier import EvidenceClassifier
            statuses = [EvidenceStatus(e.status) for e in evidence]
            evidence_status = EvidenceClassifier.resolve(statuses).value
        claims.append(EvaluationClaim(
            claim_id=str(uuid.uuid4()),
            target_id=target_id,
            criterion=criterion,
            conclusion=conclusion,
            evidence=evidence,
            evidence_status=evidence_status,
            rationale=rationale,
            uncertainty=uncertainty,
            conflicts=conflicts or [],
        ))

    def _evaluate_decision_quality(
        self, report: ReconstructionReport,
        claims: list[EvaluationClaim],
    ) -> DecisionQuality:
        dq = DecisionQuality()

        gov = report.governance
        completeness = report.completeness
        identity = report.identity
        exec_record = report.execution
        target = identity.execution_id if identity else ""

        if exec_record is None and identity is None:
            for attr in ("authority_compliance", "policy_compliance",
                         "evidence_sufficiency", "provenance_completeness",
                         "decision_consistency"):
                setattr(dq, attr, EvaluationLevel.UNKNOWN)
            self._add_claim(claims, target, "authority_compliance", "UNKNOWN", [],
                            "No execution record available")
            self._add_claim(claims, target, "policy_compliance", "UNKNOWN", [],
                            "No execution record available")
            self._add_claim(claims, target, "evidence_sufficiency", "UNKNOWN", [],
                            "No execution record available")
            self._add_claim(claims, target, "provenance_completeness", "UNKNOWN", [],
                            "No execution record available")
            self._add_claim(claims, target, "decision_consistency", "UNKNOWN", [],
                            "No execution record available")
            dq.overall = EvaluationLevel.UNKNOWN
            return dq

        ev = []
        if gov:
            ev.append(EvidenceRef(
                source_id=gov.decision_id,
                relation_type="AUTHORIZES",
                status=EvidenceStatus.VERIFIED.value,
                evidence_source="decisions_db",
                reason=f"Decision {gov.decision_id} has type={gov.decision_type}",
            ))
            if gov.decision_type == "governance":
                dq.authority_compliance = EvaluationLevel.GOOD
            else:
                dq.authority_compliance = EvaluationLevel.ACCEPTABLE
        else:
            dq.authority_compliance = EvaluationLevel.UNKNOWN
        self._add_claim(claims, target,
                        "authority_compliance", dq.authority_compliance.value, ev)

        ev2 = []
        if gov and gov.governance_action:
            ev2.append(EvidenceRef(
                source_id=gov.decision_id,
                relation_type="AUTHORIZES",
                status=EvidenceStatus.VERIFIED.value,
                evidence_source="decisions_db",
                reason=f"Governance action: {gov.governance_action}",
            ))
            if gov.governance_action == "allow":
                dq.policy_compliance = EvaluationLevel.GOOD
            elif gov.governance_action == "block":
                dq.policy_compliance = EvaluationLevel.BAD
            else:
                dq.policy_compliance = EvaluationLevel.ACCEPTABLE
        else:
            dq.policy_compliance = EvaluationLevel.UNKNOWN
        self._add_claim(claims, target,
                        "policy_compliance", dq.policy_compliance.value, ev2)

        ev3 = []
        total = completeness.verified + completeness.inferred + completeness.missing + completeness.conflict
        if total > 0:
            ev3.append(EvidenceRef(
                source_id="reconstruction",
                relation_type="CONTAINS",
                status=EvidenceStatus.VERIFIED.value,
                evidence_source="reconstruction_report",
                reason=f"Verified {completeness.verified}/{total} relations",
            ))
            if completeness.missing > 0 or completeness.conflict > 0:
                if completeness.verified >= total * 0.5:
                    dq.evidence_sufficiency = EvaluationLevel.ACCEPTABLE
                else:
                    dq.evidence_sufficiency = EvaluationLevel.BAD
            else:
                dq.evidence_sufficiency = EvaluationLevel.GOOD
        else:
            dq.evidence_sufficiency = EvaluationLevel.UNKNOWN
        self._add_claim(claims, target,
                        "evidence_sufficiency", dq.evidence_sufficiency.value, ev3)

        ev4 = []
        if total > 0:
            ev4.append(EvidenceRef(
                source_id="reconstruction",
                relation_type="CONTAINS",
                status=EvidenceStatus.VERIFIED.value,
                evidence_source="completeness_summary",
                reason=f"{completeness.verified} verified, {completeness.inferred} inferred, "
                       f"{completeness.missing} missing, {completeness.conflict} conflict",
            ))
            if completeness.missing == 0 and completeness.conflict == 0:
                dq.provenance_completeness = EvaluationLevel.GOOD
            elif completeness.missing <= total * 0.3:
                dq.provenance_completeness = EvaluationLevel.ACCEPTABLE
            else:
                dq.provenance_completeness = EvaluationLevel.BAD
        else:
            dq.provenance_completeness = EvaluationLevel.UNKNOWN
        self._add_claim(claims, target,
                        "provenance_completeness", dq.provenance_completeness.value, ev4)

        ev5 = []
        integ = report.integrity
        integ_fields = [
            ("execution_id_consistent", integ.execution_id_consistent),
            ("trace_id_consistent", integ.trace_id_consistent),
            ("span_id_consistent", integ.span_id_consistent),
            ("decision_id_consistent", integ.decision_id_consistent),
            ("receipt_integrity_valid", integ.receipt_integrity_valid),
            ("verification_consistent", integ.verification_consistent),
            ("decision_db_consistent", integ.decision_db_consistent),
            ("no_orphan_execution", integ.no_orphan_execution),
            ("no_orphan_decision", integ.no_orphan_decision),
            ("no_cross_trace", integ.no_cross_trace),
        ]
        has_conflict = any(s == EvidenceStatus.CONFLICT for _, s in integ_fields)
        all_good = all(s in (EvidenceStatus.VERIFIED, EvidenceStatus.INFERRED) for _, s in integ_fields)
        if has_conflict:
            dq.decision_consistency = EvaluationLevel.BAD
            ev5.append(EvidenceRef(
                source_id="integrity",
                relation_type="CONFLICT",
                status=EvidenceStatus.CONFLICT.value,
                evidence_source="integrity_status",
                reason="Integrity check found conflicts",
            ))
        elif all_good:
            dq.decision_consistency = EvaluationLevel.GOOD
            ev5.append(EvidenceRef(
                source_id="integrity",
                relation_type="CAUSES",
                status=EvidenceStatus.VERIFIED.value,
                evidence_source="integrity_status",
                reason="All integrity fields consistent",
            ))
        else:
            dq.decision_consistency = EvaluationLevel.ACCEPTABLE
            ev5.append(EvidenceRef(
                source_id="integrity",
                relation_type="CONTAINS",
                status=EvidenceStatus.INFERRED.value,
                evidence_source="integrity_status",
                reason="Some integrity fields unresolved",
            ))
        self._add_claim(claims, target,
                        "decision_consistency", dq.decision_consistency.value, ev5)

        levels = [dq.authority_compliance, dq.policy_compliance,
                  dq.evidence_sufficiency, dq.provenance_completeness,
                  dq.decision_consistency]
        if any(l == EvaluationLevel.BAD for l in levels):
            dq.overall = EvaluationLevel.BAD
        elif all(l == EvaluationLevel.GOOD for l in levels):
            dq.overall = EvaluationLevel.GOOD
        elif any(l == EvaluationLevel.UNKNOWN for l in levels):
            dq.overall = EvaluationLevel.ACCEPTABLE
        else:
            dq.overall = EvaluationLevel.ACCEPTABLE

        return dq

    def _evaluate_execution_quality(
        self, report: ReconstructionReport,
        claims: list[EvaluationClaim],
        mreil_metrics: Any = None,
    ) -> ExecutionQuality:
        eq = ExecutionQuality()
        exec_rec = report.execution
        identity = report.identity
        completeness = report.completeness

        ev = []
        if exec_rec is not None:
            ev.append(EvidenceRef(
                source_id=exec_rec.execution_id,
                relation_type="CAUSES",
                status=EvidenceStatus.VERIFIED.value,
                evidence_source="utr_execution_store",
                reason=f"Execution success={exec_rec.success}",
            ))
            if exec_rec.success:
                eq.execution_success = EvaluationLevel.GOOD
            else:
                eq.execution_success = EvaluationLevel.BAD
        else:
            eq.execution_success = EvaluationLevel.UNKNOWN
        self._add_claim(claims, identity.execution_id if identity else "",
                        "execution_success", eq.execution_success.value, ev)

        ev2 = []
        gov = report.governance
        if gov and gov.governance_action == "allow":
            eq.policy_compliance = EvaluationLevel.GOOD
            ev2.append(EvidenceRef(
                source_id=gov.decision_id,
                relation_type="AUTHORIZES",
                status=EvidenceStatus.VERIFIED.value,
                evidence_source="decisions_db",
                reason="Governance allowed execution",
            ))
        elif gov and gov.governance_action == "block":
            eq.policy_compliance = EvaluationLevel.BAD
        else:
            eq.policy_compliance = EvaluationLevel.UNKNOWN
        self._add_claim(claims, identity.execution_id if identity else "",
                        "execution_policy_compliance", eq.policy_compliance.value, ev2)

        ev3 = []
        if completeness.conflict == 0:
            eq.trust_boundary_compliance = EvaluationLevel.GOOD
            ev3.append(EvidenceRef(
                source_id="reconstruction",
                relation_type="CONTAINS",
                status=EvidenceStatus.VERIFIED.value,
                evidence_source="completeness_summary",
                reason="No conflicts detected",
            ))
        else:
            eq.trust_boundary_compliance = EvaluationLevel.BAD
            ev3.append(EvidenceRef(
                source_id="reconstruction",
                relation_type="CONFLICT",
                status=EvidenceStatus.CONFLICT.value,
                evidence_source="completeness_summary",
                reason=f"{completeness.conflict} conflict(s) detected",
            ))
        self._add_claim(claims, identity.execution_id if identity else "",
                        "trust_boundary_compliance", eq.trust_boundary_compliance.value, ev3)

        ev4 = []
        if exec_rec is not None:
            if exec_rec.integrity_valid:
                eq.provenance_integrity = EvaluationLevel.GOOD
            else:
                eq.provenance_integrity = EvaluationLevel.BAD
            ev4.append(EvidenceRef(
                source_id=exec_rec.receipt_id,
                relation_type="VERIFIES",
                status=EvidenceStatus.VERIFIED.value if exec_rec.integrity_valid else EvidenceStatus.CONFLICT.value,
                evidence_source="receipt_integrity",
                reason=f"Integrity valid={exec_rec.integrity_valid}",
            ))
        else:
            eq.provenance_integrity = EvaluationLevel.UNKNOWN
        self._add_claim(claims, identity.execution_id if identity else "",
                        "provenance_integrity", eq.provenance_integrity.value, ev4)

        ev5 = []
        verif = report.verification
        if verif is not None:
            ev5.append(EvidenceRef(
                source_id=verif.verification_id,
                relation_type="VERIFIES",
                status=EvidenceStatus.VERIFIED.value,
                evidence_source="utr_verification_store",
                reason=f"Verification status: {verif.status}",
            ))
            if verif.status in ("verified", "passed", "ok"):
                eq.verification_result = EvaluationLevel.GOOD
            elif verif.status in ("failed", "rejected"):
                eq.verification_result = EvaluationLevel.BAD
            else:
                eq.verification_result = EvaluationLevel.ACCEPTABLE
        else:
            eq.verification_result = EvaluationLevel.UNKNOWN
        self._add_claim(claims, identity.execution_id if identity else "",
                        "verification_result", eq.verification_result.value, ev5)

        ev6 = []
        if exec_rec is not None and exec_rec.execution_time > 0:
            if exec_rec.execution_time < 1.0:
                eq.latency = EvaluationLevel.GOOD
            elif exec_rec.execution_time < 5.0:
                eq.latency = EvaluationLevel.ACCEPTABLE
            else:
                eq.latency = EvaluationLevel.BAD
            ev6.append(EvidenceRef(
                source_id=exec_rec.execution_id,
                relation_type="PRODUCES",
                status=EvidenceStatus.VERIFIED.value,
                evidence_source="execution_record",
                reason=f"Execution time: {exec_rec.execution_time}s",
            ))
        else:
            eq.latency = EvaluationLevel.UNKNOWN
        self._add_claim(claims, identity.execution_id if identity else "",
                        "latency", eq.latency.value, ev6)

        ev7 = []
        if mreil_metrics is not None:
            resources = getattr(mreil_metrics, "resources", None)
            if resources is not None:
                latency = getattr(resources, "latency", 0.0)
                token_usage = getattr(resources, "token_usage", 0)
                cpu_time = getattr(resources, "cpu_time", 0.0)
                if latency < 1.0 and token_usage < 1000 and cpu_time < 0.5:
                    eq.resource_efficiency = EvaluationLevel.GOOD
                elif latency < 5.0:
                    eq.resource_efficiency = EvaluationLevel.ACCEPTABLE
                else:
                    eq.resource_efficiency = EvaluationLevel.BAD
                ev7.append(EvidenceRef(
                    source_id="mreil",
                    relation_type="PRODUCES",
                    status=EvidenceStatus.VERIFIED.value,
                    evidence_source="mreil_metrics",
                    reason=f"Resource metrics: latency={latency}s, tokens={token_usage}, cpu={cpu_time}s",
                ))
            else:
                eq.resource_efficiency = EvaluationLevel.UNKNOWN
        elif exec_rec is not None:
            if exec_rec.execution_time < 1.0:
                eq.resource_efficiency = EvaluationLevel.ACCEPTABLE
            else:
                eq.resource_efficiency = EvaluationLevel.UNKNOWN
            ev7.append(EvidenceRef(
                source_id=exec_rec.execution_id,
                relation_type="PRODUCES",
                status=EvidenceStatus.INFERRED.value,
                evidence_source="execution_record",
                reason="No MREIL metrics available — using execution_time as proxy",
            ))
        else:
            eq.resource_efficiency = EvaluationLevel.UNKNOWN
        self._add_claim(claims, identity.execution_id if identity else "",
                        "resource_efficiency", eq.resource_efficiency.value, ev7)

        levels = [eq.execution_success, eq.policy_compliance,
                  eq.trust_boundary_compliance, eq.provenance_integrity,
                  eq.verification_result, eq.latency]
        if any(l == EvaluationLevel.BAD for l in levels):
            eq.overall = EvaluationLevel.BAD
        elif all(l == EvaluationLevel.GOOD for l in levels):
            eq.overall = EvaluationLevel.GOOD
        elif any(l == EvaluationLevel.UNKNOWN for l in levels):
            eq.overall = EvaluationLevel.ACCEPTABLE
        else:
            eq.overall = EvaluationLevel.ACCEPTABLE

        return eq

    def _evaluate_outcome_quality(
        self, report: ReconstructionReport,
        claims: list[EvaluationClaim],
        outcome_record: Any = None,
    ) -> tuple[OutcomeState, str]:
        from features.execution.outcome import OutcomeRecord as OR
        identity = report.identity
        target = identity.execution_id if identity else ""
        exec_rec = report.execution
        verif = report.verification

        outcome_rec_id = ""
        if outcome_record is not None:
            outcome_rec_id = getattr(outcome_record, "outcome_id", "")

        # RULE 1: Technical execution success does NOT imply outcome success.
        # RULE 2: OutcomeRecord is NOT independently verified without independent evidence.
        # Outcome quality depends on actual outcome evidence, not receipt.success.

        if isinstance(outcome_record, OR):
            return self._evaluate_from_outcome_record(
                target, claims, outcome_record, outcome_rec_id
            )

        if outcome_record is not None:
            or_status = getattr(outcome_record, "outcome_status", None)
            or_verified = getattr(outcome_record, "verified_outcome", None)
            or_evidence_status = getattr(outcome_record, "evidence_status", None)

            ev_internal = []
            if or_evidence_status:
                ev_internal.append(EvidenceRef(
                    source_id=outcome_rec_id,
                    relation_type="CAUSES",
                    status=or_evidence_status.value
                    if hasattr(or_evidence_status, "value") else str(or_evidence_status),
                    evidence_source=getattr(outcome_record, "source", "outcome_record"),
                    reason=f"OutcomeRecord evidence_status={or_evidence_status}",
                ))

            if or_evidence_status and hasattr(or_evidence_status, "value"):
                if or_evidence_status == EvidenceStatus.VERIFIED:
                    if or_verified in ("SUCCESS", OutcomeState.SUCCESS.value):
                        self._add_claim(claims, target, "outcome_quality",
                                        OutcomeState.SUCCESS.value, ev_internal,
                                        "Independent evidence confirms outcome success")
                        return OutcomeState.SUCCESS, outcome_rec_id
                    elif or_verified in ("FAILURE", OutcomeState.FAILURE.value):
                        self._add_claim(claims, target, "outcome_quality",
                                        OutcomeState.FAILURE.value, ev_internal,
                                        "Independent evidence confirms outcome failure")
                        return OutcomeState.FAILURE, outcome_rec_id
                    elif or_verified in ("PARTIAL", OutcomeState.PARTIAL.value):
                        self._add_claim(claims, target, "outcome_quality",
                                        OutcomeState.PARTIAL.value, ev_internal,
                                        "Independent evidence confirms partial outcome")
                        return OutcomeState.PARTIAL, outcome_rec_id

                if or_evidence_status == EvidenceStatus.INFERRED:
                    self._add_claim(claims, target, "outcome_quality",
                                    OutcomeState.PARTIAL.value, ev_internal,
                                    "Outcome evidence is inferred, not independently verified",
                                    uncertainty="Outcome from non-independent source")
                    return OutcomeState.PARTIAL, outcome_rec_id

            self._add_claim(claims, target, "outcome_quality",
                            OutcomeState.UNKNOWN.value, ev_internal,
                            uncertainty="No reliable outcome evidence")
            return OutcomeState.UNKNOWN, outcome_rec_id

        # Without an OutcomeRecord: outcome quality is UNKNOWN.
        # RULE 1: Technical success alone does NOT establish outcome.
        self._add_claim(claims, target, "outcome_quality",
                        OutcomeState.UNKNOWN.value, [],
                        "No OutcomeRecord available — cannot assess outcome quality",
                        uncertainty="No outcome evidence exists")
        return OutcomeState.UNKNOWN, outcome_rec_id

    def _evaluate_from_outcome_record(
        self, target: str, claims: list[EvaluationClaim],
        outcome_record: "OutcomeRecord",
        outcome_rec_id: str,
    ) -> tuple[OutcomeState, str]:
        from features.execution.outcome import OutcomeStatus
        ev = []
        evidence_status = getattr(outcome_record, "evidence_status", None)
        if evidence_status is not None:
            ev.append(EvidenceRef(
                source_id=outcome_rec_id,
                relation_type="CAUSES",
                status=str(evidence_status.value if hasattr(evidence_status, "value") else evidence_status),
                evidence_source=getattr(outcome_record, "source", "outcome_record"),
                reason=f"OutcomeRecord evidence_status={evidence_status}",
            ))
        outcome_status = getattr(outcome_record, "outcome_status", None)
        verified_outcome = getattr(outcome_record, "verified_outcome", None)

        if evidence_status and hasattr(evidence_status, "value"):
            if evidence_status == EvidenceStatus.VERIFIED:
                if verified_outcome == OutcomeStatus.SUCCESS:
                    self._add_claim(claims, target, "outcome_quality",
                                    OutcomeState.SUCCESS.value, ev,
                                    "Independent evidence confirms outcome success")
                    return OutcomeState.SUCCESS, outcome_rec_id
                elif verified_outcome == OutcomeStatus.FAILURE:
                    self._add_claim(claims, target, "outcome_quality",
                                    OutcomeState.FAILURE.value, ev,
                                    "Independent evidence confirms outcome failure")
                    return OutcomeState.FAILURE, outcome_rec_id
                elif verified_outcome == OutcomeStatus.PARTIAL:
                    self._add_claim(claims, target, "outcome_quality",
                                    OutcomeState.PARTIAL.value, ev,
                                    "Independent evidence confirms partial outcome")
                    return OutcomeState.PARTIAL, outcome_rec_id
            elif evidence_status == EvidenceStatus.INFERRED:
                self._add_claim(claims, target, "outcome_quality",
                                OutcomeState.PARTIAL.value, ev,
                                "Outcome evidence is inferred, not independently verified",
                                uncertainty="Outcome from non-independent source")
                return OutcomeState.PARTIAL, outcome_rec_id
            elif evidence_status == EvidenceStatus.MISSING:
                self._add_claim(claims, target, "outcome_quality",
                                OutcomeState.UNKNOWN.value, ev,
                                uncertainty="No outcome evidence available")
                return OutcomeState.UNKNOWN, outcome_rec_id

        self._add_claim(claims, target, "outcome_quality",
                        OutcomeState.UNKNOWN.value, ev,
                        uncertainty="No reliable outcome evidence")
        return OutcomeState.UNKNOWN, outcome_rec_id

    def _evaluate_causal(
        self, report: ReconstructionReport,
        claims: list[EvaluationClaim],
    ) -> CausalEvaluation:
        ca = CausalEvaluation()
        identity = report.identity
        relations = report.relations

        for r in relations:
            if r.relation_type == RelationType.AUTHORIZES and r.status == EvidenceStatus.VERIFIED:
                ca.decision_to_execution = CausalAssessment.CAUSALLY_SUPPORTED
                break
            elif r.relation_type == RelationType.AUTHORIZES:
                ca.decision_to_execution = CausalAssessment.INFERRED

        ev_d2e = []
        if ca.decision_to_execution != CausalAssessment.UNKNOWN:
            ev_d2e.append(EvidenceRef(
                source_id=identity.decision_id if identity else "",
                relation_type="AUTHORIZES",
                status=EvidenceStatus.VERIFIED.value,
                evidence_source="decisions_db",
                reason=f"Causal assessment: {ca.decision_to_execution.value}",
            ))
        self._add_claim(claims, identity.execution_id if identity else "",
                        "decision_to_execution_causal", ca.decision_to_execution.value, ev_d2e)

        exec_rec = report.execution
        verif = report.verification
        if exec_rec is not None and verif is not None:
            if verif.status in ("verified", "passed", "ok"):
                ca.execution_to_outcome = CausalAssessment.CAUSALLY_SUPPORTED
            else:
                ca.execution_to_outcome = CausalAssessment.CORRELATED
        elif exec_rec is not None:
            ca.execution_to_outcome = CausalAssessment.TEMPORALLY_ASSOCIATED
        else:
            ca.execution_to_outcome = CausalAssessment.UNKNOWN

        ev_e2o = []
        if ca.execution_to_outcome != CausalAssessment.UNKNOWN:
            ev_e2o.append(EvidenceRef(
                source_id=identity.execution_id if identity else "",
                relation_type="CAUSES",
                status=EvidenceStatus.VERIFIED.value,
                evidence_source="execution_record",
                reason=f"Causal assessment: {ca.execution_to_outcome.value}",
            ))
        self._add_claim(claims, identity.execution_id if identity else "",
                        "execution_to_outcome_causal", ca.execution_to_outcome.value, ev_e2o)

        for r in relations:
            if r.relation_type == RelationType.CONTAINS and r.status == EvidenceStatus.VERIFIED:
                ca.trace_containment = CausalAssessment.CAUSALLY_SUPPORTED
                break
            elif r.relation_type == RelationType.CONTAINS:
                ca.trace_containment = CausalAssessment.INFERRED

        if ca.trace_containment == CausalAssessment.UNKNOWN and identity and identity.trace_id:
            ca.trace_containment = CausalAssessment.INFERRED

        ev_tc = []
        if ca.trace_containment != CausalAssessment.UNKNOWN:
            ev_tc.append(EvidenceRef(
                source_id=identity.trace_id if identity else "",
                relation_type="CONTAINS",
                status=EvidenceStatus.VERIFIED.value,
                evidence_source="receipt + decisions_db",
                reason=f"Causal assessment: {ca.trace_containment.value}",
            ))
        self._add_claim(claims, identity.execution_id if identity else "",
                        "trace_containment_causal", ca.trace_containment.value, ev_tc)

        levels = [ca.decision_to_execution, ca.execution_to_outcome, ca.trace_containment]
        if any(l == CausalAssessment.CAUSALLY_SUPPORTED for l in levels):
            ca.overall = CausalAssessment.CAUSALLY_SUPPORTED
        elif any(l in (CausalAssessment.TEMPORALLY_ASSOCIATED, CausalAssessment.CORRELATED) for l in levels):
            ca.overall = CausalAssessment.CORRELATED
        elif any(l == CausalAssessment.INFERRED for l in levels):
            ca.overall = CausalAssessment.INFERRED
        else:
            ca.overall = CausalAssessment.UNKNOWN

        return ca
