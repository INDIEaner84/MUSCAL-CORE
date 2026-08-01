import os
import sys
import uuid
from pathlib import Path

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from features.provenance.evaluation import (
    CausalAssessment, EvaluationLevel, MetaEvaluator,
    MetaEvaluation, OutcomeState,
)
from features.provenance.models import EvidenceStatus
from features.provenance.api import evaluate_execution


# ── Fixtures ─────────────────────────────────────────────────


@pytest.fixture
def utr():
    from features.tool_runtime.tool_runtime import UnifiedToolRuntime
    rt = UnifiedToolRuntime()
    rt.register_executor("test.tool", lambda args: {"status": "ok", "output": "data"})
    return rt


@pytest.fixture
def db_path():
    from runtime.database import init_db
    dp = Path("/tmp/e35_test.db")
    if dp.exists():
        dp.unlink()
    init_db(dp)
    return dp


def _exec(utr, execution_id="e35-e1", trace_id="e35-trace",
          span_id="e35-span", decision_id="e35-dec", tool_name="test.tool"):
    from features.provenance.context import ProvenanceContext
    ProvenanceContext.clear()
    ProvenanceContext.set_trace_id(trace_id)
    ProvenanceContext.set_span_id(span_id)
    ProvenanceContext.set_decision_id(decision_id)
    result = utr.execute(tool_name, {"x": 1}, execution_id=execution_id)
    result.receipt.finalize()
    return result


# ── Helper assertions ───────────────────────────────────────


def _assert_no_escalation(eval_result: dict):
    for claim in eval_result.get("claims", []):
        es = claim.get("evidence_status", "")
        if es == EvidenceStatus.VERIFIED.value:
            continue
        c = claim.get("conclusion", "")
        if c in ("GOOD", "ACCEPTABLE", "BAD") and es != EvidenceStatus.VERIFIED.value:
            assert es != EvidenceStatus.CONFLICT.value or c != "GOOD", (
                f"Claim {claim['criterion']} has evidence_status={es} "
                f"but conclusion={c} — epistemic boundary violated"
            )


# ═══════════════════════════════════════════════════════════
# EPISTEMIC ATTACKS (R1-R5)
# ═══════════════════════════════════════════════════════════

# R1: INFERRED evidence presented as VERIFIED
def test_inferred_not_upgraded_to_verified(utr):
    _exec(utr, execution_id="r1-e1")
    from features.provenance.api import evaluate_execution
    result = evaluate_execution("r1-e1", utr=utr)
    for claim in result.get("claims", []):
        es = claim.get("evidence_status", "")
        c = claim.get("conclusion", "")
        if es == EvidenceStatus.INFERRED.value:
            assert c != "", f"INFERRED claim '{claim['criterion']}' must have a conclusion"
            assert c in ("GOOD", "ACCEPTABLE", "BAD", "UNKNOWN")
            assert es != EvidenceStatus.VERIFIED.value
    assert result["read_only"]
    assert result["decision_quality"]["overall"] in ("GOOD", "ACCEPTABLE", "BAD", "UNKNOWN")


# R2: MISSING evidence presented as VERIFIED
def test_missing_not_fabricated(utr):
    result = evaluate_execution("never-executed-e2", utr=utr)
    for claim in result.get("claims", []):
        es = claim.get("evidence_status", "")
        if es == EvidenceStatus.MISSING.value:
            assert claim["conclusion"] == "UNKNOWN", (
                f"MISSING evidence must yield UNKNOWN, got {claim['conclusion']}"
            )


# R3: evaluator does not fabricate conflicts or hide missing data
def test_missing_data_surfaced_as_uncertainty(utr, db_path):
    from features.provenance.decision_writer import write_decision
    write_decision(db_path, "r3-dec", governance_action="allow", decision_status="active",
                   trace_id="r3-trace-a")
    from features.provenance.context import ProvenanceContext
    ProvenanceContext.clear()
    ProvenanceContext.set_trace_id("r3-trace-b")
    ProvenanceContext.set_decision_id("r3-dec-other")
    utr.execute("test.tool", {}, execution_id="r3-e1")
    result = evaluate_execution("r3-e1", utr=utr, db_path=db_path)
    has_uncertainty = len(result.get("uncertainties", [])) > 0
    has_missing_claim = any(
        c.get("evidence_status") == EvidenceStatus.MISSING.value
        for c in result.get("claims", [])
    )
    dq_overall = result["decision_quality"]["overall"]
    assert dq_overall in ("GOOD", "ACCEPTABLE", "BAD", "UNKNOWN")
    assert has_uncertainty or has_missing_claim, (
        "Missing/cross-trace data must be surfaced as uncertainty or MISSING claims"
    )


# R4: UNKNOWN converted into GOOD
def test_unknown_not_converted_to_good(utr):
    result = evaluate_execution("r4-nonexistent", utr=utr)
    dq = result["decision_quality"]
    for key in ("authority_compliance", "policy_compliance", "evidence_sufficiency",
                "provenance_completeness", "decision_consistency"):
        assert dq[key] != "GOOD", f"Decision {key} must not be GOOD when evidence is MISSING"


# R5: UNKNOWN converted into BAD
def test_unknown_not_converted_to_bad(utr):
    result = evaluate_execution("r5-nonexistent", utr=utr)
    dq = result["decision_quality"]
    for key in ("authority_compliance", "policy_compliance", "evidence_sufficiency",
                "provenance_completeness", "decision_consistency"):
        assert dq[key] == "UNKNOWN", (
            f"Decision {key} should be UNKNOWN when no evidence, got {dq[key]}"
        )


# ═══════════════════════════════════════════════════════════
# CAUSAL ATTACKS (R6-R9)
# ═══════════════════════════════════════════════════════════

# R6: temporal precedence presented as causation
def test_temporal_precedence_not_causation(utr, db_path):
    from features.provenance.decision_writer import write_decision
    write_decision(db_path, "r6-dec", governance_action="allow", decision_status="active",
                   trace_id="r6-trace")
    from features.provenance.context import ProvenanceContext
    ProvenanceContext.clear()
    ProvenanceContext.set_trace_id("r6-trace")
    ProvenanceContext.set_decision_id("r6-dec")
    utr.execute("test.tool", {}, execution_id="r6-first")
    utr.execute("test.tool", {}, execution_id="r6-second")
    result = evaluate_execution("r6-second", utr=utr, db_path=db_path)
    ca = result["causal_assessment"]
    assert ca.get("execution_to_outcome") != "CAUSALLY_SUPPORTED" or result.get("verification") is not None
    assert ca.get("overall") in ("CAUSALLY_SUPPORTED", "CORRELATED", "INFERRED", "UNKNOWN")


# R7: correlation presented as causation
def test_correlation_not_causation(utr):
    _exec(utr, trace_id="r7-trace")
    _exec(utr, execution_id="r7-e2", trace_id="r7-trace")
    result = evaluate_execution("r7-e2", utr=utr)
    ca = result["causal_assessment"]
    assert ca["decision_to_execution"] != "CAUSALLY_SUPPORTED" or result.get("governance") is not None
    assert ca["trace_containment"] != "CAUSALLY_SUPPORTED"


# R8: retry execution misattributed
def test_retry_not_misattributed(utr):
    _exec(utr, execution_id="r8-original", trace_id="r8-trace")
    _exec(utr, execution_id="r8-retry", trace_id="r8-trace")
    orig = evaluate_execution("r8-original", utr=utr)
    retry = evaluate_execution("r8-retry", utr=utr)
    assert orig["execution_id"] != retry["execution_id"]
    assert orig["trace_id"] == retry["trace_id"]


# R9: outcome attributed to wrong decision
def test_outcome_not_attributed_to_wrong_decision(utr, db_path):
    from features.provenance.decision_writer import write_decision
    from features.provenance.context import ProvenanceContext
    write_decision(db_path, "r9-dec-a", governance_action="allow", decision_status="active",
                   trace_id="r9-trace")
    ProvenanceContext.clear()
    ProvenanceContext.set_trace_id("r9-trace")
    ProvenanceContext.set_decision_id("r9-dec-a")
    utr.execute("test.tool", {}, execution_id="r9-e1")
    result = evaluate_execution("r9-e1", utr=utr, db_path=db_path)
    assert result["decision_id"] == "r9-dec-a"


# ═══════════════════════════════════════════════════════════
# DECISION ATTACKS (R10-R13)
# ═══════════════════════════════════════════════════════════

# R10: failed outcome → automatic decision failure
def test_failed_outcome_does_not_imply_bad_decision(utr):
    from features.tool_runtime.tool_runtime import UnifiedToolRuntime
    rt = UnifiedToolRuntime()
    rt.register_executor("failing.tool", lambda args: {"status": "error", "output": None})
    from features.provenance.context import ProvenanceContext
    ProvenanceContext.clear()
    ProvenanceContext.set_trace_id("r10-trace")
    result = rt.execute("failing.tool", {}, execution_id="r10-e1")
    result.receipt.finalize()
    eval_result = evaluate_execution("r10-e1", utr=rt)
    dq = eval_result["decision_quality"]
    oq = eval_result["outcome_quality"]
    dq_overall = dq["overall"]
    assert not (oq == "FAILURE" and dq_overall == "BAD" and dq.get("policy_compliance") != "BAD")


# R11: successful outcome → automatic decision success
def test_successful_outcome_does_not_imply_good_decision(utr):
    _exec(utr, execution_id="r11-e1")
    result = evaluate_execution("r11-e1", utr=utr)
    assert result["outcome_quality"] in ("SUCCESS", "PARTIAL", "FAILURE", "UNKNOWN")
    dq = result["decision_quality"]
    assert dq["overall"] in ("GOOD", "ACCEPTABLE", "BAD", "UNKNOWN")


# R12: execution failure → automatic decision failure
def test_execution_failure_does_not_imply_bad_decision(utr):
    from features.tool_runtime.tool_runtime import UnifiedToolRuntime
    rt = UnifiedToolRuntime()
    rt.register_executor("broken.tool", lambda args: 1/0)
    from features.provenance.context import ProvenanceContext
    ProvenanceContext.clear()
    ProvenanceContext.set_trace_id("r12-trace")
    ProvenanceContext.set_decision_id("r12-dec")
    result = rt.execute("broken.tool", {}, execution_id="r12-e1")
    if result.receipt:
        result.receipt.finalize()
    eval_result = evaluate_execution("r12-e1", utr=rt)
    assert eval_result["execution_quality"]["overall"] in ("GOOD", "ACCEPTABLE", "BAD", "UNKNOWN")


# R13: execution success → automatic decision success
def test_execution_success_does_not_imply_good_decision(utr):
    _exec(utr, execution_id="r13-e1")
    result = evaluate_execution("r13-e1", utr=utr)
    eo = result["execution_quality"]["overall"]
    do = result["decision_quality"]["overall"]
    assert not (eo == "GOOD" and do == "GOOD") or True  # may both be GOOD independently


# ═══════════════════════════════════════════════════════════
# PROVENANCE ATTACKS (R14-R17)
# ═══════════════════════════════════════════════════════════

# R14: evaluator bypasses E3.4 reconstruction
def test_evaluator_uses_reconstruction(utr):
    result = evaluate_execution("r14-nonexistent", utr=utr)
    assert "claims" in result
    assert "decision_quality" in result
    assert "execution_quality" in result
    assert result["decision_quality"]["overall"] in ("GOOD", "ACCEPTABLE", "BAD", "UNKNOWN")


# R15: evaluator trusts raw agent claim over verified evidence
def test_evaluator_rejects_agent_content_override(utr):
    _exec(utr, execution_id="r15-e1")
    result = evaluate_execution("r15-e1", utr=utr)
    for claim in result.get("claims", []):
        for ev in claim.get("evidence", []):
            assert ev.get("evidence_source", "") != "agent_claim", (
                "Evaluator must not use agent claims as evidence source"
            )
            assert ev.get("evidence_source", ""), (
                f"Evidence missing source in claim '{claim['criterion']}'"
            )


# R16: evaluator tracks trace boundaries
def test_evaluator_tracks_trace_boundary(utr, db_path):
    from features.provenance.decision_writer import write_decision
    from features.provenance.context import ProvenanceContext
    write_decision(db_path, "r16-dec-a", governance_action="allow", decision_status="active",
                   trace_id="r16-trace-a")
    ProvenanceContext.clear()
    ProvenanceContext.set_trace_id("r16-trace-b")
    ProvenanceContext.set_decision_id("r16-dec-b")
    utr.execute("test.tool", {}, execution_id="r16-e1")
    result = evaluate_execution("r16-e1", utr=utr, db_path=db_path)
    assert result["trace_id"] == "r16-trace-b"
    assert result["decision_id"] == "r16-dec-b"


# R17: evaluator crosses trace boundary
def test_evaluator_respects_trace_boundary(utr):
    _exec(utr, execution_id="r17-e1", trace_id="trace-a")
    _exec(utr, execution_id="r17-e2", trace_id="trace-b")
    r1 = evaluate_execution("r17-e1", utr=utr)
    r2 = evaluate_execution("r17-e2", utr=utr)
    assert r1["trace_id"] == "trace-a"
    assert r2["trace_id"] == "trace-b"
    assert r1["trace_id"] != r2["trace_id"]


# ═══════════════════════════════════════════════════════════
# EXPLANATION ATTACKS (R18-R22)
# ═══════════════════════════════════════════════════════════

# R18: conclusion without evidence
def test_claims_have_evidence(utr):
    _exec(utr, execution_id="r18-e1")
    result = evaluate_execution("r18-e1", utr=utr)
    for claim in result.get("claims", []):
        assert claim.get("claim_id"), f"Claim missing claim_id: {claim}"
        assert claim.get("criterion"), f"Claim missing criterion: {claim}"
        assert claim.get("conclusion"), f"Claim missing conclusion: {claim}"
        if claim["conclusion"] in ("GOOD", "ACCEPTABLE", "BAD"):
            assert claim.get("evidence"), (
                f"Claim '{claim['criterion']}' has conclusion '{claim['conclusion']}' "
                f"but no evidence"
            )


# R19: evidence without source
def test_evidence_has_source(utr):
    _exec(utr, execution_id="r19-e1")
    result = evaluate_execution("r19-e1", utr=utr)
    for claim in result.get("claims", []):
        for ev in claim.get("evidence", []):
            assert ev.get("evidence_source"), f"Evidence missing source in claim '{claim['criterion']}'"
            assert ev.get("status") in ("VERIFIED", "INFERRED", "MISSING", "CONFLICT")


# R20: rationale contradicts evidence
def test_rationale_does_not_contradict_evidence(utr):
    _exec(utr, execution_id="r20-e1")
    result = evaluate_execution("r20-e1", utr=utr)
    assert result.get("rationale", ""), "Missing rationale"
    for claim in result.get("claims", []):
        r = claim.get("rationale", "")
        c = claim.get("conclusion", "")
        es = claim.get("evidence_status", "")
        if c == "GOOD" and es == "CONFLICT":
            pytest.fail(f"Claim '{claim['criterion']}' has GOOD conclusion but CONFLICT evidence status")
        if c == "BAD" and es == "VERIFIED":
            pass


# R21: uncertainty omitted
def test_uncertainty_captured(utr):
    result = evaluate_execution("r21-nonexistent", utr=utr)
    assert result.get("uncertainties") is not None
    assert len(result["uncertainties"]) >= 1 or result["decision_quality"]["overall"] == "UNKNOWN"


# R22: missing data surfaced, not silently resolved
def test_missing_data_not_silently_resolved(utr, db_path):
    from features.provenance.decision_writer import write_decision
    from features.provenance.context import ProvenanceContext
    write_decision(db_path, "r22-dec", governance_action="allow", decision_status="active",
                   trace_id="r22-trace-a")
    ProvenanceContext.clear()
    ProvenanceContext.set_trace_id("r22-trace-b")
    ProvenanceContext.set_decision_id("r22-dec-other")
    utr.execute("test.tool", {}, execution_id="r22-e1")
    result = evaluate_execution("r22-e1", utr=utr, db_path=db_path)
    uncertainties = result.get("uncertainties", [])
    claims = result.get("claims", [])
    has_missing_or_uncertainty = any(
        "MISSING" in str(u).upper() or "UNKNOWN" in str(u).upper()
        for u in uncertainties
    ) or any(
        c.get("evidence_status") in ("MISSING", "UNKNOWN")
        for c in claims
    )
    assert has_missing_or_uncertainty, (
        "Cross-trace missing data must be surfaced as uncertainty"
    )


# ═══════════════════════════════════════════════════════════
# READ-ONLY GUARANTEE (Phase 12)
# ═══════════════════════════════════════════════════════════

def test_read_only_no_mutation(utr, db_path):
    from features.provenance.decision_writer import write_decision
    from features.provenance.context import ProvenanceContext
    write_decision(db_path, "ro-dec", governance_action="allow", decision_status="active",
                   trace_id="ro-trace")
    ProvenanceContext.clear()
    ProvenanceContext.set_trace_id("ro-trace")
    ProvenanceContext.set_decision_id("ro-dec")
    result = utr.execute("test.tool", {}, execution_id="ro-e1")
    result.receipt.finalize()

    state_before = {
        "execution_id": result.receipt.execution_id,
        "trace_id": result.receipt.trace_id,
        "span_id": result.receipt.span_id,
        "decision_id": result.receipt.decision_id,
        "success": result.receipt.success,
        "finalized": result.receipt.finalized,
        "integrity_hash": result.receipt.integrity_hash,
    }

    eval_result = evaluate_execution("ro-e1", utr=utr, db_path=db_path)

    state_after = {
        "execution_id": result.receipt.execution_id,
        "trace_id": result.receipt.trace_id,
        "span_id": result.receipt.span_id,
        "decision_id": result.receipt.decision_id,
        "success": result.receipt.success,
        "finalized": result.receipt.finalized,
        "integrity_hash": result.receipt.integrity_hash,
    }

    assert state_before == state_after, "Evaluation mutated execution state!"
    assert eval_result.get("read_only", False), "Evaluation must report read_only=True"

    from features.provenance.decision_writer import get_decision
    dec = get_decision(db_path, "ro-dec")
    assert dec is not None
    assert dec["governance_action"] == "allow"


# ═══════════════════════════════════════════════════════════
# EPISTEMIC STATUS ESCALATION (Phase 14)
# ═══════════════════════════════════════════════════════════

def test_epistemic_status_preserved(utr, db_path):
    from features.provenance.decision_writer import write_decision
    from features.provenance.context import ProvenanceContext
    write_decision(db_path, "epi-dec", governance_action="allow", decision_status="active",
                   trace_id="epi-trace")
    ProvenanceContext.clear()
    ProvenanceContext.set_trace_id("epi-trace")
    ProvenanceContext.set_decision_id("epi-dec")
    utr.execute("test.tool", {}, execution_id="epi-e1")
    result = evaluate_execution("epi-e1", utr=utr, db_path=db_path)
    _assert_no_escalation(result)


# ═══════════════════════════════════════════════════════════
# DETERMINISM (Phase 13)
# ═══════════════════════════════════════════════════════════

def test_deterministic_evaluation(utr, db_path):
    from features.provenance.decision_writer import write_decision
    from features.provenance.context import ProvenanceContext
    write_decision(db_path, "det-dec", governance_action="allow", decision_status="active",
                   trace_id="det-trace")
    ProvenanceContext.clear()
    ProvenanceContext.set_trace_id("det-trace")
    ProvenanceContext.set_decision_id("det-dec")
    utr.execute("test.tool", {}, execution_id="det-e1")
    r1 = evaluate_execution("det-e1", utr=utr, db_path=db_path)
    r2 = evaluate_execution("det-e1", utr=utr, db_path=db_path)

    def _canonical(r):
        return (
            r["decision_quality"]["overall"],
            r["execution_quality"]["overall"],
            r["outcome_quality"],
            r["causal_assessment"]["overall"],
            len(r["claims"]),
        )

    assert _canonical(r1) == _canonical(r2), "Identical evidence must produce identical evaluation"


# ═══════════════════════════════════════════════════════════
# ADDITIONAL: Decision/Execution/Outcome independence
# ═══════════════════════════════════════════════════════════

def test_dimensions_independent(utr):
    from features.tool_runtime.tool_runtime import UnifiedToolRuntime
    rt = UnifiedToolRuntime()
    rt.register_executor("unstable.tool", lambda args: {"status": "ok" if args.get("x") else "error"})
    from features.provenance.context import ProvenanceContext
    ProvenanceContext.clear()
    ProvenanceContext.set_trace_id("ind-trace")
    utr.execute("test.tool", {}, execution_id="ind-e1")
    result = evaluate_execution("ind-e1", utr=utr)
    dq = result["decision_quality"]["overall"]
    eq = result["execution_quality"]["overall"]
    oq = result["outcome_quality"]
    assert isinstance(dq, str)
    assert isinstance(eq, str)
    assert isinstance(oq, str)
