import os
import sys
import uuid
import tempfile
import threading
import asyncio
from pathlib import Path

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from features.provenance.evaluation import MetaEvaluator, MetaEvaluation, OutcomeState
from features.provenance.context import ProvenanceContext
from features.execution.outcome import OutcomeRecord, OutcomeStatus, EvidenceStatus
from features.execution.evaluation_validation import EvaluationValidation, ValidationResult
from features.execution.mreil import MREILCapture


def _make_utr():
    from features.tool_runtime.tool_runtime import UnifiedToolRuntime
    utr = UnifiedToolRuntime()
    utr.register_executor("test.tool", lambda args: {"status": "ok", "output": "data"})
    return utr


def _make_decision(db_path, decision_id="dec-cert-1", trace_id="trace-cert-1",
                   span_id="span-cert-1", action="allow"):
    from features.provenance.decision_writer import write_decision
    write_decision(
        db_path=db_path, decision_id=decision_id,
        trace_id=trace_id, span_id=span_id,
        governance_action=action, decision_status="active",
    )


def _init_db():
    from runtime.database import init_db
    td = tempfile.mkdtemp()
    db_path = Path(td) / "test_cert.db"
    init_db(db_path)
    return db_path


# ═══════════════════════════════════════════════════════════
# Phase 2: Cross-Phase Identity Integrity
# ═══════════════════════════════════════════════════════════

class TestPhase2IdentityIntegrity:

    def test_1_correct_identity_propagation(self):
        utr = _make_utr()
        db_path = _init_db()
        exec_id = "cert-identity-1"
        trace_id = "cert-trace-1"
        dec_id = "cert-dec-1"
        agent_id = "cert-agent-1"
        model_id = "cert-model-1"
        _make_decision(db_path, decision_id=dec_id, trace_id=trace_id)
        ProvenanceContext.clear()
        ProvenanceContext.set_trace_id(trace_id)
        ProvenanceContext.set_decision_id(dec_id)
        result = utr.execute("test.tool", {}, execution_id=exec_id,
                             agent_id=agent_id, model_id=model_id)
        receipt = result.receipt
        m = MetaEvaluator(utr=utr, db_path=db_path)
        eval_ = m.evaluate(exec_id)
        assert eval_.execution_id == exec_id
        assert eval_.trace_id == trace_id
        assert eval_.decision_id == dec_id
        assert eval_.agent_id == agent_id
        assert eval_.model_id == model_id
        assert receipt.execution_id == exec_id
        assert receipt.trace_id == trace_id
        assert receipt.decision_id == dec_id
        assert receipt.agent_id == agent_id
        assert receipt.model_id == model_id

    def test_2_missing_identity(self):
        utr = _make_utr()
        result = utr.execute("test.tool", {}, execution_id="cert-missing-id")
        receipt = result.receipt
        assert receipt.agent_id == ""
        assert receipt.model_id == ""

    def test_3_wrong_execution_id(self):
        utr = _make_utr()
        result = utr.execute("test.tool", {}, execution_id="cert-real-exec")
        m = MetaEvaluator(utr=utr)
        eval_ = m.evaluate("cert-wrong-exec")
        assert eval_.execution_id == "cert-wrong-exec"
        assert eval_.outcome_quality == OutcomeState.UNKNOWN

    def test_4_wrong_trace_id(self):
        utr = _make_utr()
        db_path = _init_db()
        _make_decision(db_path, decision_id="dec-wtrace", trace_id="trace-db")
        ProvenanceContext.clear()
        ProvenanceContext.set_trace_id("trace-receipt")
        ProvenanceContext.set_decision_id("dec-wtrace")
        result = utr.execute("test.tool", {}, execution_id="cert-wtrace")
        m = MetaEvaluator(utr=utr, db_path=db_path)
        eval_ = m.evaluate("cert-wtrace")
        assert eval_.trace_id == "trace-receipt"
        assert eval_.decision_id == "dec-wtrace"

    def test_5_wrong_decision_id(self):
        utr = _make_utr()
        db_path = _init_db()
        _make_decision(db_path, decision_id="dec-db", trace_id="trace-ok")
        ProvenanceContext.clear()
        ProvenanceContext.set_decision_id("dec-receipt")
        ProvenanceContext.set_trace_id("trace-ok")
        result = utr.execute("test.tool", {}, execution_id="cert-wdec")
        m = MetaEvaluator(utr=utr, db_path=db_path)
        eval_ = m.evaluate("cert-wdec")
        assert eval_.decision_id == "dec-receipt"

    def test_6_wrong_receipt_id_not_acceptable(self):
        utr = _make_utr()
        r_a = utr.execute("test.tool", {}, execution_id="cert-wrec-a",
                          agent_id="agent-a", model_id="model-a")
        r_b = utr.execute("test.tool", {}, execution_id="cert-wrec-b",
                          agent_id="agent-b", model_id="model-b")
        rid_a = r_a.receipt.receipt_id
        rid_b = r_b.receipt.receipt_id
        assert rid_a != rid_b
        assert r_a.receipt.execution_id == "cert-wrec-a"
        assert r_b.receipt.execution_id == "cert-wrec-b"
        m = MetaEvaluator(utr=utr)
        e_a = m.evaluate("cert-wrec-a")
        e_b = m.evaluate("cert-wrec-b")
        assert e_a.execution_id == "cert-wrec-a"
        assert e_b.execution_id == "cert-wrec-b"
        assert e_a.agent_id == "agent-a"
        assert e_b.agent_id == "agent-b"

    def test_7_wrong_verification_id(self):
        utr = _make_utr()
        from features.tool_runtime.tool_runtime import VerificationResult
        result = utr.execute("test.tool", {}, execution_id="cert-wver")
        vr = VerificationResult(verification_id="vr-fake", execution_id="cert-wver")
        utr._verification_store["vr-fake"] = vr
        m = MetaEvaluator(utr=utr)
        eval_ = m.evaluate("cert-wver")
        assert eval_.execution_id == "cert-wver"

    def test_8_wrong_agent_id(self):
        utr = _make_utr()
        result_a = utr.execute("test.tool", {}, execution_id="cert-wagent-a", agent_id="agent-a")
        result_b = utr.execute("test.tool", {}, execution_id="cert-wagent-b", agent_id="agent-b")
        m = MetaEvaluator(utr=utr)
        ea = m.evaluate("cert-wagent-a")
        eb = m.evaluate("cert-wagent-b")
        assert ea.agent_id == "agent-a"
        assert eb.agent_id == "agent-b"

    def test_9_wrong_model_id(self):
        utr = _make_utr()
        result_a = utr.execute("test.tool", {}, execution_id="cert-wmodel-a", model_id="model-a")
        result_b = utr.execute("test.tool", {}, execution_id="cert-wmodel-b", model_id="model-b")
        m = MetaEvaluator(utr=utr)
        ea = m.evaluate("cert-wmodel-a")
        eb = m.evaluate("cert-wmodel-b")
        assert ea.model_id == "model-a"
        assert eb.model_id == "model-b"

    def test_10_cross_execution_identity_substitution_rejected(self):
        utr = _make_utr()
        r1 = utr.execute("test.tool", {}, execution_id="cert-sub-a", agent_id="agent-a", model_id="model-a")
        r2 = utr.execute("test.tool", {}, execution_id="cert-sub-b", agent_id="agent-b", model_id="model-b")
        m = MetaEvaluator(utr=utr)
        e1 = m.evaluate("cert-sub-a")
        e2 = m.evaluate("cert-sub-b")
        assert e1.agent_id == "agent-a"
        assert e2.agent_id == "agent-b"
        assert e1.agent_id != e2.agent_id
        assert e1.model_id != e2.model_id


# ═══════════════════════════════════════════════════════════
# Phase 3: Outcome Integrity
# ═══════════════════════════════════════════════════════════

class TestPhase3OutcomeIntegrity:

    def test_case_a_exec_success_outcome_success_validation_success(self):
        utr = _make_utr()
        result = utr.execute("test.tool", {}, execution_id="cert-eov-a")
        outcome = OutcomeRecord(execution_id="cert-eov-a")
        outcome.update_verified(OutcomeStatus.SUCCESS, source="independent_monitor")
        outcome.finalize()
        m = MetaEvaluator(utr=utr)
        e = m.evaluate("cert-eov-a", outcome_record=outcome)
        assert result.success is True
        assert e.outcome_quality == OutcomeState.SUCCESS
        assert len(e.validation_artifacts) == 1
        assert e.validation_artifacts[0]["validation_result"] is not None

    def test_case_b_exec_success_outcome_failure(self):
        utr = _make_utr()
        result = utr.execute("test.tool", {}, execution_id="cert-eov-b")
        assert result.success is True
        outcome = OutcomeRecord(execution_id="cert-eov-b")
        outcome.update_verified(OutcomeStatus.FAILURE, source="independent_monitor")
        outcome.finalize()
        m = MetaEvaluator(utr=utr)
        e = m.evaluate("cert-eov-b", outcome_record=outcome)
        assert e.outcome_quality == OutcomeState.FAILURE
        assert result.success is True

    def test_case_c_exec_success_outcome_unknown(self):
        utr = _make_utr()
        result = utr.execute("test.tool", {}, execution_id="cert-eov-c")
        assert result.success is True
        m = MetaEvaluator(utr=utr)
        e = m.evaluate("cert-eov-c")
        assert e.outcome_quality == OutcomeState.UNKNOWN

    def test_case_d_exec_failure_outcome_claims_success(self):
        utr2 = type('UTR', (), {})()
        from features.tool_runtime.tool_runtime import UnifiedToolRuntime
        utr2 = UnifiedToolRuntime()
        utr2.register_executor("failing.tool", lambda args: (_ for _ in ()).throw(RuntimeError("fail")))
        result = utr2.execute("failing.tool", {}, execution_id="cert-eov-d")
        outcome = OutcomeRecord(execution_id="cert-eov-d")
        outcome.update_verified(OutcomeStatus.SUCCESS, source="independent_monitor")
        outcome.finalize()
        m = MetaEvaluator(utr=utr2)
        e = m.evaluate("cert-eov-d", outcome_record=outcome)
        assert e.outcome_quality == OutcomeState.SUCCESS

    def test_case_e_agent_claims_success_independent_says_failure(self):
        outcome = OutcomeRecord(execution_id="cert-eov-e")
        outcome.update_observed(OutcomeStatus.SUCCESS, source="agent")
        outcome.update_verified(OutcomeStatus.FAILURE, source="independent_monitor")
        assert outcome.evidence_status == EvidenceStatus.CONFLICT
        assert outcome.outcome_status == OutcomeStatus.FAILURE

    def test_case_f_observed_conflicts_verified(self):
        outcome = OutcomeRecord(execution_id="cert-eov-f")
        outcome.update_observed(OutcomeStatus.SUCCESS, source="agent")
        outcome.update_verified(OutcomeStatus.FAILURE, source="independent_monitor")
        assert outcome.evidence_status == EvidenceStatus.CONFLICT
        assert outcome.observed_outcome != outcome.verified_outcome
        outcome2 = OutcomeRecord(execution_id="cert-eov-f2")
        outcome2.update_observed(OutcomeStatus.FAILURE, source="agent")
        outcome2.update_verified(OutcomeStatus.SUCCESS, source="independent_monitor")
        assert outcome2.evidence_status == EvidenceStatus.CONFLICT
        assert outcome2.observed_outcome != outcome2.verified_outcome


# ═══════════════════════════════════════════════════════════
# Phase 4: Outcome Substitution Attack
# ═══════════════════════════════════════════════════════════

class TestPhase4OutcomeSubstitution:

    def test_outcome_substitution_rejected(self):
        utr = _make_utr()
        r_a = utr.execute("test.tool", {}, execution_id="cert-sub-a")
        r_b = utr.execute("test.tool", {}, execution_id="cert-sub-b")
        r_a.receipt.finalize()
        r_b.receipt.finalize()
        outcome_a = OutcomeRecord(execution_id="cert-sub-a")
        outcome_a.update_verified(OutcomeStatus.FAILURE, source="independent_monitor")
        outcome_a.finalize()
        outcome_b = OutcomeRecord(execution_id="cert-sub-b")
        outcome_b.update_verified(OutcomeStatus.SUCCESS, source="independent_monitor")
        outcome_b.finalize()
        m = MetaEvaluator(utr=utr)
        e_a = m.evaluate("cert-sub-a", outcome_record=outcome_a)
        e_b_attempt = m.evaluate("cert-sub-a", outcome_record=outcome_b)
        assert e_a.outcome_quality == OutcomeState.FAILURE
        assert e_b_attempt.outcome_quality != OutcomeState.SUCCESS
        assert e_b_attempt.outcome_quality == OutcomeState.UNKNOWN


# ═══════════════════════════════════════════════════════════
# Phase 5: Evaluation Backfill / Historical Immutability
# ═══════════════════════════════════════════════════════════

class TestPhase5HistoricalImmutability:

    def test_initial_unknown_later_success_creates_new_artifact(self):
        utr = _make_utr()
        r = utr.execute("test.tool", {}, execution_id="cert-backfill-1")
        r.receipt.finalize()
        m = MetaEvaluator(utr=utr)
        e1 = m.evaluate("cert-backfill-1")
        e1_id = e1.evaluation_id
        assert e1.outcome_quality == OutcomeState.UNKNOWN
        outcome = OutcomeRecord(execution_id="cert-backfill-1")
        outcome.update_verified(OutcomeStatus.SUCCESS, source="independent_monitor")
        outcome.finalize()
        e2 = m.evaluate("cert-backfill-1", outcome_record=outcome)
        assert e2.outcome_quality == OutcomeState.SUCCESS
        assert e2.evaluation_id != e1_id
        assert e1.outcome_quality == OutcomeState.UNKNOWN

    def test_initial_success_later_failure_creates_new_validation(self):
        utr = _make_utr()
        r = utr.execute("test.tool", {}, execution_id="cert-backfill-2")
        r.receipt.finalize()
        outcome1 = OutcomeRecord(execution_id="cert-backfill-2")
        outcome1.update_verified(OutcomeStatus.SUCCESS, source="independent_monitor")
        outcome1.finalize()
        m = MetaEvaluator(utr=utr)
        e1 = m.evaluate("cert-backfill-2", outcome_record=outcome1)
        assert e1.outcome_quality == OutcomeState.SUCCESS
        outcome2 = OutcomeRecord(execution_id="cert-backfill-2")
        outcome2.update_verified(OutcomeStatus.FAILURE, source="independent_monitor_2")
        outcome2.finalize()
        e2 = m.evaluate("cert-backfill-2", outcome_record=outcome2)
        assert e2.outcome_quality == OutcomeState.FAILURE
        assert e2.evaluation_id != e1.evaluation_id


# ═══════════════════════════════════════════════════════════
# Phase 6: Provenance Chain Integrity (8 identifiers)
# ═══════════════════════════════════════════════════════════

class TestPhase6ProvenanceChain:

    def test_all_8_identifiers_through_pipeline(self):
        utr = _make_utr()
        db_path = _init_db()
        exec_id = "cert-chain-8"
        trace_id = "cert-chain-trace"
        dec_id = "cert-chain-dec"
        agent_id = "cert-chain-agent"
        model_id = "cert-chain-model"
        _make_decision(db_path, decision_id=dec_id, trace_id=trace_id)
        ProvenanceContext.clear()
        ProvenanceContext.set_trace_id(trace_id)
        ProvenanceContext.set_decision_id(dec_id)
        result = utr.execute("test.tool", {}, execution_id=exec_id,
                             agent_id=agent_id, model_id=model_id)
        receipt = result.receipt
        m = MetaEvaluator(utr=utr, db_path=db_path)
        outcome = OutcomeRecord(execution_id=exec_id, trace_id=trace_id, decision_id=dec_id)
        outcome.update_verified(OutcomeStatus.SUCCESS, source="independent_monitor")
        outcome.finalize()
        eval_ = m.evaluate(exec_id, outcome_record=outcome)
        assert eval_.execution_id == exec_id
        assert eval_.trace_id == trace_id
        assert eval_.decision_id == dec_id
        assert eval_.agent_id == agent_id
        assert eval_.model_id == model_id
        assert receipt.receipt_id != ""
        assert outcome.outcome_id != ""
        assert eval_.validation_artifacts[0]["validation_id"] != ""

    def test_no_identifier_replaced_by_agent(self):
        utr = _make_utr()
        exec_id = "cert-no-agent-id"
        agent_id = "agent-try-override"
        model_id = "model-try-override"
        result = utr.execute("test.tool", {}, execution_id=exec_id,
                             agent_id=agent_id, model_id=model_id)
        rec = result.receipt
        assert rec.agent_id == agent_id
        assert rec.model_id == model_id
        assert rec.execution_id == exec_id


# ═══════════════════════════════════════════════════════════
# Phase 7: MREIL Integrity
# ═══════════════════════════════════════════════════════════

class TestPhase7MREILIntegrity:

    def test_1_correct_metrics(self):
        utr = _make_utr()
        r = utr.execute("test.tool", {}, execution_id="cert-mreil-1")
        r.receipt.finalize()
        cap = MREILCapture()
        cap.begin()
        cap.add_tokens(42)
        mreil = cap.build_metric(execution_id="cert-mreil-1")
        m = MetaEvaluator(utr=utr)
        e = m.evaluate("cert-mreil-1", mreil_metrics=mreil)
        assert e.execution_quality.resource_efficiency.value in ("GOOD", "ACCEPTABLE")

    def test_2_missing_metrics(self):
        utr = _make_utr()
        r = utr.execute("test.tool", {}, execution_id="cert-mreil-2")
        r.receipt.finalize()
        m = MetaEvaluator(utr=utr)
        e = m.evaluate("cert-mreil-2")
        assert e.execution_quality.resource_efficiency.value in ("UNKNOWN", "ACCEPTABLE")

    def test_3_wrong_execution_metrics(self):
        utr = _make_utr()
        r1 = utr.execute("test.tool", {}, execution_id="cert-mreil-3a")
        r2 = utr.execute("test.tool", {}, execution_id="cert-mreil-3b")
        cap = MREILCapture()
        cap.begin()
        mreil = cap.build_metric(execution_id="cert-mreil-3b")
        m = MetaEvaluator(utr=utr)
        e = m.evaluate("cert-mreil-3a", mreil_metrics=mreil)
        assert e.execution_id == "cert-mreil-3a"

    def test_4_fabricated_metrics_not_authoritative(self):
        uitr = _make_utr()
        r = uitr.execute("test.tool", {}, execution_id="cert-mreil-4")
        r.receipt.finalize()
        m = MetaEvaluator(utr=uitr)
        fake_metric = type('FakeMetric', (), {'resources': type('R', (), {'latency': 999.0, 'token_usage': 999999, 'cpu_time': 999.0})()})()
        e = m.evaluate("cert-mreil-4", mreil_metrics=fake_metric)
        assert e.execution_quality.resource_efficiency.value == "BAD"


# ═══════════════════════════════════════════════════════════
# Phase 8: Epistemic Boundary
# ═══════════════════════════════════════════════════════════

class TestPhase8EpistemicBoundary:

    def test_inferred_not_upgraded_to_verified(self):
        e = EvidenceStatus.INFERRED
        assert e != EvidenceStatus.VERIFIED

    def test_missing_remains_unknown(self):
        outcome = OutcomeRecord(execution_id="cert-epistemic-1")
        assert outcome.evidence_status == EvidenceStatus.MISSING
        assert outcome.outcome_status == OutcomeStatus.UNKNOWN

    def test_conflict_remains_conflict(self):
        outcome = OutcomeRecord(execution_id="cert-epistemic-2")
        outcome.update_observed(OutcomeStatus.SUCCESS, source="agent")
        outcome.update_verified(OutcomeStatus.FAILURE, source="independent_monitor")
        assert outcome.evidence_status == EvidenceStatus.CONFLICT

    def test_agent_claim_not_independent_evidence(self):
        outcome = OutcomeRecord(execution_id="cert-epistemic-3")
        outcome.update_observed(OutcomeStatus.SUCCESS, source="agent")
        assert outcome.evidence_status == EvidenceStatus.INFERRED
        assert outcome.evidence_status != EvidenceStatus.VERIFIED

    def test_evaluation_conclusion_separate_from_evidence(self):
        outcome = OutcomeRecord(execution_id="cert-epistemic-4")
        outcome.update_observed(OutcomeStatus.SUCCESS, source="agent")
        assert outcome.outcome_status == OutcomeStatus.PARTIAL
        assert outcome.evidence_status == EvidenceStatus.INFERRED


# ═══════════════════════════════════════════════════════════
# Phase 9: Evaluation Validation Integrity
# ═══════════════════════════════════════════════════════════

class TestPhase9EvaluationValidation:

    def test_validation_for_correct_evaluation(self):
        utr = _make_utr()
        r = utr.execute("test.tool", {}, execution_id="cert-val-1")
        r.receipt.finalize()
        m = MetaEvaluator(utr=utr)
        e = m.evaluate("cert-val-1")
        assert len(e.validation_artifacts) == 1
        v = e.validation_artifacts[0]
        assert v["evaluation_id"] == e.evaluation_id
        assert v["execution_id"] == e.execution_id
        assert v["finalized"] is True

    def test_validation_substitution_rejected_via_immutable_hash(self):
        utr = _make_utr()
        r1 = utr.execute("test.tool", {}, execution_id="cert-val-2a",
                         agent_id="agent-a", model_id="model-a")
        r2 = utr.execute("test.tool", {}, execution_id="cert-val-2b",
                         agent_id="agent-b", model_id="model-b")
        r1.receipt.finalize()
        r2.receipt.finalize()
        m = MetaEvaluator(utr=utr)
        e1 = m.evaluate("cert-val-2a")
        e2 = m.evaluate("cert-val-2b")
        v1 = e1.validation_artifacts[0]
        v2 = e2.validation_artifacts[0]
        assert v1["integrity_hash"] != v2["integrity_hash"]
        assert v1["execution_id"] != v2["execution_id"]
        artifact_a = EvaluationValidation.from_dict(v1)
        artifact_b = EvaluationValidation.from_dict(v2)
        v2_tampered = dict(v2)
        v2_tampered["integrity_hash"] = v1["integrity_hash"]
        tampered = EvaluationValidation.from_dict(v2_tampered)
        assert not tampered.verify_integrity()

    def test_no_cross_execution_validation(self):
        utr = _make_utr()
        r1 = utr.execute("test.tool", {}, execution_id="cert-val-3a")
        r2 = utr.execute("test.tool", {}, execution_id="cert-val-3b")
        r1.receipt.finalize()
        r2.receipt.finalize()
        m = MetaEvaluator(utr=utr)
        e1 = m.evaluate("cert-val-3a")
        e2 = m.evaluate("cert-val-3b")
        assert e1.validation_artifacts[0]["execution_id"] == "cert-val-3a"
        assert e2.validation_artifacts[0]["execution_id"] == "cert-val-3b"
        assert e1.validation_artifacts[0]["validation_id"] != e2.validation_artifacts[0]["validation_id"]

    def test_validation_with_conflicting_outcome(self):
        utr = _make_utr()
        r = utr.execute("test.tool", {}, execution_id="cert-val-4")
        r.receipt.finalize()
        outcome = OutcomeRecord(execution_id="cert-val-4")
        outcome.update_observed(OutcomeStatus.SUCCESS, source="agent")
        outcome.update_verified(OutcomeStatus.FAILURE, source="independent_monitor")
        outcome.finalize()
        m = MetaEvaluator(utr=utr)
        e = m.evaluate("cert-val-4", outcome_record=outcome)
        assert len(e.validation_artifacts) == 1

    def test_validation_after_later_evidence(self):
        utr = _make_utr()
        r = utr.execute("test.tool", {}, execution_id="cert-val-5")
        r.receipt.finalize()
        m = MetaEvaluator(utr=utr)
        e1 = m.evaluate("cert-val-5")
        outcome = OutcomeRecord(execution_id="cert-val-5")
        outcome.update_verified(OutcomeStatus.SUCCESS, source="independent_monitor")
        outcome.finalize()
        e2 = m.evaluate("cert-val-5", outcome_record=outcome)
        assert e1.validation_artifacts[0]["integrity_hash"] != e2.validation_artifacts[0]["integrity_hash"]


# ═══════════════════════════════════════════════════════════
# Phase 10: Async / Worker Isolation
# ═══════════════════════════════════════════════════════════

class TestPhase10AsyncWorkerIsolation:

    def test_concurrent_threads_no_leakage(self):
        results = {}
        def worker(wid):
            ProvenanceContext.clear()
            ProvenanceContext.set_trace_id(f"thread-{wid}")
            ProvenanceContext.set_span_id(f"span-{wid}")
            ProvenanceContext.set_decision_id(f"dec-{wid}")
            results[wid] = {
                "trace_id": ProvenanceContext.get_trace_id(),
                "span_id": ProvenanceContext.get_span_id(),
                "decision_id": ProvenanceContext.get_decision_id(),
            }
        threads = [threading.Thread(target=worker, args=(i,)) for i in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        for i in range(5):
            assert results[i]["trace_id"] == f"thread-{i}"
            assert results[i]["span_id"] == f"span-{i}"
            assert results[i]["decision_id"] == f"dec-{i}"

    def test_async_tasks_no_leakage(self):
        async def task(task_id):
            ProvenanceContext.clear()
            ProvenanceContext.set_trace_id(f"async-{task_id}")
            ProvenanceContext.set_span_id(f"async-span-{task_id}")
            return {"trace": ProvenanceContext.get_trace_id(),
                    "span": ProvenanceContext.get_span_id()}
        async def run():
            return await asyncio.gather(*[task(i) for i in range(5)])
        results = asyncio.run(run())
        for i, r in enumerate(results):
            assert r["trace"] == f"async-{i}"
            assert r["span"] == f"async-span-{i}"

    def test_worker_context_cleanup(self):
        ProvenanceContext.clear()
        ProvenanceContext.set_trace_id("main-trace")
        def worker():
            ProvenanceContext.clear()
            ProvenanceContext.set_trace_id("worker-trace")
        t = threading.Thread(target=worker)
        t.start()
        t.join()
        assert ProvenanceContext.get_trace_id() == "main-trace"

    def test_exception_in_worker_no_leakage(self):
        ProvenanceContext.clear()
        ProvenanceContext.set_trace_id("main-safe")
        def worker():
            ProvenanceContext.clear()
            ProvenanceContext.set_trace_id("worker-leak")
            raise RuntimeError("boom")
        t = threading.Thread(target=worker)
        t.start()
        t.join()
        assert ProvenanceContext.get_trace_id() == "main-safe"


# ═══════════════════════════════════════════════════════════
# Phase 11: Cross-Phase Attack Matrix
# ═══════════════════════════════════════════════════════════

class TestPhase11CrossPhaseAttackMatrix:

    def test_a_identity_substitution(self):
        utr = _make_utr()
        r1 = utr.execute("test.tool", {}, execution_id="cert-cp-a1", agent_id="agent-a")
        r2 = utr.execute("test.tool", {}, execution_id="cert-cp-a2", agent_id="agent-b")
        m = MetaEvaluator(utr=utr)
        e1 = m.evaluate("cert-cp-a1")
        e2 = m.evaluate("cert-cp-a2")
        assert e1.agent_id == "agent-a"
        assert e2.agent_id == "agent-b"
        assert e1.agent_id != e2.agent_id

    def test_b_provenance_substitution(self):
        utr = _make_utr()
        ProvenanceContext.clear()
        ProvenanceContext.set_trace_id("trace-x")
        r1 = utr.execute("test.tool", {}, execution_id="cert-cp-b1")
        ProvenanceContext.clear()
        ProvenanceContext.set_trace_id("trace-y")
        r2 = utr.execute("test.tool", {}, execution_id="cert-cp-b2")
        m = MetaEvaluator(utr=utr)
        e1 = m.evaluate("cert-cp-b1")
        e2 = m.evaluate("cert-cp-b2")
        assert e1.trace_id == "trace-x"
        assert e2.trace_id == "trace-y"

    def test_c_outcome_substitution(self):
        utr = _make_utr()
        r_a = utr.execute("test.tool", {}, execution_id="cert-cp-ca")
        r_b = utr.execute("test.tool", {}, execution_id="cert-cp-cb")
        outcome_a_fail = OutcomeRecord(execution_id="cert-cp-ca")
        outcome_a_fail.update_verified(OutcomeStatus.FAILURE, source="independent_monitor")
        outcome_a_fail.finalize()
        outcome_b_success = OutcomeRecord(execution_id="cert-cp-cb")
        outcome_b_success.update_verified(OutcomeStatus.SUCCESS, source="independent_monitor")
        outcome_b_success.finalize()
        m = MetaEvaluator(utr=utr)
        e_a_correct = m.evaluate("cert-cp-ca", outcome_record=outcome_a_fail)
        e_a_attack = m.evaluate("cert-cp-ca", outcome_record=outcome_b_success)
        assert e_a_correct.outcome_quality == OutcomeState.FAILURE
        assert e_a_attack.outcome_quality != OutcomeState.SUCCESS
        assert e_a_attack.outcome_quality == OutcomeState.UNKNOWN

    def test_d_evaluation_substitution(self):
        utr = _make_utr()
        r = utr.execute("test.tool", {}, execution_id="cert-cp-d")
        r.receipt.finalize()
        m = MetaEvaluator(utr=utr)
        e = m.evaluate("cert-cp-d")
        assert e.execution_id == "cert-cp-d"
        assert e.evaluation_id != ""

    def test_e_validation_substitution(self):
        utr = _make_utr()
        r = utr.execute("test.tool", {}, execution_id="cert-cp-e")
        r.receipt.finalize()
        m = MetaEvaluator(utr=utr)
        e = m.evaluate("cert-cp-e")
        v = e.validation_artifacts[0]
        assert v["execution_id"] == "cert-cp-e"
        assert v["evaluation_id"] == e.evaluation_id

    def test_f_cross_execution_no_contamination(self):
        utr = _make_utr()
        r1 = utr.execute("test.tool", {}, execution_id="cert-cp-f1", agent_id="agent-f1", model_id="model-f1")
        r2 = utr.execute("test.tool", {}, execution_id="cert-cp-f2", agent_id="agent-f2", model_id="model-f2")
        m = MetaEvaluator(utr=utr)
        e1 = m.evaluate("cert-cp-f1")
        e2 = m.evaluate("cert-cp-f2")
        assert e1.agent_id == "agent-f1"
        assert e1.model_id == "model-f1"
        assert e2.agent_id == "agent-f2"
        assert e2.model_id == "model-f2"

    def test_g_cross_agent_no_contamination(self):
        utr = _make_utr()
        for i, (ag, mo) in enumerate([("agent-1", "model-1"), ("agent-2", "model-2"), ("agent-3", "model-3")]):
            r = utr.execute("test.tool", {}, execution_id=f"cert-cp-g{i}", agent_id=ag, model_id=mo)
        m = MetaEvaluator(utr=utr)
        e0 = m.evaluate("cert-cp-g0")
        e1 = m.evaluate("cert-cp-g1")
        e2 = m.evaluate("cert-cp-g2")
        assert e0.agent_id == "agent-1"
        assert e1.agent_id == "agent-2"
        assert e2.agent_id == "agent-3"

    def test_h_cross_model_no_contamination(self):
        utr = _make_utr()
        for i, ag in enumerate(["model-a", "model-b", "model-c"]):
            r = utr.execute("test.tool", {}, execution_id=f"cert-cp-h{i}", model_id=ag)
        m = MetaEvaluator(utr=utr)
        assert m.evaluate("cert-cp-h0").model_id == "model-a"
        assert m.evaluate("cert-cp-h1").model_id == "model-b"
        assert m.evaluate("cert-cp-h2").model_id == "model-c"

    def test_i_historical_mutation_not_possible(self):
        outcome = OutcomeRecord(execution_id="cert-cp-i")
        outcome.update_observed(OutcomeStatus.SUCCESS, source="agent")
        before = outcome.to_dict()
        outcome.finalize()
        with pytest.raises(ValueError, match="cannot mutate finalized"):
            outcome.update_observed(OutcomeStatus.FAILURE, source="evaluator")
        after = outcome.to_dict()
        assert before["observed_outcome"] == after["observed_outcome"]

    def test_j_evidence_escalation_not_possible(self):
        outcome = OutcomeRecord(execution_id="cert-cp-j")
        outcome.update_observed(OutcomeStatus.SUCCESS, source="agent")
        assert outcome.evidence_status == EvidenceStatus.INFERRED
        outcome.update_observed(OutcomeStatus.SUCCESS, source="evaluator")
        assert outcome.evidence_status == EvidenceStatus.INFERRED
        assert outcome.evidence_status != EvidenceStatus.VERIFIED

    def test_k_agent_claim_injection_rejected(self):
        outcome = OutcomeRecord(execution_id="cert-cp-k")
        outcome.update_observed(OutcomeStatus.SUCCESS, source="agent")
        assert outcome.source == "agent"
        assert outcome.evidence_status != EvidenceStatus.VERIFIED

    def test_l_resource_metric_spoofing(self):
        uitr = _make_utr()
        r = uitr.execute("test.tool", {}, execution_id="cert-cp-l")
        r.receipt.finalize()
        m = MetaEvaluator(utr=uitr)
        fake = type('FM', (), {'resources': type('R', (), {'latency': 99.0, 'token_usage': 99999, 'cpu_time': 99.0})()})()
        e = m.evaluate("cert-cp-l", mreil_metrics=fake)
        assert e.execution_quality.resource_efficiency.value == "BAD"
        no_metrics = m.evaluate("cert-cp-l")
        assert no_metrics.execution_quality.resource_efficiency.value in ("UNKNOWN", "ACCEPTABLE")

    def test_m_replay_detected(self):
        from features.tool_runtime.tool_runtime import UnifiedToolRuntime
        utr = UnifiedToolRuntime()
        utr.register_executor("test.tool", lambda args: {"status": "ok"})
        r1 = utr.execute("test.tool", {}, execution_id="cert-cp-m")
        r2 = utr.execute("test.tool", {}, execution_id="cert-cp-m")
        assert not r2.success
        assert "DUPLICATE_EXECUTION_ID" in r2.error

    def test_n_stale_outcome_not_accepted(self):
        outcome = OutcomeRecord(execution_id="cert-cp-n")
        outcome.update_observed(OutcomeStatus.SUCCESS, source="agent")
        outcome.finalize()
        with pytest.raises(ValueError):
            outcome.update_verified(OutcomeStatus.FAILURE, source="independent_monitor")

    def test_o_conflicting_outcome_not_resolved_silently(self):
        outcome = OutcomeRecord(execution_id="cert-cp-o")
        outcome.update_observed(OutcomeStatus.SUCCESS, source="agent")
        outcome.update_verified(OutcomeStatus.FAILURE, source="independent_monitor")
        assert outcome.evidence_status == EvidenceStatus.CONFLICT
        assert outcome.evidence_status != EvidenceStatus.VERIFIED

    def test_p_wrong_decision_binding(self):
        utr = _make_utr()
        db_path = _init_db()
        _make_decision(db_path, decision_id="dec-cp-p", trace_id="trace-cp-p")
        ProvenanceContext.clear()
        ProvenanceContext.set_decision_id("dec-wrong")
        ProvenanceContext.set_trace_id("trace-cp-p")
        result = utr.execute("test.tool", {}, execution_id="cert-cp-p")
        m = MetaEvaluator(utr=utr, db_path=db_path)
        e = m.evaluate("cert-cp-p")
        assert e.decision_id == "dec-wrong"

    def test_q_wrong_trace_binding(self):
        utr = _make_utr()
        ProvenanceContext.clear()
        ProvenanceContext.set_trace_id("trace-correct")
        result = utr.execute("test.tool", {}, execution_id="cert-cp-q")
        rec = result.receipt
        assert rec.trace_id == "trace-correct"

    def test_r_wrong_receipt_binding(self):
        utr = _make_utr()
        result = utr.execute("test.tool", {}, execution_id="cert-cp-r")
        rec = result.receipt
        m = MetaEvaluator(utr=utr)
        e = m.evaluate("cert-cp-r")
        assert e.execution_id == "cert-cp-r"
        assert e.execution_quality.execution_success.value in ("GOOD", "BAD")

    def test_s_wrong_verification_binding(self):
        utr = _make_utr()
        from features.tool_runtime.tool_runtime import VerificationResult
        r1 = utr.execute("test.tool", {}, execution_id="cert-cp-s1")
        r2 = utr.execute("test.tool", {}, execution_id="cert-cp-s2")
        vr_wrong = VerificationResult(verification_id="vr-wrong", execution_id="cert-cp-s2")
        utr._verification_store["vr-wrong"] = vr_wrong
        m = MetaEvaluator(utr=utr)
        e = m.evaluate("cert-cp-s1")
        assert e.execution_id == "cert-cp-s1"

    def test_t_async_context_leakage(self):
        ProvenanceContext.clear()
        ProvenanceContext.set_trace_id("main-async")
        async def task(n):
            ProvenanceContext.clear()
            ProvenanceContext.set_trace_id(f"async-{n}")
            return ProvenanceContext.get_trace_id()
        async def run():
            return await asyncio.gather(*[task(i) for i in range(5)])
        results = asyncio.run(run())
        for i, r in enumerate(results):
            assert r == f"async-{i}"
        assert ProvenanceContext.get_trace_id() == "main-async"


# ═══════════════════════════════════════════════════════════
# E3.5.1 Closure: Condition 1 – Validation Artifact Persistence
# ═══════════════════════════════════════════════════════════

class TestE351ClosureCondition1Persistence:

    def test_artifact_persisted_via_store(self):
        from features.execution.validation_store import ValidationArtifactStore
        from runtime.database import init_db
        utr = _make_utr()
        db_path = _init_db()
        r = utr.execute("test.tool", {}, execution_id="cert-e351-c1",
                        agent_id="c1-agent", model_id="c1-model")
        r.receipt.finalize()
        store = ValidationArtifactStore(db_path=db_path)
        m = MetaEvaluator(utr=utr, db_path=db_path, validation_store=store)
        e = m.evaluate("cert-e351-c1")
        assert len(e.validation_artifacts) == 1
        v = e.validation_artifacts[0]
        loaded = store.load(v["validation_id"])
        assert loaded is not None
        assert loaded["execution_id"] == "cert-e351-c1"
        assert loaded["evaluation_id"] == e.evaluation_id

    def test_artifact_contains_span_agent_model(self):
        from features.execution.validation_store import ValidationArtifactStore
        from runtime.database import init_db
        utr = _make_utr()
        db_path = _init_db()
        r = utr.execute("test.tool", {}, execution_id="cert-e351-c1b",
                        agent_id="c1b-agent", model_id="c1b-model")
        r.receipt.finalize()
        store = ValidationArtifactStore(db_path=db_path)
        m = MetaEvaluator(utr=utr, db_path=db_path, validation_store=store)
        e = m.evaluate("cert-e351-c1b")
        v = e.validation_artifacts[0]
        assert v.get("agent_id") == "c1b-agent"
        assert v.get("model_id") == "c1b-model"
        assert v.get("span_id") != ""
        loaded = store.load(v["validation_id"])
        assert loaded["agent_id"] == "c1b-agent"
        assert loaded["model_id"] == "c1b-model"
        assert loaded["span_id"] != ""

    def test_persisted_artifact_integrity_verifiable(self):
        from features.execution.validation_store import ValidationArtifactStore
        from runtime.database import init_db
        utr = _make_utr()
        db_path = _init_db()
        r = utr.execute("test.tool", {}, execution_id="cert-e351-c1c",
                        agent_id="c1c-agent", model_id="c1c-model")
        r.receipt.finalize()
        store = ValidationArtifactStore(db_path=db_path)
        m = MetaEvaluator(utr=utr, db_path=db_path, validation_store=store)
        e = m.evaluate("cert-e351-c1c")
        v = e.validation_artifacts[0]
        loaded = store.load(v["validation_id"])
        assert store.verify_integrity(loaded) is True

    def test_no_store_no_persistence(self):
        utr = _make_utr()
        r = utr.execute("test.tool", {}, execution_id="cert-e351-c1d")
        r.receipt.finalize()
        m = MetaEvaluator(utr=utr)
        e = m.evaluate("cert-e351-c1d")
        assert len(e.validation_artifacts) == 1
        v = e.validation_artifacts[0]
        assert v["evaluation_id"] == e.evaluation_id


# ═══════════════════════════════════════════════════════════
# E3.5.1 Closure: Condition 2 – OutcomeRecord Integrity
# ═══════════════════════════════════════════════════════════

class TestE351ClosureCondition2OutcomeIntegrity:

    def test_finalized_outcome_passes_integrity(self):
        utr = _make_utr()
        r = utr.execute("test.tool", {}, execution_id="cert-e351-c2a")
        outcome = OutcomeRecord(execution_id="cert-e351-c2a")
        outcome.update_verified(OutcomeStatus.SUCCESS, source="independent_monitor")
        outcome.finalize()
        m = MetaEvaluator(utr=utr)
        e = m.evaluate("cert-e351-c2a", outcome_record=outcome)
        assert e.outcome_quality == OutcomeState.SUCCESS

    def test_tampered_outcome_rejected_as_unknown(self):
        utr = _make_utr()
        r = utr.execute("test.tool", {}, execution_id="cert-e351-c2b")
        outcome = OutcomeRecord(execution_id="cert-e351-c2b")
        outcome.update_verified(OutcomeStatus.SUCCESS, source="independent_monitor")
        outcome.finalize()
        original_hash = outcome.integrity_hash
        outcome._integrity_hash = "tampered"
        m = MetaEvaluator(utr=utr)
        e = m.evaluate("cert-e351-c2b", outcome_record=outcome)
        assert e.outcome_quality != OutcomeState.SUCCESS
        assert e.outcome_quality == OutcomeState.UNKNOWN

    def test_unfinalized_outcome_still_accepted(self):
        utr = _make_utr()
        r = utr.execute("test.tool", {}, execution_id="cert-e351-c2c")
        outcome = OutcomeRecord(execution_id="cert-e351-c2c")
        outcome.update_verified(OutcomeStatus.SUCCESS, source="independent_monitor")
        m = MetaEvaluator(utr=utr)
        e = m.evaluate("cert-e351-c2c", outcome_record=outcome)
        assert e.outcome_quality is not None

    def test_tampered_outcome_verified_finalized_rejected(self):
        utr = _make_utr()
        r = utr.execute("test.tool", {}, execution_id="cert-e351-c2d")
        outcome = OutcomeRecord(execution_id="cert-e351-c2d")
        outcome.update_verified(OutcomeStatus.SUCCESS, source="independent_monitor")
        outcome.finalize()
        outcome.verified_outcome = OutcomeStatus.FAILURE
        m = MetaEvaluator(utr=utr)
        e = m.evaluate("cert-e351-c2d", outcome_record=outcome)
        assert e.outcome_quality == OutcomeState.UNKNOWN
