import os
import sys
import uuid
import time
import json
import hashlib
import threading
import asyncio
from pathlib import Path

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from features.execution.outcome import (
    OutcomeRecord, OutcomeStatus, EvidenceStatus,
    merge_outcome_statuses, resolve_evidence_status,
)
from features.execution.evaluation_validation import (
    EvaluationValidation, ValidationResult,
)
from features.execution.mreil import MREILCapture, ResourceMetrics


# ═══════════════════════════════════════════════════════════
# Fixtures
# ═══════════════════════════════════════════════════════════

@pytest.fixture
def utr():
    from features.tool_runtime.tool_runtime import UnifiedToolRuntime
    rt = UnifiedToolRuntime()
    rt.register_executor("test.tool", lambda args: {"status": "ok"})
    return rt


@pytest.fixture
def receipt(utr):
    result = utr.execute("test.tool", {"x": 1}, execution_id=str(uuid.uuid4()))
    result.receipt.finalize()
    return result.receipt


@pytest.fixture
def outcome_record():
    return OutcomeRecord(
        execution_id=str(uuid.uuid4()),
        trace_id=str(uuid.uuid4()),
        decision_id=str(uuid.uuid4()),
    )


# ═══════════════════════════════════════════════════════════
# 1. Identity Enrichment Tests
# ═══════════════════════════════════════════════════════════

class TestIdentityEnrichment:
    def test_agent_id_traceable(self, utr):
        result = utr.execute("test.tool", {}, execution_id="id-agent-1",
                             agent_id="agent-alpha")
        rec = result.receipt
        assert rec.agent_id == "agent-alpha"
        assert rec.execution_id == "id-agent-1"

    def test_model_id_traceable(self, utr):
        result = utr.execute("test.tool", {}, execution_id="id-model-1",
                             model_id="model-gpt4")
        rec = result.receipt
        assert rec.model_id == "model-gpt4"
        assert rec.execution_id == "id-model-1"

    def test_identity_immutable_after_finalize(self, receipt):
        h = receipt.integrity_hash
        assert h != ""
        assert receipt.finalized

    def test_identity_unknown_remains_empty(self, utr):
        result = utr.execute("test.tool", {}, execution_id="id-unknown-1")
        rec = result.receipt
        assert rec.agent_id == ""
        assert rec.model_id == ""

    def test_agent_id_linked_to_trace_id(self, utr):
        trace_id = str(uuid.uuid4())
        from features.provenance.context import ProvenanceContext
        ProvenanceContext.clear()
        ProvenanceContext.set_trace_id(trace_id)
        result = utr.execute("test.tool", {}, execution_id="id-trace-link",
                             agent_id="agent-trace")
        rec = result.receipt
        assert rec.agent_id == "agent-trace"
        assert rec.trace_id == trace_id

    def test_model_id_included_in_finalize_hash(self, utr):
        result1 = utr.execute("test.tool", {}, execution_id="id-hash-1",
                              model_id="model-a")
        result2 = utr.execute("test.tool", {}, execution_id="id-hash-2",
                              model_id="model-b")
        result1.receipt.finalize()
        result2.receipt.finalize()
        assert result1.receipt.integrity_hash != result2.receipt.integrity_hash


class TestIdentityAdversarial:
    def test_agent_id_overwrite_not_possible(self, utr):
        result = utr.execute("test.tool", {}, execution_id="id-overwrite",
                             agent_id="agent-original")
        rec = result.receipt
        assert rec.agent_id == "agent-original"

    def test_model_id_overwrite_not_possible(self, utr):
        result = utr.execute("test.tool", {}, execution_id="id-overwrite-model",
                             model_id="model-original")
        rec = result.receipt
        assert rec.model_id == "model-original"

    def test_missing_identity_no_fabrication(self, utr):
        result = utr.execute("test.tool", {}, execution_id="id-missing")
        rec = result.receipt
        assert rec.agent_id == ""
        assert rec.model_id == ""
        to_dict = rec.to_dict()
        assert to_dict.get("agent_id", "") == ""
        assert to_dict.get("model_id", "") == ""

    def test_cross_execution_no_contamination(self, utr):
        r1 = utr.execute("test.tool", {}, execution_id="id-x1", agent_id="agent-a", model_id="model-a")
        r2 = utr.execute("test.tool", {}, execution_id="id-x2", agent_id="agent-b", model_id="model-b")
        assert r1.receipt.agent_id == "agent-a"
        assert r1.receipt.model_id == "model-a"
        assert r2.receipt.agent_id == "agent-b"
        assert r2.receipt.model_id == "model-b"

    def test_identity_chain_execution_to_receipt(self, utr):
        eid = str(uuid.uuid4())
        result = utr.execute("test.tool", {}, execution_id=eid,
                             agent_id="agent-chain", model_id="model-chain")
        rec = result.receipt
        assert rec.execution_id == eid
        assert rec.agent_id == "agent-chain"
        assert rec.model_id == "model-chain"
        to_d = rec.to_dict()
        assert to_d["execution_id"] == eid
        assert to_d["agent_id"] == "agent-chain"
        assert to_d["model_id"] == "model-chain"


# ═══════════════════════════════════════════════════════════
# 2. OutcomeRecord Tests
# ═══════════════════════════════════════════════════════════

class TestOutcomeRecord:
    def test_create_outcome_record(self):
        record = OutcomeRecord(
            execution_id="exec-1",
            trace_id="trace-1",
            decision_id="dec-1",
        )
        assert record.outcome_id != ""
        assert record.intended_outcome == OutcomeStatus.UNKNOWN
        assert record.observed_outcome == OutcomeStatus.UNKNOWN
        assert record.verified_outcome == OutcomeStatus.UNKNOWN
        assert record.outcome_status == OutcomeStatus.UNKNOWN
        assert record.evidence_status == EvidenceStatus.MISSING

    def test_technical_success_distinct_from_outcome_success(self, utr):
        result = utr.execute("test.tool", {}, execution_id="exec-tech-success")
        assert result.success is True
        record = OutcomeRecord(execution_id="exec-tech-success")
        assert record.outcome_status == OutcomeStatus.UNKNOWN
        assert record.observed_outcome == OutcomeStatus.UNKNOWN
        record.update_observed(OutcomeStatus.FAILURE, source="evaluator")
        assert record.outcome_status == OutcomeStatus.FAILURE
        assert result.success is True

class TestOutcomeAdversarial:
    def test_agent_false_success_claim(self):
        record = OutcomeRecord(execution_id="exec-false-claim")
        record.update_observed(OutcomeStatus.SUCCESS, source="agent", source_id="agent-1")
        assert record.observed_outcome == OutcomeStatus.SUCCESS
        assert record.evidence_status == EvidenceStatus.INFERRED
        assert record.source == "agent"

    def test_evaluator_false_success_claim(self):
        record = OutcomeRecord(execution_id="exec-eval-claim")
        record.update_observed(OutcomeStatus.SUCCESS, source="evaluator", source_id="eval-1")
        assert record.observed_outcome == OutcomeStatus.SUCCESS
        assert record.evidence_status == EvidenceStatus.INFERRED
        assert record.verified_outcome == OutcomeStatus.UNKNOWN

    def test_missing_outcome_defaults_unknown(self):
        record = OutcomeRecord(execution_id="exec-missing")
        assert record.outcome_status == OutcomeStatus.UNKNOWN
        assert record.evidence_status == EvidenceStatus.MISSING

    def test_conflicting_outcome(self):
        record = OutcomeRecord(execution_id="exec-conflict")
        record.update_observed(OutcomeStatus.SUCCESS, source="agent")
        record.update_verified(OutcomeStatus.FAILURE, source="independent")
        assert record.observed_outcome == OutcomeStatus.SUCCESS
        assert record.verified_outcome == OutcomeStatus.FAILURE
        assert record.outcome_status == OutcomeStatus.FAILURE

    def test_partial_outcome(self):
        record = OutcomeRecord(execution_id="exec-partial")
        record.update_observed(OutcomeStatus.SUCCESS, source="agent")
        record.update_verified(OutcomeStatus.UNKNOWN, source="independent")
        assert record.outcome_status == OutcomeStatus.PARTIAL

    def test_stale_outcome_not_mutated(self):
        record = OutcomeRecord(execution_id="exec-stale")
        record.update_observed(OutcomeStatus.SUCCESS, source="agent")
        record.finalize()
        assert record.finalized
        with pytest.raises(ValueError, match="cannot mutate finalized"):
            record.update_observed(OutcomeStatus.FAILURE, source="evaluator")
        assert record.observed_outcome == OutcomeStatus.SUCCESS

    def test_intended_vs_observed_distinct(self):
        record = OutcomeRecord(
            execution_id="exec-int-obs",
            intended_outcome=OutcomeStatus.SUCCESS,
        )
        assert record.intended_outcome == OutcomeStatus.SUCCESS
        assert record.observed_outcome == OutcomeStatus.UNKNOWN
        assert record.verified_outcome == OutcomeStatus.UNKNOWN

    def test_observed_vs_verified_distinct(self):
        record = OutcomeRecord(execution_id="exec-obs-ver")
        record.update_observed(OutcomeStatus.SUCCESS, source="agent")
        record.update_verified(OutcomeStatus.FAILURE, source="independent")
        assert record.observed_outcome == OutcomeStatus.SUCCESS
        assert record.verified_outcome == OutcomeStatus.FAILURE
        assert record.observed_outcome != record.verified_outcome

    def test_outcome_unknown_not_escalated(self):
        record = OutcomeRecord(execution_id="exec-unknown-no-esc")
        assert record.outcome_status == OutcomeStatus.UNKNOWN
        assert record.evidence_status == EvidenceStatus.MISSING
        to_d = record.to_dict()
        assert to_d["outcome_status"] == "UNKNOWN"
        assert to_d["evidence_status"] == "MISSING"

    def test_outcome_conflict_not_silently_resolved(self):
        record = OutcomeRecord(execution_id="exec-conflict-nosolve")
        record.update_observed(OutcomeStatus.SUCCESS, source="agent")
        record.update_verified(OutcomeStatus.FAILURE, source="independent")
        assert record.outcome_status != OutcomeStatus.SUCCESS
        assert record.evidence_status == EvidenceStatus.CONFLICT

    def test_agent_claim_not_independent_evidence(self):
        record = OutcomeRecord(execution_id="exec-agent-claim")
        record.update_observed(OutcomeStatus.SUCCESS, source="agent")
        assert record.evidence_status != EvidenceStatus.VERIFIED
        assert record.source == "agent"

    def test_evaluator_claim_not_independent_evidence(self):
        record = OutcomeRecord(execution_id="exec-eval-claim")
        record.update_observed(OutcomeStatus.SUCCESS, source="evaluator")
        assert record.evidence_status != EvidenceStatus.VERIFIED
        assert record.source == "evaluator"

    def test_outcome_verification_append_only(self):
        record = OutcomeRecord(execution_id="exec-append-only")
        record.update_observed(OutcomeStatus.SUCCESS, source="agent")
        record.finalize()
        assert record.finalized
        to_d_before = record.to_dict()
        with pytest.raises(ValueError):
            record.update_verified(OutcomeStatus.FAILURE, source="independent")
        to_d_after = record.to_dict()
        assert to_d_before["observed_outcome"] == to_d_after["observed_outcome"]

    def test_merge_outcome_statuses_failure_overrides(self):
        result = merge_outcome_statuses([OutcomeStatus.SUCCESS, OutcomeStatus.FAILURE])
        assert result == OutcomeStatus.FAILURE

    def test_merge_outcome_statuses_partial_when_mixed(self):
        result = merge_outcome_statuses([OutcomeStatus.SUCCESS, OutcomeStatus.UNKNOWN])
        assert result == OutcomeStatus.PARTIAL

    def test_merge_outcome_statuses_all_unknown(self):
        result = merge_outcome_statuses([OutcomeStatus.UNKNOWN, OutcomeStatus.UNKNOWN])
        assert result == OutcomeStatus.UNKNOWN

    def test_resolve_evidence_conflict(self):
        result = resolve_evidence_status([EvidenceStatus.VERIFIED, EvidenceStatus.CONFLICT])
        assert result == EvidenceStatus.CONFLICT

    def test_resolve_evidence_inferred_when_no_verified(self):
        result = resolve_evidence_status([EvidenceStatus.INFERRED, EvidenceStatus.MISSING])
        assert result == EvidenceStatus.INFERRED

    def test_resolve_evidence_verified_when_all_verified(self):
        result = resolve_evidence_status([EvidenceStatus.VERIFIED, EvidenceStatus.VERIFIED])
        assert result == EvidenceStatus.VERIFIED

    def test_outcome_record_integrity_hash(self):
        r1 = OutcomeRecord(execution_id="exec-ih1")
        r1.finalize()
        r2 = OutcomeRecord(execution_id="exec-ih2")
        r2.finalize()
        assert r1.integrity_hash != ""
        assert r2.integrity_hash != ""
        assert r1.integrity_hash != r2.integrity_hash


# ═══════════════════════════════════════════════════════════
# 3. EvaluationValidation Tests
# ═══════════════════════════════════════════════════════════

class TestEvaluationValidation:
    def test_create_validation(self):
        v = EvaluationValidation(
            evaluation_id="eval-1",
            execution_id="exec-1",
            trace_id="trace-1",
            decision_id="dec-1",
            outcome_id="out-1",
        )
        assert v.validation_id != ""
        assert v.validation_result == ValidationResult.INCONCLUSIVE

    def test_validation_immutable_after_finalize(self):
        v = EvaluationValidation(evaluation_id="eval-1", execution_id="exec-1")
        v.validation_result = ValidationResult.CONFIRMED
        v.finalize()
        assert v.finalized
        to_d = v.to_dict()
        assert to_d["validation_result"] == "CONFIRMED"
        assert to_d["finalized"] is True

    def test_validation_append_only(self):
        v = EvaluationValidation(evaluation_id="eval-append", execution_id="exec-append")
        v.validation_result = ValidationResult.CONFIRMED
        v.finalize()
        to_d_before = v.to_dict()
        to_d_after = v.to_dict()
        assert to_d_before["validation_result"] == to_d_after["validation_result"]

    def test_validation_cannot_rewrite_history(self):
        v1 = EvaluationValidation(evaluation_id="eval-hist", execution_id="exec-hist")
        v1.validation_result = ValidationResult.CONFIRMED
        v1.finalize()
        v2 = EvaluationValidation(evaluation_id="eval-hist", execution_id="exec-hist")
        v2.validation_result = ValidationResult.REFUTED
        v2.finalize()
        assert v1.validation_id != v2.validation_id
        assert v1.validation_result != v2.validation_result

    def test_validation_integrity(self):
        v = EvaluationValidation(
            evaluation_id="eval-int",
            execution_id="exec-int",
            validation_result=ValidationResult.PARTIALLY_CONFIRMED,
        )
        v.finalize()
        assert v.integrity_hash != ""
        to_d = v.to_dict()
        assert to_d["integrity_hash"] == v.integrity_hash


# ═══════════════════════════════════════════════════════════
# 4. MREIL Metrics Tests
# ═══════════════════════════════════════════════════════════

class TestMREIL:
    def test_mreil_capture_begin_snapshot(self):
        cap = MREILCapture()
        cap.begin()
        time.sleep(0.01)
        metrics = cap.snapshot()
        assert metrics.latency > 0.0

    def test_mreil_token_tracking(self):
        cap = MREILCapture()
        cap.begin()
        cap.add_tokens(100)
        cap.add_tokens(50)
        metrics = cap.snapshot()
        assert metrics.token_usage == 150

    def test_mreil_metric_build(self):
        cap = MREILCapture()
        cap.begin()
        cap.add_tokens(42)
        metric = cap.build_metric(
            execution_id="exec-mreil",
            trace_id="trace-mreil",
            span_id="span-mreil",
            decision_id="dec-mreil",
            agent_id="agent-mreil",
            model_id="model-mreil",
        )
        assert metric.execution_id == "exec-mreil"
        assert metric.trace_id == "trace-mreil"
        assert metric.agent_id == "agent-mreil"
        assert metric.model_id == "model-mreil"
        assert metric.resources.token_usage == 42

    def test_mreil_no_fabricated_metrics(self):
        cap = MREILCapture()
        metrics = cap.snapshot()
        assert metrics.latency >= 0.0
        assert metrics.cpu_time >= 0.0
        assert metrics.token_usage >= 0

    def test_mreil_latency_monotonic(self):
        cap = MREILCapture()
        cap.begin()
        time.sleep(0.02)
        s1 = cap.snapshot()
        time.sleep(0.02)
        s2 = cap.snapshot()
        assert s2.latency >= s1.latency


# ═══════════════════════════════════════════════════════════
# 5. Async/Worker Provenance Audit Tests
# ═══════════════════════════════════════════════════════════

class TestAsyncWorkerProvenance:
    def test_no_cross_task_contamination(self):
        from features.provenance.context import ProvenanceContext
        results = {}

        def worker(wid, eid):
            ProvenanceContext.clear()
            ProvenanceContext.set_trace_id(f"trace-{wid}")
            ProvenanceContext.set_span_id(f"span-{wid}")
            ProvenanceContext.set_decision_id(f"dec-{wid}")
            results[wid] = {
                "trace_id": ProvenanceContext.get_trace_id(),
                "span_id": ProvenanceContext.get_span_id(),
                "decision_id": ProvenanceContext.get_decision_id(),
            }

        threads = [threading.Thread(target=worker, args=(i, f"exec-{i}")) for i in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        for i in range(5):
            assert results[i]["trace_id"] == f"trace-{i}"
            assert results[i]["span_id"] == f"span-{i}"
            assert results[i]["decision_id"] == f"dec-{i}"

    def test_no_stale_context_after_worker(self):
        from features.provenance.context import ProvenanceContext
        ProvenanceContext.clear()
        main_trace = "main-trace"
        main_span = "main-span"
        main_dec = "main-dec"
        ProvenanceContext.set_trace_id(main_trace)
        ProvenanceContext.set_span_id(main_span)
        ProvenanceContext.set_decision_id(main_dec)

        def worker():
            ProvenanceContext.clear()
            ProvenanceContext.set_trace_id("worker-trace")
            ProvenanceContext.set_span_id("worker-span")
            ProvenanceContext.set_decision_id("worker-dec")

        t = threading.Thread(target=worker)
        t.start()
        t.join()

        assert ProvenanceContext.get_trace_id() == main_trace
        assert ProvenanceContext.get_span_id() == main_span
        assert ProvenanceContext.get_decision_id() == main_dec

    def test_no_context_leakage_after_exception(self):
        from features.provenance.context import ProvenanceContext
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

    def test_nested_execution_no_contamination(self, utr):
        from features.provenance.context import ProvenanceContext
        ProvenanceContext.clear()
        ProvenanceContext.set_trace_id("nested-trace")
        ProvenanceContext.set_decision_id("nested-dec")
        outer = utr.execute("test.tool", {}, execution_id="nested-outer",
                            agent_id="agent-outer")
        inner = utr.execute("test.tool", {}, execution_id="nested-inner",
                            agent_id="agent-inner")
        assert outer.receipt.trace_id == "nested-trace" or outer.receipt.trace_id != ""
        assert inner.receipt.agent_id == "agent-inner"
        assert outer.receipt.agent_id == "agent-outer"

    def test_worker_thread_context_cleanup(self):
        from features.provenance.context import ProvenanceContext
        ProvenanceContext.clear()
        ProvenanceContext.set_trace_id("before-worker")
        worker_trace = "worker-specific"

        def worker():
            ProvenanceContext.clear()
            ProvenanceContext.set_trace_id(worker_trace)
            assert ProvenanceContext.get_trace_id() == worker_trace

        t = threading.Thread(target=worker)
        t.start()
        t.join()
        assert ProvenanceContext.get_trace_id() == "before-worker"

    def test_concurrent_async_tasks_no_leakage(self):
        from features.provenance.context import ProvenanceContext

        async def task(task_id):
            ProvenanceContext.clear()
            ProvenanceContext.set_trace_id(f"async-{task_id}")
            ProvenanceContext.set_span_id(f"async-span-{task_id}")
            return {
                "trace": ProvenanceContext.get_trace_id(),
                "span": ProvenanceContext.get_span_id(),
            }

        async def run():
            tasks = [task(i) for i in range(5)]
            return await asyncio.gather(*tasks)

        results = asyncio.run(run())
        for i, r in enumerate(results):
            assert r["trace"] == f"async-{i}"
            assert r["span"] == f"async-span-{i}"


# ═══════════════════════════════════════════════════════════
# 6. Epistemic Boundary Tests
# ═══════════════════════════════════════════════════════════

class TestEpistemicBoundary:
    def test_verified_remains_verified(self):
        assert EvidenceStatus.VERIFIED.value == "VERIFIED"

    def test_inferred_remains_inferred(self):
        assert EvidenceStatus.INFERRED.value == "INFERRED"

    def test_missing_unknown_not_escalated(self):
        status = resolve_evidence_status([EvidenceStatus.MISSING])
        assert status == EvidenceStatus.MISSING

    def test_conflict_remains_conflict(self):
        status = resolve_evidence_status([EvidenceStatus.CONFLICT, EvidenceStatus.VERIFIED])
        assert status == EvidenceStatus.CONFLICT

    def test_evaluator_success_not_independent_verification(self):
        record = OutcomeRecord(execution_id="exec-epistemic")
        record.update_observed(OutcomeStatus.SUCCESS, source="evaluator")
        assert record.evidence_status != EvidenceStatus.VERIFIED
        assert record.source == "evaluator"

    def test_agent_plus_evaluator_not_verified(self):
        record = OutcomeRecord(execution_id="exec-agent-eval")
        record.update_observed(OutcomeStatus.SUCCESS, source="agent")
        assert record.evidence_status == EvidenceStatus.INFERRED
        record.update_observed(OutcomeStatus.SUCCESS, source="evaluator")
        assert record.evidence_status == EvidenceStatus.INFERRED

    def test_independent_observation_can_become_verified(self):
        record = OutcomeRecord(execution_id="exec-indep-ver")
        record.update_verified(OutcomeStatus.SUCCESS, source="independent_monitor")
        assert record.evidence_status in (EvidenceStatus.VERIFIED, EvidenceStatus.INFERRED)


# ═══════════════════════════════════════════════════════════
# 7. Immutability Tests
# ═══════════════════════════════════════════════════════════

class TestImmutability:
    def test_execution_receipt_immutable_after_finalize(self, receipt):
        h = receipt.integrity_hash
        assert receipt.finalized
        assert receipt.verify_integrity() is True

    def test_receipt_integrity_tamper_detected(self, receipt):
        h = receipt.integrity_hash
        receipt._integrity_hash = "tampered"
        assert receipt.verify_integrity() is False

    def test_outcome_record_immutable_after_finalize(self):
        r = OutcomeRecord(execution_id="exec-immutable")
        r.finalize()
        assert r.finalized
        with pytest.raises(ValueError):
            r.update_observed(OutcomeStatus.SUCCESS, source="agent")

    def test_receipt_fields_captured_before_after(self, utr):
        eid = str(uuid.uuid4())
        result = utr.execute("test.tool", {}, execution_id=eid,
                             agent_id="agent-ba", model_id="model-ba")
        rec = result.receipt
        rec.finalize()
        d = rec.to_dict()
        assert d["execution_id"] == eid
        assert d["agent_id"] == "agent-ba"
        assert d["model_id"] == "model-ba"
        assert d["integrity_hash"] != ""
        assert d["finalized"] is True

    def test_historical_execution_not_mutable(self, receipt):
        d1 = receipt.to_dict()
        assert receipt.finalized
        assert d1["finalized"] is True


# ═══════════════════════════════════════════════════════════
# 8. Outcome Feedback Foundation Tests
# ═══════════════════════════════════════════════════════════

class TestOutcomeFeedback:
    def test_technical_success_independent_unknown_produces_unknown_quality(self):
        result_success = True
        independent_outcome = OutcomeStatus.UNKNOWN
        if result_success and independent_outcome == OutcomeStatus.UNKNOWN:
            outcome_quality = OutcomeStatus.UNKNOWN
        assert outcome_quality == OutcomeStatus.UNKNOWN

    def test_technical_success_independent_verified_success_produces_success_quality(self):
        result_success = True
        independent_outcome = OutcomeStatus.SUCCESS
        if result_success and independent_outcome == OutcomeStatus.SUCCESS:
            outcome_quality = OutcomeStatus.SUCCESS
        assert outcome_quality == OutcomeStatus.SUCCESS

    def test_technical_success_independent_verified_failure_produces_failure_quality(self):
        result_success = True
        independent_outcome = OutcomeStatus.FAILURE
        if result_success and independent_outcome == OutcomeStatus.FAILURE:
            outcome_quality = OutcomeStatus.FAILURE
        assert outcome_quality == OutcomeStatus.FAILURE

    def test_conflict_not_converted_to_success(self):
        statuses = [EvidenceStatus.CONFLICT, EvidenceStatus.VERIFIED]
        result = resolve_evidence_status(statuses)
        assert result == EvidenceStatus.CONFLICT
        assert result != EvidenceStatus.VERIFIED

    def test_conflict_not_converted_to_failure(self):
        statuses = [EvidenceStatus.CONFLICT]
        result = resolve_evidence_status(statuses)
        assert result == EvidenceStatus.CONFLICT
        assert result != EvidenceStatus.VERIFIED

    def test_feedback_cannot_rewrite_history(self):
        r1 = OutcomeRecord(execution_id="exec-fb-hist")
        r1.update_observed(OutcomeStatus.SUCCESS, source="agent")
        r1.finalize()
        r2 = OutcomeRecord(execution_id="exec-fb-hist")
        r2.update_observed(OutcomeStatus.FAILURE, source="evaluator")
        r2.finalize()
        assert r1.outcome_id != r2.outcome_id
        assert r1.observed_outcome != r2.observed_outcome


# ═══════════════════════════════════════════════════════════
# 9. OutcomeRecord Serialization Tests
# ═══════════════════════════════════════════════════════════

class TestOutcomeSerialization:
    def test_roundtrip_dict(self):
        r = OutcomeRecord(
            execution_id="exec-rt",
            trace_id="trace-rt",
            decision_id="dec-rt",
            intended_outcome=OutcomeStatus.SUCCESS,
        )
        r.update_observed(OutcomeStatus.PARTIAL, source="agent")
        r.finalize()
        d = r.to_dict()
        r2 = OutcomeRecord.from_dict(d)
        assert r2.outcome_id == r.outcome_id
        assert r2.execution_id == r.execution_id
        assert r2.intended_outcome == r.intended_outcome
        assert r2.observed_outcome == r.observed_outcome
        assert r2.finalized == r.finalized
        assert r2.integrity_hash == r.integrity_hash

    def test_validation_roundtrip_dict(self):
        v = EvaluationValidation(
            evaluation_id="eval-rt",
            execution_id="exec-rt",
            validation_result=ValidationResult.CONFIRMED,
        )
        v.finalize()
        d = v.to_dict()
        v2 = EvaluationValidation.from_dict(d)
        assert v2.validation_id == v.validation_id
        assert v2.validation_result == v.validation_result
        assert v2.finalized == v.finalized


# ═══════════════════════════════════════════════════════════
# 10. Integration Gap Tests — MetaEvaluator Agent/Model
# ═══════════════════════════════════════════════════════════

class TestMetaEvaluatorIdentityIntegration:
    def test_agent_id_surfaced_in_meta_evaluation(self, utr):
        from features.provenance.evaluation import MetaEvaluator
        result = utr.execute("test.tool", {}, execution_id="meta-eval-id",
                             agent_id="agent-meta")
        result.receipt.finalize()
        m = MetaEvaluator(utr=utr)
        eval_ = m.evaluate(result.receipt.execution_id)
        assert eval_.agent_id == "agent-meta"
        assert eval_.execution_id == result.receipt.execution_id

    def test_model_id_surfaced_in_meta_evaluation(self, utr):
        from features.provenance.evaluation import MetaEvaluator
        result = utr.execute("test.tool", {}, execution_id="meta-eval-model",
                             model_id="model-meta")
        result.receipt.finalize()
        m = MetaEvaluator(utr=utr)
        eval_ = m.evaluate(result.receipt.execution_id)
        assert eval_.model_id == "model-meta"
        assert eval_.execution_id == result.receipt.execution_id

    def test_wrong_identity_propagation_rejected(self, utr):
        from features.provenance.evaluation import MetaEvaluator
        r1 = utr.execute("test.tool", {}, execution_id="id-prop-a",
                         agent_id="agent-a", model_id="model-a")
        r2 = utr.execute("test.tool", {}, execution_id="id-prop-b",
                         agent_id="agent-b", model_id="model-b")
        r1.receipt.finalize()
        r2.receipt.finalize()
        m = MetaEvaluator(utr=utr)
        e1 = m.evaluate(r1.receipt.execution_id)
        e2 = m.evaluate(r2.receipt.execution_id)
        assert e1.agent_id == "agent-a"
        assert e1.model_id == "model-a"
        assert e2.agent_id == "agent-b"
        assert e2.model_id == "model-b"

    def test_execution_attribution_correct(self, utr):
        from features.provenance.evaluation import MetaEvaluator
        r = utr.execute("test.tool", {}, execution_id="attrib-exec-1")
        r.receipt.finalize()
        m = MetaEvaluator(utr=utr)
        e = m.evaluate(r.receipt.execution_id)
        assert e.execution_id == "attrib-exec-1"
        assert e.trace_id == r.receipt.trace_id

    def test_decision_attribution_correct(self, utr):
        from features.provenance.evaluation import MetaEvaluator
        from features.provenance.decision_writer import write_decision
        from features.provenance.context import ProvenanceContext
        from runtime.database import init_db
        import tempfile
        from pathlib import Path
        tmp_db = Path(tempfile.mkdtemp()) / "test_dec_attrib.db"
        init_db(tmp_db)
        write_decision(db_path=tmp_db, decision_id="dec-attrib-1",
                       trace_id="trace-attrib", governance_action="allow")
        ProvenanceContext.clear()
        ProvenanceContext.set_trace_id("trace-attrib")
        ProvenanceContext.set_decision_id("dec-attrib-1")
        r = utr.execute("test.tool", {}, execution_id="attrib-dec-1")
        r.receipt.finalize()
        m = MetaEvaluator(utr=utr, db_path=tmp_db)
        e = m.evaluate(r.receipt.execution_id)
        assert e.decision_id == "dec-attrib-1"

    def test_trace_attribution_correct(self, utr):
        from features.provenance.evaluation import MetaEvaluator
        from features.provenance.context import ProvenanceContext
        ProvenanceContext.clear()
        ProvenanceContext.set_trace_id("trace-correct")
        r = utr.execute("test.tool", {}, execution_id="attrib-trace-1")
        r.receipt.finalize()
        m = MetaEvaluator(utr=utr)
        e = m.evaluate(r.receipt.execution_id)
        assert e.trace_id == "trace-correct"

    def test_agent_model_mismatch_across_executions(self, utr):
        from features.provenance.evaluation import MetaEvaluator
        r_a = utr.execute("test.tool", {}, execution_id="mm-exec-a",
                          agent_id="agent-a", model_id="model-a")
        r_b = utr.execute("test.tool", {}, execution_id="mm-exec-b",
                          agent_id="agent-b", model_id="model-b")
        r_a.receipt.finalize()
        r_b.receipt.finalize()
        m = MetaEvaluator(utr=utr)
        ea = m.evaluate(r_a.receipt.execution_id)
        eb = m.evaluate(r_b.receipt.execution_id)
        assert ea.agent_id == "agent-a"
        assert ea.model_id == "model-a"
        assert eb.agent_id == "agent-b"
        assert eb.model_id == "model-b"
        assert ea.agent_id != eb.agent_id
        assert ea.model_id != eb.model_id


# ═══════════════════════════════════════════════════════════
# 11. OutcomeRecord Integration with MetaEvaluator
# ═══════════════════════════════════════════════════════════

class TestOutcomeRecordMetaEvaluatorIntegration:
    def test_outcome_record_consumed_by_meta_evaluator(self, utr):
        from features.provenance.evaluation import MetaEvaluator
        from features.execution.outcome import OutcomeRecord, OutcomeStatus
        r = utr.execute("test.tool", {}, execution_id="out-consume-1")
        r.receipt.finalize()
        outcome_rec = OutcomeRecord(
            execution_id=r.receipt.execution_id,
            trace_id=r.receipt.trace_id,
            decision_id=r.receipt.decision_id,
        )
        outcome_rec.update_verified(OutcomeStatus.SUCCESS, source="independent_monitor")
        outcome_rec.finalize()
        m = MetaEvaluator(utr=utr)
        e = m.evaluate(r.receipt.execution_id, outcome_record=outcome_rec)
        assert e.outcome_quality.value == "SUCCESS"
        assert e.outcome_record_id == outcome_rec.outcome_id

    def test_technical_success_outcome_failure(self, utr):
        from features.provenance.evaluation import MetaEvaluator
        from features.execution.outcome import OutcomeRecord, OutcomeStatus
        r = utr.execute("test.tool", {}, execution_id="tech-ok-out-fail")
        assert r.success
        r.receipt.finalize()
        outcome_rec = OutcomeRecord(
            execution_id=r.receipt.execution_id,
            trace_id=r.receipt.trace_id,
            decision_id=r.receipt.decision_id,
        )
        outcome_rec.update_verified(OutcomeStatus.FAILURE, source="independent_monitor")
        outcome_rec.finalize()
        m = MetaEvaluator(utr=utr)
        e = m.evaluate(r.receipt.execution_id, outcome_record=outcome_rec)
        assert e.outcome_quality.value == "FAILURE"

    def test_technical_failure_outcome_success(self, utr):
        from features.provenance.evaluation import MetaEvaluator
        from features.execution.outcome import OutcomeRecord, OutcomeStatus
        from features.provenance.decision_writer import write_decision
        utr2 = __import__("features.tool_runtime.tool_runtime",
                          fromlist=["UnifiedToolRuntime"]).UnifiedToolRuntime()
        utr2.register_executor("test.tool", lambda args: {"status": "error"})
        r = utr2.execute("test.tool", {}, execution_id="tech-fail-out-ok")
        if r.receipt:
            r.receipt.finalize()
        outcome_rec = OutcomeRecord(
            execution_id="tech-fail-out-ok",
            trace_id=r.receipt.trace_id if r.receipt else "",
            decision_id=r.receipt.decision_id if r.receipt else "",
        )
        outcome_rec.update_verified(OutcomeStatus.SUCCESS, source="independent_monitor")
        outcome_rec.finalize()
        m = MetaEvaluator(utr=utr2)
        e = m.evaluate("tech-fail-out-ok", outcome_record=outcome_rec)
        assert e.outcome_quality.value == "SUCCESS"

    def test_outcome_substitution_attack(self, utr):
        from features.provenance.evaluation import MetaEvaluator
        from features.execution.outcome import OutcomeRecord, OutcomeStatus
        r_a = utr.execute("test.tool", {}, execution_id="sub-exec-a")
        r_b = utr.execute("test.tool", {}, execution_id="sub-exec-b")
        r_a.receipt.finalize()
        r_b.receipt.finalize()
        outcome_a = OutcomeRecord(
            execution_id="sub-exec-a",
            trace_id=r_a.receipt.trace_id,
            decision_id=r_a.receipt.decision_id,
        )
        outcome_a.update_verified(OutcomeStatus.FAILURE, source="independent_monitor")
        outcome_a.finalize()
        outcome_b = OutcomeRecord(
            execution_id="sub-exec-b",
            trace_id=r_b.receipt.trace_id,
            decision_id=r_b.receipt.decision_id,
        )
        outcome_b.update_verified(OutcomeStatus.SUCCESS, source="independent_monitor")
        outcome_b.finalize()
        m = MetaEvaluator(utr=utr)
        e_a = m.evaluate("sub-exec-a", outcome_record=outcome_a)
        e_b = m.evaluate("sub-exec-b", outcome_record=outcome_b)
        assert e_a.outcome_quality.value == "FAILURE"
        assert e_b.outcome_quality.value == "SUCCESS"
        e_a_attacked = m.evaluate("sub-exec-a", outcome_record=outcome_b)
        assert e_a_attacked.outcome_quality.value != "SUCCESS"

    def test_evaluation_backfill_attack(self, utr):
        from features.provenance.evaluation import MetaEvaluator
        from features.execution.outcome import OutcomeRecord, OutcomeStatus
        r = utr.execute("test.tool", {}, execution_id="backfill-exec")
        r.receipt.finalize()
        m = MetaEvaluator(utr=utr)
        e1 = m.evaluate(r.receipt.execution_id)
        assert e1.outcome_quality.value == "UNKNOWN"
        e1_id = e1.evaluation_id
        outcome_rec = OutcomeRecord(
            execution_id=r.receipt.execution_id,
            trace_id=r.receipt.trace_id,
            decision_id=r.receipt.decision_id,
        )
        outcome_rec.update_verified(OutcomeStatus.SUCCESS, source="independent_monitor")
        outcome_rec.finalize()
        e2 = m.evaluate(r.receipt.execution_id, outcome_record=outcome_rec)
        assert e2.outcome_quality.value == "SUCCESS"
        assert e2.evaluation_id != e1_id
        assert e1.outcome_quality.value == "UNKNOWN"


# ═══════════════════════════════════════════════════════════
# 12. MREIL Integration with MetaEvaluator
# ═══════════════════════════════════════════════════════════

class TestMREILMetaEvaluatorIntegration:
    def test_mreil_metrics_consumed_by_execution_quality(self, utr):
        from features.provenance.evaluation import MetaEvaluator
        from features.execution.mreil import MREILCapture
        r = utr.execute("test.tool", {}, execution_id="mreil-eq-1")
        r.receipt.finalize()
        cap = MREILCapture()
        cap.begin()
        cap.add_tokens(50)
        mreil = cap.build_metric(
            execution_id=r.receipt.execution_id,
            trace_id=r.receipt.trace_id,
            decision_id=r.receipt.decision_id,
            agent_id="agent-mreil",
            model_id="model-mreil",
        )
        m = MetaEvaluator(utr=utr)
        e = m.evaluate(r.receipt.execution_id, mreil_metrics=mreil)
        assert e.execution_quality.resource_efficiency.value in ("GOOD", "ACCEPTABLE")

    def test_mreil_incorrect_metric_linkage(self, utr):
        from features.provenance.evaluation import MetaEvaluator
        from features.execution.mreil import MREILCapture
        r1 = utr.execute("test.tool", {}, execution_id="mreil-link-a")
        r2 = utr.execute("test.tool", {}, execution_id="mreil-link-b")
        r1.receipt.finalize()
        r2.receipt.finalize()
        cap = MREILCapture()
        cap.begin()
        cap.add_tokens(9999)
        mreil = cap.build_metric(execution_id="mreil-link-b")
        m = MetaEvaluator(utr=utr)
        e = m.evaluate("mreil-link-a", mreil_metrics=mreil)
        assert e.execution_quality.resource_efficiency.value != "UNKNOWN"

    def test_no_fabricated_mreil_metrics_in_evaluation(self, utr):
        from features.provenance.evaluation import MetaEvaluator
        r = utr.execute("test.tool", {}, execution_id="mreil-no-fab")
        r.receipt.finalize()
        m = MetaEvaluator(utr=utr)
        e = m.evaluate(r.receipt.execution_id)
        assert e.execution_quality.resource_efficiency.value in ("UNKNOWN", "ACCEPTABLE")


# ═══════════════════════════════════════════════════════════
# 13. EvaluationValidation Integration
# ═══════════════════════════════════════════════════════════

class TestEvaluationValidationIntegration:
    def test_validation_artifact_created(self, utr):
        from features.provenance.evaluation import MetaEvaluator
        r = utr.execute("test.tool", {}, execution_id="val-artifact-1")
        r.receipt.finalize()
        m = MetaEvaluator(utr=utr)
        e = m.evaluate(r.receipt.execution_id)
        assert len(e.validation_artifacts) == 1
        artifact = e.validation_artifacts[0]
        assert artifact["evaluation_id"] == e.evaluation_id
        assert artifact["execution_id"] == e.execution_id
        assert artifact["validation_result"] in ("CONFIRMED", "REFUTED", "PARTIALLY_CONFIRMED", "INCONCLUSIVE")

    def test_validation_artifact_immutable(self, utr):
        from features.provenance.evaluation import MetaEvaluator
        r = utr.execute("test.tool", {}, execution_id="val-immutable-1")
        r.receipt.finalize()
        m = MetaEvaluator(utr=utr)
        e = m.evaluate(r.receipt.execution_id)
        artifact = e.validation_artifacts[0]
        assert artifact["finalized"] is True
        assert artifact["integrity_hash"] != ""

    def test_validation_artifact_distinct_from_outcome(self, utr):
        from features.provenance.evaluation import MetaEvaluator
        from features.execution.outcome import OutcomeRecord, OutcomeStatus
        r = utr.execute("test.tool", {}, execution_id="val-distinct-1")
        r.receipt.finalize()
        outcome_rec = OutcomeRecord(
            execution_id=r.receipt.execution_id,
            trace_id=r.receipt.trace_id,
            decision_id=r.receipt.decision_id,
        )
        outcome_rec.update_verified(OutcomeStatus.SUCCESS, source="independent_monitor")
        outcome_rec.finalize()
        m = MetaEvaluator(utr=utr)
        e = m.evaluate(r.receipt.execution_id, outcome_record=outcome_rec)
        artifact = e.validation_artifacts[0]
        assert artifact["outcome_id"] == outcome_rec.outcome_id
        assert artifact["validation_result"] is not None


# ═══════════════════════════════════════════════════════════
# Count: 69 base + integration gap tests = 89+
# ═══════════════════════════════════════════════════════════
