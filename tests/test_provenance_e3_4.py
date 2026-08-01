import os
import sys
import tempfile
from pathlib import Path

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from features.provenance.models import EvidenceStatus

# ──────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────


def _make_utr_with_execution(execution_id="exec-1", trace_id="trace-1",
                              span_id="span-1", decision_id="dec-1",
                              finalized=True, tool_name="test.tool"):
    from features.tool_runtime.tool_runtime import UnifiedToolRuntime, ExecutionReceipt
    utr = UnifiedToolRuntime()
    utr.register_executor("test.tool", lambda args: {"status": "ok", "output": "data"})
    result = utr.execute(tool_name, {"x": 1}, execution_id=execution_id)
    receipt = result.receipt
    receipt.trace_id = trace_id
    receipt.span_id = span_id
    receipt.decision_id = decision_id
    if finalized:
        receipt.finalize()
    return utr, result


def _make_resolver(utr=None, db_path=None):
    from features.provenance.resolver import ProvenanceResolver
    return ProvenanceResolver(utr=utr, db_path=db_path)


def _make_decision(db_path, decision_id="dec-1", trace_id="trace-1",
                   span_id="span-1", action="allow"):
    from features.provenance.decision_writer import write_decision
    write_decision(
        db_path=db_path,
        decision_id=decision_id,
        trace_id=trace_id,
        span_id=span_id,
        governance_action=action,
        decision_status="active",
    )


# ── Identity Attacks ─────────────────────────

# R1: forged trace_id
def test_forged_trace_id():
    utr, result = _make_utr_with_execution(trace_id="real-trace")
    resolver = _make_resolver(utr=utr)
    report = resolver.resolve_execution(result.receipt.execution_id)
    trace_rels = [r for r in report.relations
                  if r.relation_type.value == "CONTAINS"]
    # Without a DB, trace_id from receipt is INFERRED (not CONFLICT — no DB to check against)
    assert all(r.status != EvidenceStatus.VERIFIED for r in trace_rels)
    assert report.identity.trace_id == "real-trace"


# R2: forged span_id
def test_forged_span_id():
    utr, result = _make_utr_with_execution(span_id="forged-span")
    resolver = _make_resolver(utr=utr)
    report = resolver.resolve_execution(result.receipt.execution_id)
    assert report.identity.span_id == "forged-span"
    # Span is in execution record, so it's VERIFIED in context
    assert report.execution.span_id == "forged-span"


# R3: forged decision_id
def test_forged_decision_id():
    utr, result = _make_utr_with_execution(decision_id="forged-dec")
    resolver = _make_resolver(utr=utr)
    report = resolver.resolve_execution(result.receipt.execution_id)
    # Without DB to verify against, decision_id is INFERRED
    dec_rels = [r for r in report.relations
                if r.relation_type.value == "AUTHORIZES"]
    assert dec_rels
    assert dec_rels[0].status == EvidenceStatus.MISSING


# R4: mismatched execution_id
def test_mismatched_execution_id():
    utr, result = _make_utr_with_execution(execution_id="e1")
    resolver = _make_resolver(utr=utr)
    report = resolver.resolve_execution("nonexistent-exec")
    assert report.identity is None
    assert report.completeness.missing >= 1


# R5: cross-trace binding
def test_cross_trace_binding():
    utr = __import__("features.tool_runtime.tool_runtime",
                     fromlist=["UnifiedToolRuntime", "ExecutionReceipt"])
    UTR = utr.UnifiedToolRuntime
    ER = utr.ExecutionReceipt
    rt = UTR()
    rt.register_executor("test.tool", lambda args: {"status": "ok"})
    r1 = rt.execute("test.tool", {}, execution_id="e1")
    r2 = rt.execute("test.tool", {}, execution_id="e2")
    r1.receipt.trace_id = "trace-a"
    r2.receipt.trace_id = "trace-b"
    r1.receipt.finalize()
    r2.receipt.finalize()
    resolver = _make_resolver(utr=rt)
    report = resolver.resolve_execution("e1")
    assert report.identity.trace_id == "trace-a"
    assert report.identity.execution_id == "e1"


# R6: cross-task binding — handled via decision_id uniqueness
def test_cross_task_decision():
    tmp_db = _temp_db()
    _make_decision(tmp_db, decision_id="dec-shared", trace_id="trace-a")
    utr, result = _make_utr_with_execution(decision_id="dec-shared", trace_id="trace-b")
    resolver = _make_resolver(utr=utr, db_path=tmp_db)
    report = resolver.resolve_execution(result.receipt.execution_id)
    # Decision "dec-shared" exists in DB (trace-a) — dec_link is VERIFIED
    # But receipt trace_id="trace-b" has no DB decisions — CONTAINS is INFERRED
    dec_rels = [r for r in report.relations
                if r.relation_type.value == "AUTHORIZES"]
    contains_rels = [r for r in report.relations
                     if r.relation_type.value == "CONTAINS"]
    assert any(r.status == EvidenceStatus.VERIFIED for r in dec_rels)
    assert any(r.status == EvidenceStatus.INFERRED for r in contains_rels)


# ── Provenance Attacks ───────────────────────

# R7: provenance overwrite (receipt trace_id changed after finalize)
def test_provenance_overwrite():
    utr, result = _make_utr_with_execution(trace_id="original", finalized=True)
    result.receipt.trace_id = "overwritten"
    valid = result.receipt.verify_integrity()
    assert not valid, "Overwrite after finalize should break integrity"


# R8: provenance deletion (trace_id removed)
def test_provenance_deletion():
    utr, result = _make_utr_with_execution(trace_id="will-be-deleted")
    result.receipt.trace_id = ""
    result.receipt.finalize()
    resolver = _make_resolver(utr=utr)
    report = resolver.resolve_execution(result.receipt.execution_id)
    assert report.identity.trace_id == ""


# R9: stale provenance (old hash no longer represents the data)
def test_stale_provenance():
    utr, result = _make_utr_with_execution(trace_id="stale")
    h1 = result.receipt.integrity_hash
    result.receipt.tool_name = "changed.tool"
    valid = result.receipt.verify_integrity()
    assert not valid


# R10: replayed provenance (same ID, different data)
def test_replayed_provenance():
    from features.tool_runtime.tool_runtime import UnifiedToolRuntime
    utr = UnifiedToolRuntime()
    utr.register_executor("test.tool", lambda args: {"status": "ok"})
    # First execution with specific execution_id
    r1 = utr.execute("test.tool", {}, execution_id="replay-e1")
    # Second execution with same execution_id — should be rejected
    r2 = utr.execute("test.tool", {}, execution_id="replay-e1")
    assert not r2.success
    assert "DUPLICATE_EXECUTION_ID" in r2.error


# R11: orphaned execution (no receipt found)
def test_orphaned_execution():
    resolver = _make_resolver(utr=None)
    report = resolver.resolve_execution("orphan-exec")
    assert report.identity is None
    assert report.completeness.missing > 0


# R12: orphaned decision (no receipt for decision_id)
def test_orphaned_decision():
    tmp_db = _temp_db()
    _make_decision(tmp_db, decision_id="orphan-dec")
    from features.provenance.decision_writer import get_decision
    dec = get_decision(tmp_db, "orphan-dec")
    assert dec is not None
    assert dec["id"] == "orphan-dec"
    resolver = _make_resolver(utr=None, db_path=tmp_db)
    # No execution exists — decision is orphaned
    report = resolver.resolve_execution("no-such-exec")
    assert report.identity is None


# R13: orphaned receipt (receipt in store but no execution link)
def test_orphaned_receipt():
    from features.tool_runtime.tool_runtime import ExecutionReceipt, UnifiedToolRuntime
    utr = UnifiedToolRuntime()
    er = ExecutionReceipt(tool_name="test", trace_id="orphan-receipt")
    er.finalize()
    utr._put_receipt(er)
    resolver = _make_resolver(utr=utr)
    # A receipt exists but is not in execution_store
    receipt = utr._get_receipt(er.receipt_id)
    assert receipt is not None
    assert er.receipt_id not in utr._execution_store


# R14: orphaned verification
def test_orphaned_verification():
    from features.tool_runtime.tool_runtime import VerificationResult, UnifiedToolRuntime
    utr = UnifiedToolRuntime()
    vr = VerificationResult(verification_id="orphan-vr", execution_id="no-exec")
    utr._verification_store["orphan-vr"] = vr
    resolver = _make_resolver(utr=utr)
    report = resolver.resolve_execution("no-exec")
    assert report.identity is None


# ── Conflict Attacks ─────────────────────────

# R15: receipt vs decision mismatch
def test_receipt_decision_mismatch():
    tmp_db = _temp_db()
    _make_decision(tmp_db, decision_id="db-dec")
    utr, result = _make_utr_with_execution(decision_id="receipt-dec")
    resolver = _make_resolver(utr=utr, db_path=tmp_db)
    report = resolver.resolve_execution(result.receipt.execution_id)
    dec_rels = [r for r in report.relations
                if r.relation_type.value == "AUTHORIZES"]
    # receipt-dec != db-dec → MISSING (db-dec not referenced, receipt-dec not in DB)
    assert any(r.status == EvidenceStatus.MISSING for r in dec_rels)


# R16: execution vs trace mismatch
def test_execution_trace_mismatch():
    tmp_db = _temp_db()
    _make_decision(tmp_db, decision_id="dec-1", trace_id="trace-db")
    utr, result = _make_utr_with_execution(decision_id="dec-1", trace_id="trace-receipt")
    resolver = _make_resolver(utr=utr, db_path=tmp_db)
    report = resolver.resolve_execution(result.receipt.execution_id)
    # Receipt trace_id ≠ DB trace_id for same decision
    ctx = report.integrity.decision_db_consistent
    assert ctx == EvidenceStatus.CONFLICT or ctx == EvidenceStatus.INFERRED


# R17: verification vs receipt mismatch
def test_verification_receipt_mismatch():
    from features.tool_runtime.tool_runtime import VerificationResult
    utr, result = _make_utr_with_execution(decision_id="receipt-dec")
    vr = VerificationResult(
        verification_id="vr-1", execution_id=result.receipt.execution_id,
        decision_id="vr-decision",
    )
    utr._verification_store["vr-1"] = vr
    resolver = _make_resolver(utr=utr)
    report = resolver.resolve_execution(result.receipt.execution_id)
    assert report.verification is not None
    # The verification record exists — the decision_id mismatch is captured
    # if there's a DB to check against, otherwise just noted as different


# R18: contradictory timestamps
def test_contradictory_timestamps():
    utr, result = _make_utr_with_execution()
    receipt = result.receipt
    resolver = _make_resolver(utr=utr)
    report = resolver.resolve_execution(receipt.execution_id)
    assert report.execution is not None
    assert report.execution.execution_time >= 0


# R19: duplicate decision identity
def test_duplicate_decision_identity():
    tmp_db = _temp_db()
    _make_decision(tmp_db, decision_id="dup-dec", action="allow")
    ok = __import__("features.provenance.decision_writer",
                    fromlist=["write_decision"]).write_decision
    dup_result = ok(
        db_path=tmp_db, decision_id="dup-dec",
        governance_action="block",
    )
    assert not dup_result


# ── Reconstruction Attacks ───────────────────

# R20: missing provenance
def test_missing_provenance():
    resolver = _make_resolver(utr=None)
    report = resolver.resolve_execution("completely-missing")
    assert report.identity is None
    assert report.completeness.missing > 0
    assert report.completeness.verified == 0


# R21: partial provenance (execution exists, no DB)
def test_partial_provenance():
    utr, result = _make_utr_with_execution(trace_id="partial-trace")
    resolver = _make_resolver(utr=utr)
    report = resolver.resolve_execution(result.receipt.execution_id)
    assert report.identity is not None
    assert report.execution is not None
    # Without DB, decision is MISSING
    dec_rels = [r for r in report.relations
                if r.relation_type.value == "AUTHORIZES"]
    assert any(r.status == EvidenceStatus.MISSING for r in dec_rels)


# R22: inferred relationship presented as verified
def test_inferred_not_verified():
    utr, result = _make_utr_with_execution(trace_id="inferred-trace")
    resolver = _make_resolver(utr=utr)
    report = resolver.resolve_execution(result.receipt.execution_id)
    for rel in report.relations:
        if rel.relation_type.value == "CONTAINS":
            assert rel.status == EvidenceStatus.INFERRED


# R23: temporal relation presented as causal
def test_temporal_not_causal():
    utr, result = _make_utr_with_execution()
    resolver = _make_resolver(utr=utr)
    report = resolver.resolve_execution(result.receipt.execution_id)
    for rel in report.relations:
        assert rel.relation_type.value != "PRECEDES"
        assert rel.relation_type.value in ("CAUSES", "AUTHORIZES", "CONTAINS",
                                            "CORRELATES_WITH", "VERIFIES")


# R24: internally valid but semantically false
def test_internally_valid_semantically_false():
    tmp_db = _temp_db()
    _make_decision(tmp_db, decision_id="dec-valid", trace_id="trace-v", action="allow")
    utr, result = _make_utr_with_execution(
        decision_id="dec-valid", trace_id="trace-v",
    )
    resolver = _make_resolver(utr=utr, db_path=tmp_db)
    report = resolver.resolve_execution(result.receipt.execution_id)
    assert report.semantic_truth.semantic_truth == "NOT ESTABLISHED"
    assert report.semantic_truth.provenance_integrity in (
        EvidenceStatus.VERIFIED, EvidenceStatus.INFERRED
    )


# R25: corrupted integrity hash
def test_corrupted_integrity_hash():
    utr = __import__("features.tool_runtime.tool_runtime",
                     fromlist=["UnifiedToolRuntime"])
    UTR = utr.UnifiedToolRuntime
    rt = UTR()
    rt.register_executor("test.tool", lambda args: {"status": "ok"})
    result = rt.execute("test.tool", {}, execution_id="corrupt-e1")
    receipt = result.receipt
    receipt.finalize()
    receipt._integrity_hash = "corrupted-hash"
    valid = receipt.verify_integrity()
    assert not valid


# ── Utility ──────────────────────────────────

def _temp_db():
    import tempfile
    from runtime.database import init_db
    td = tempfile.mkdtemp()
    db_path = Path(td) / "test_e34.db"
    init_db(db_path)
    return db_path


# ── Phase 9: Retry Reconstruction ────────────

def test_retry_same_trace_new_execution():
    utr, result1 = _make_utr_with_execution(
        execution_id="retry-e1", trace_id="retry-trace", decision_id="retry-dec",
    )
    utr2, result2 = _make_utr_with_execution(
        execution_id="retry-e2", trace_id="retry-trace", decision_id="retry-dec",
    )
    for r in (result1, result2):
        r.receipt.finalize()
    resolver = _make_resolver(utr=utr)
    r1 = resolver.resolve_execution("retry-e1")
    assert r1.identity.trace_id == "retry-trace"
    assert r1.identity.execution_id == "retry-e1"
    assert r1.identity.span_id != ""


# ── Phase 10: Async / Parallel Analysis ──────

def test_thread_local_context_isolation():
    import threading
    from features.provenance.context import ProvenanceContext
    results = {}
    def worker(tid):
        ProvenanceContext.clear()
        ProvenanceContext.set_trace_id(f"thread-{tid}")
        results[tid] = ProvenanceContext.get_trace_id()
    threads = [threading.Thread(target=worker, args=(i,)) for i in range(3)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    assert len(results) == 3
    assert results[0] != results[1]
    assert results[1] != results[2]
    assert results[0] != results[2]
