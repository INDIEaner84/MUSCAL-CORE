import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from features.provenance.classifier import EvidenceClassifier
from features.provenance.decision_writer import get_decision, get_decisions_by_trace
from features.provenance.models import (
    CausalGraph,
    CompletenessSummary,
    EvidenceStatus,
    ExecutionRecord,
    GovernanceRecord,
    GraphEdgeRecord,
    GraphNodeRecord,
    IdentityRecord,
    IntegrityStatus,
    ReconstructionReport,
    Relation,
    RelationType,
    SemanticTruthStatus,
    VerificationRecord,
)

log = logging.getLogger("muscal.provenance.resolver")


class ProvenanceResolver:

    def __init__(self, utr=None, db_path: Optional[Path] = None,
                 graph_state=None, event_bus=None):
        self._utr = utr
        self._db_path = db_path
        self._graph_state = graph_state
        self._event_bus = event_bus

    def set_utr(self, utr) -> None:
        self._utr = utr

    def set_db_path(self, db_path: Path) -> None:
        self._db_path = db_path

    def _get_execution_store(self) -> dict:
        if self._utr is None:
            return {}
        try:
            return self._utr._execution_store
        except AttributeError:
            return {}

    def _get_receipt_store(self) -> dict:
        if self._utr is None:
            return {}
        try:
            return self._utr._receipt_store
        except AttributeError:
            return {}

    def _get_verification_store(self) -> dict:
        if self._utr is None:
            return {}
        try:
            return self._utr._verification_store
        except AttributeError:
            return {}

    def _get_expected_state_store(self) -> dict:
        if self._utr is None:
            return {}
        try:
            return self._utr._expected_state_store
        except AttributeError:
            return {}

    def _locate_execution(self, execution_id: str) -> Optional[dict]:
        store = self._get_execution_store()
        receipt = store.get(execution_id)
        if receipt is not None:
            return {
                "source": "utr_execution_store",
                "receipt": receipt,
            }
        return None

    def _locate_receipt_by_id(self, receipt_id: str) -> Optional[dict]:
        store = self._get_receipt_store()
        return store.get(receipt_id)

    def _verify_receipt_integrity(self, receipt) -> tuple[bool, str]:
        if not hasattr(receipt, "finalized") or not receipt.finalized:
            return False, "receipt not finalized"
        try:
            valid = receipt.verify_integrity()
            if valid:
                return True, "integrity hash verified"
            return False, "integrity hash mismatch"
        except Exception as e:
            return False, f"integrity check error: {e}"

    def _build_execution_record(self, receipt, integrity_valid: bool) -> ExecutionRecord:
        return ExecutionRecord(
            execution_id=getattr(receipt, "execution_id", ""),
            tool_name=getattr(receipt, "tool_name", ""),
            success=getattr(receipt, "success", False),
            execution_time=getattr(receipt, "execution_time", 0.0),
            correlation_id=getattr(receipt, "correlation_id", ""),
            trace_id=getattr(receipt, "trace_id", ""),
            span_id=getattr(receipt, "span_id", ""),
            decision_id=getattr(receipt, "decision_id", ""),
            receipt_id=getattr(receipt, "receipt_id", ""),
            integrity_hash=getattr(receipt, "integrity_hash", ""),
            integrity_valid=integrity_valid,
            finalized=getattr(receipt, "finalized", False),
            agent_id=getattr(receipt, "agent_id", ""),
            model_id=getattr(receipt, "model_id", ""),
        )

    def _build_identity_record(self, exec_rec: ExecutionRecord,
                               verif_rec: Optional[VerificationRecord]) -> IdentityRecord:
        return IdentityRecord(
            execution_id=exec_rec.execution_id,
            trace_id=exec_rec.trace_id,
            span_id=exec_rec.span_id,
            decision_id=exec_rec.decision_id,
            receipt_id=exec_rec.receipt_id,
            verification_id=verif_rec.verification_id if verif_rec else "",
        )

    def _resolve_governance(self, decision_id: str) -> tuple[Optional[GovernanceRecord], EvidenceStatus]:
        if not decision_id or self._db_path is None:
            return None, EvidenceStatus.MISSING
        try:
            dec = get_decision(self._db_path, decision_id)
            if dec is None:
                return None, EvidenceStatus.MISSING
            return GovernanceRecord(
                decision_id=dec.get("id", ""),
                governance_action=dec.get("governance_action", ""),
                decision_status=dec.get("decision_status", "active"),
                decision_type=dec.get("decision_type", "governance"),
                trace_id=dec.get("trace_id", ""),
                span_id=dec.get("span_id", ""),
                reasoning=dec.get("reasoning", ""),
                made_at=dec.get("made_at", ""),
            ), EvidenceStatus.VERIFIED
        except Exception as e:
            log.warning("Failed to resolve decision %s: %s", decision_id, e)
            return None, EvidenceStatus.MISSING

    def _resolve_trace_decisions(self, trace_id: str) -> tuple[list[GovernanceRecord], EvidenceStatus]:
        if not trace_id or self._db_path is None:
            return [], EvidenceStatus.MISSING
        try:
            rows = get_decisions_by_trace(self._db_path, trace_id)
            records = []
            for r in rows:
                records.append(GovernanceRecord(
                    decision_id=r.get("id", ""),
                    governance_action=r.get("governance_action", ""),
                    decision_status=r.get("decision_status", "active"),
                    decision_type=r.get("decision_type", "governance"),
                    trace_id=r.get("trace_id", ""),
                    span_id=r.get("span_id", ""),
                    reasoning=r.get("reasoning", ""),
                    made_at=r.get("made_at", ""),
                ))
            if records:
                return records, EvidenceStatus.VERIFIED
            return [], EvidenceStatus.INFERRED
        except Exception as e:
            log.warning("Failed to resolve trace %s: %s", trace_id, e)
            return [], EvidenceStatus.MISSING

    def _resolve_verification(self, execution_id: str) -> tuple[Optional[VerificationRecord], EvidenceStatus]:
        store = self._get_verification_store()
        for vr in store.values():
            if hasattr(vr, "execution_id") and vr.execution_id == execution_id:
                return VerificationRecord(
                    verification_id=getattr(vr, "verification_id", ""),
                    execution_id=getattr(vr, "execution_id", ""),
                    receipt_id=getattr(vr, "receipt_id", ""),
                    verifier_id=getattr(vr, "verifier_id", ""),
                    status=getattr(vr, "status", "pending"),
                    decision_id=getattr(vr, "decision_id", ""),
                ), EvidenceStatus.VERIFIED
        return None, EvidenceStatus.MISSING

    def _build_graph(self, records: dict) -> CausalGraph:
        graph = CausalGraph()
        identity = records.get("identity")
        governance = records.get("governance")
        execution = records.get("execution")
        verification = records.get("verification")

        if identity:
            graph.nodes.append(GraphNodeRecord(
                node_id=identity.execution_id, node_type="execution",
                payload={}, timestamp=0.0,
            ))
            graph.nodes.append(GraphNodeRecord(
                node_id=identity.trace_id, node_type="trace",
                payload={}, timestamp=0.0,
            ))
            graph.nodes.append(GraphNodeRecord(
                node_id=identity.span_id, node_type="span",
                payload={}, timestamp=0.0,
            ))
            if identity.decision_id:
                graph.nodes.append(GraphNodeRecord(
                    node_id=identity.decision_id, node_type="decision",
                    payload={}, timestamp=0.0,
                ))

        if governance and governance.decision_id:
            graph.nodes.append(GraphNodeRecord(
                node_id=governance.decision_id, node_type="governance_decision",
                payload={"action": governance.governance_action,
                         "status": governance.decision_status},
                timestamp=0.0,
            ))

        if identity:
            graph.edges.append(GraphEdgeRecord(
                source_id=identity.trace_id, target_id=identity.span_id,
                edge_type="CONTAINS", payload={},
            ))
            graph.edges.append(GraphEdgeRecord(
                source_id=identity.span_id, target_id=identity.execution_id,
                edge_type="CAUSES", payload={},
            ))
            if identity.decision_id and governance:
                graph.edges.append(GraphEdgeRecord(
                    source_id=identity.decision_id, target_id=identity.execution_id,
                    edge_type="AUTHORIZES", payload={},
                ))

        if verification:
            graph.nodes.append(GraphNodeRecord(
                node_id=verification.verification_id, node_type="verification",
                payload={"status": verification.status}, timestamp=0.0,
            ))
            graph.edges.append(GraphEdgeRecord(
                source_id=verification.verification_id,
                target_id=identity.execution_id if identity else "",
                edge_type="VERIFIES", payload={},
            ))

        return graph

    def _detect_retries(self, exec_rec: ExecutionRecord) -> list[Relation]:
        store = self._get_execution_store()
        relations: list[Relation] = []
        same_trace = []
        for eid, receipt in store.items():
            if eid == exec_rec.execution_id:
                continue
            tid = getattr(receipt, "trace_id", "")
            if tid and tid == exec_rec.trace_id:
                same_trace.append((eid, receipt))
        if same_trace:
            sorted_retries = sorted(same_trace, key=lambda x: getattr(x[1], "execution_time", 0))
            for eid, _ in sorted_retries:
                relations.append(Relation(
                    source_id=exec_rec.execution_id,
                    relation_type=RelationType.RETRIES,
                    target_id=eid,
                    status=EvidenceStatus.INFERRED,
                    evidence_source="utr_execution_store",
                    reason=f"Same trace_id '{exec_rec.trace_id}' → retry relationship",
                ))
        return relations

    def resolve_execution(self, execution_id: str) -> ReconstructionReport:
        report = ReconstructionReport()
        relations: list[Relation] = []

        located = self._locate_execution(execution_id)

        if located is None:
            rel = Relation(
                source_id=execution_id, relation_type=RelationType.CAUSES,
                target_id="execution_context",
                status=EvidenceStatus.MISSING,
                evidence_source="all_sources",
                reason=f"execution_id '{execution_id}' not found in any data source",
            )
            relations.append(rel)
            report.relations = relations
            report.completeness.missing = 1
            report.semantic_truth = SemanticTruthStatus(
                provenance_integrity=EvidenceStatus.MISSING,
                semantic_truth="NOT ESTABLISHED",
                reason="Execution record not found — cannot assess",
            )
            return report

        receipt = located["receipt"]
        integrity_valid, integrity_reason = self._verify_receipt_integrity(receipt)

        class_integrity, _ = EvidenceClassifier.classify_integrity(
            getattr(receipt, "finalized", False), integrity_valid
        )
        report.integrity.receipt_integrity_valid = class_integrity

        exec_rec = self._build_execution_record(receipt, integrity_valid)
        report.execution = exec_rec

        verif_rec, verif_status = self._resolve_verification(execution_id)
        report.verification = verif_rec
        report.integrity.verification_consistent = verif_status

        identity = self._build_identity_record(exec_rec, verif_rec)
        report.identity = identity

        gov_rec, gov_status = self._resolve_governance(exec_rec.decision_id)
        report.governance = gov_rec

        trace_decisions, trace_status = self._resolve_trace_decisions(exec_rec.trace_id)
        report.integrity.decision_db_consistent = trace_status

        dec_link_status, dec_link_reason = EvidenceClassifier.classify_decision_link(
            exec_rec.decision_id,
            gov_rec.decision_id if gov_rec else None,
        )
        trace_link_status, trace_link_reason = EvidenceClassifier.classify_trace_link(
            exec_rec.trace_id,
            [d.decision_id for d in trace_decisions],
        )

        relations.append(Relation(
            source_id=exec_rec.execution_id,
            relation_type=RelationType.CAUSES,
            target_id=exec_rec.receipt_id,
            status=EvidenceStatus.VERIFIED if integrity_valid else EvidenceStatus.INFERRED,
            evidence_source="utr_execution_store",
            reason="execution_id → receipt from in-memory store",
        ))

        relations.append(Relation(
            source_id=exec_rec.trace_id,
            relation_type=RelationType.CONTAINS,
            target_id=exec_rec.execution_id,
            status=trace_link_status,
            evidence_source="receipt + decisions_db",
            reason=trace_link_reason,
        ))

        relations.append(Relation(
            source_id=exec_rec.decision_id if exec_rec.decision_id else execution_id,
            relation_type=RelationType.AUTHORIZES,
            target_id=exec_rec.execution_id,
            status=dec_link_status,
            evidence_source="receipt + decisions_db",
            reason=dec_link_reason,
        ))

        if verif_rec:
            relations.append(Relation(
                source_id=verif_rec.verification_id,
                relation_type=RelationType.VERIFIES,
                target_id=exec_rec.execution_id,
                status=verif_status,
                evidence_source="utr_verification_store",
                reason="verification result from in-memory store",
            ))

        for d in trace_decisions:
            relations.append(Relation(
                source_id=d.decision_id,
                relation_type=RelationType.CORRELATES_WITH,
                target_id=exec_rec.trace_id,
                status=trace_status,
                evidence_source="decisions_db",
                reason=f"trace_id '{exec_rec.trace_id}' → decision '{d.decision_id}' in DB",
            ))

        if exec_rec.trace_id:
            retry_relations = self._detect_retries(exec_rec)
            relations.extend(retry_relations)

        report.relations = relations
        report.causal_graph = self._build_graph({
            "identity": identity,
            "governance": gov_rec,
            "execution": exec_rec,
            "verification": verif_rec,
        })

        for r in relations:
            if r.status == EvidenceStatus.VERIFIED:
                report.completeness.verified += 1
            elif r.status == EvidenceStatus.INFERRED:
                report.completeness.inferred += 1
            elif r.status == EvidenceStatus.MISSING:
                report.completeness.missing += 1
            elif r.status == EvidenceStatus.CONFLICT:
                report.completeness.conflict += 1

        has_conflict = any(r.status == EvidenceStatus.CONFLICT for r in relations)
        has_verified = any(r.status == EvidenceStatus.VERIFIED for r in relations)
        if has_conflict:
            report.semantic_truth = SemanticTruthStatus(
                provenance_integrity=EvidenceStatus.CONFLICT,
                semantic_truth="NOT ESTABLISHED",
                reason="Provenance chain has conflicts — cannot assess semantic truth",
            )
        elif has_verified:
            report.semantic_truth = SemanticTruthStatus(
                provenance_integrity=EvidenceStatus.VERIFIED,
                semantic_truth="NOT ESTABLISHED",
                reason="Provenance chain is internally consistent, but correctness of claims is separate",
            )
        else:
            report.semantic_truth = SemanticTruthStatus(
                provenance_integrity=EvidenceStatus.INFERRED,
                semantic_truth="NOT ESTABLISHED",
                reason="Insufficient verified evidence to establish semantic truth",
            )

        return report

    def reconstruct_execution(self, execution_id: str) -> ReconstructionReport:
        return self.resolve_execution(execution_id)

    def inspect_provenance(self, execution_id: str) -> dict:
        report = self.resolve_execution(execution_id)
        return report.to_dict()

    def validate_provenance(self, execution_id: str) -> dict:
        report = self.resolve_execution(execution_id)

        has_conflict = any(r.status == EvidenceStatus.CONFLICT for r in report.relations)
        has_orphan = (
            report.identity is None or
            (report.identity.decision_id and report.governance is None)
        )

        findings = []
        for rel in report.relations:
            if rel.status == EvidenceStatus.CONFLICT:
                findings.append(f"CONFLICT: {rel.reason}")
            elif rel.status == EvidenceStatus.MISSING:
                findings.append(f"MISSING: {rel.reason}")

        if has_conflict:
            report.integrity.findings.append("Provenance validation FAILED: conflicts detected")
        if has_orphan:
            report.integrity.findings.append("Provenance validation WARNING: orphaned records detected")

        report.integrity.findings.extend(findings)

        return {
            "execution_id": execution_id,
            "valid": not has_conflict,
            "has_conflict": has_conflict,
            "has_orphan": has_orphan,
            "findings": report.integrity.findings,
            "completeness": report.completeness.to_dict(),
        }
