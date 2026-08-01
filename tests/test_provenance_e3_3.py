import os
import sys
import tempfile
from pathlib import Path

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


# ──────────────────────────────────────────────
# P1: ProvenanceContext identity generation
# ──────────────────────────────────────────────

def test_context_generates_unique_ids():
    from features.provenance.context import ProvenanceContext
    ProvenanceContext.clear()
    t1 = ProvenanceContext.generate_trace_id()
    t2 = ProvenanceContext.generate_trace_id()
    assert t1 != t2
    assert len(t1) == 36
    assert "-" in t1

    s1 = ProvenanceContext.generate_span_id()
    s2 = ProvenanceContext.generate_span_id()
    assert s1 != s2

    d1 = ProvenanceContext.generate_decision_id()
    d2 = ProvenanceContext.generate_decision_id()
    assert d1 != d2


def test_context_get_set():
    from features.provenance.context import ProvenanceContext
    ProvenanceContext.clear()
    assert ProvenanceContext.get_trace_id() is None
    ProvenanceContext.set_trace_id("test-trace")
    assert ProvenanceContext.get_trace_id() == "test-trace"


def test_context_clear():
    from features.provenance.context import ProvenanceContext
    ProvenanceContext.set_trace_id("keep")
    ProvenanceContext.clear()
    assert ProvenanceContext.get_trace_id() is None
    assert ProvenanceContext.get_span_id() is None
    assert ProvenanceContext.get_decision_id() is None


# ──────────────────────────────────────────────
# P2: ExecutionReceipt provenance fields
# ──────────────────────────────────────────────

def test_receipt_provenance_fields():
    from features.tool_runtime.tool_runtime import ExecutionReceipt
    er = ExecutionReceipt(tool_name="test", args={"x": 1},
                          trace_id="t1", span_id="s1", decision_id="d1")
    assert er.trace_id == "t1"
    assert er.span_id == "s1"
    assert er.decision_id == "d1"


def test_receipt_provenance_defaults():
    from features.tool_runtime.tool_runtime import ExecutionReceipt
    er = ExecutionReceipt(tool_name="test", args={"x": 1})
    assert er.trace_id == ""
    assert er.span_id == ""
    assert er.decision_id == ""


def test_receipt_provenance_in_integrity():
    from features.tool_runtime.tool_runtime import ExecutionReceipt
    er = ExecutionReceipt(tool_name="test", args={"x": 1},
                          trace_id="t1", span_id="s1", decision_id="d1")
    er.finalize()
    h1 = er.integrity_hash
    er2 = ExecutionReceipt(tool_name="test", args={"x": 1})
    er2.finalize()
    assert h1 != er2.integrity_hash


def test_receipt_to_dict_provenance():
    from features.tool_runtime.tool_runtime import ExecutionReceipt
    er = ExecutionReceipt(tool_name="test", trace_id="t1", span_id="s1", decision_id="d1")
    d = er.to_dict()
    assert d["trace_id"] == "t1"
    assert d["span_id"] == "s1"
    assert d["decision_id"] == "d1"


# ──────────────────────────────────────────────
# P3: VerificationResult provenance field
# ──────────────────────────────────────────────

def test_verification_decision_id():
    from features.tool_runtime.tool_runtime import VerificationResult
    vr = VerificationResult(decision_id="d1")
    assert vr.decision_id == "d1"
    d = vr.to_dict()
    assert d["decision_id"] == "d1"


def test_verification_decision_id_default():
    from features.tool_runtime.tool_runtime import VerificationResult
    vr = VerificationResult()
    assert vr.decision_id == ""


def test_verification_from_dict_decision_id():
    from features.tool_runtime.tool_runtime import VerificationResult
    vr = VerificationResult.from_dict({"decision_id": "d1"})
    assert vr.decision_id == "d1"


# ──────────────────────────────────────────────
# P4: UTR provenance integration via thread-local
# ──────────────────────────────────────────────

def test_utr_execute_provenance_from_context():
    from features.provenance.context import ProvenanceContext
    from features.tool_runtime.tool_runtime import UnifiedToolRuntime
    ProvenanceContext.clear()
    ProvenanceContext.set_trace_id("trace-p4")
    ProvenanceContext.set_decision_id("decision-p4")

    utr = UnifiedToolRuntime()
    utr.register_executor("test.echo", lambda args: {"status": "ok", "output": args.get("msg", "")})

    span_before = ProvenanceContext.get_span_id()
    result = utr.execute("test.echo", {"msg": "hello"})
    assert result.receipt is not None
    assert result.receipt.trace_id == "trace-p4"
    assert result.receipt.decision_id == "decision-p4"

    span_after = ProvenanceContext.get_span_id()
    assert result.receipt.span_id == span_after
    assert span_after != span_before


def test_utr_execute_provenance_without_context():
    from features.provenance.context import ProvenanceContext
    from features.tool_runtime.tool_runtime import UnifiedToolRuntime
    ProvenanceContext.clear()

    utr = UnifiedToolRuntime()
    utr.register_executor("test.echo", lambda args: {"status": "ok", "output": args.get("msg", "")})

    result = utr.execute("test.echo", {"msg": "noctx"})
    assert result.receipt is not None
    assert result.receipt.trace_id == ""
    assert result.receipt.span_id != ""
    assert result.receipt.decision_id == ""


def test_utr_unknown_tool_provenance():
    from features.provenance.context import ProvenanceContext
    from features.tool_runtime.tool_runtime import UnifiedToolRuntime
    ProvenanceContext.clear()
    ProvenanceContext.set_trace_id("trace-unk")
    utr = UnifiedToolRuntime()

    result = utr.execute("no.such.tool", {})
    assert result.receipt is not None
    assert result.receipt.trace_id == "trace-unk"


# ──────────────────────────────────────────────
# P5: GovernanceStage provenance integration
# ──────────────────────────────────────────────

def test_governance_stage_sets_trace_id():
    from features.pipeline.governance_stage import GovernanceStage
    from features.provenance.context import ProvenanceContext
    ProvenanceContext.clear()

    gs = GovernanceStage(kernel=None)
    ctx = {"input_text": "test"}
    ctx = gs.process(ctx)
    assert "trace_id" in ctx
    assert len(ctx["trace_id"]) == 36
    assert ctx["trace_id"] == ProvenanceContext.get_trace_id()


def test_governance_stage_generates_decision_id():
    from features.pipeline.governance_stage import GovernanceStage
    from features.provenance.context import ProvenanceContext
    ProvenanceContext.clear()

    gs = GovernanceStage(kernel=None)
    ctx = {"input_text": "test"}
    ctx = gs.process(ctx)
    assert "decision_id" in ctx
    assert len(ctx["decision_id"]) == 36
    assert ctx["decision_id"] == ProvenanceContext.get_decision_id()


def test_governance_stage_reuses_existing_trace_id():
    from features.pipeline.governance_stage import GovernanceStage
    from features.provenance.context import ProvenanceContext
    ProvenanceContext.clear()

    gs = GovernanceStage(kernel=None)
    ctx = {"input_text": "test", "trace_id": "existing-trace"}
    ctx = gs.process(ctx)
    assert ctx["trace_id"] == "existing-trace"
    assert ProvenanceContext.get_trace_id() == "existing-trace"


def test_governance_stage_decision_blocked():
    from features.pipeline.governance_stage import GovernanceStage
    from features.provenance.context import ProvenanceContext
    ProvenanceContext.clear()

    gs = GovernanceStage(kernel=None)
    ctx = {"input_text": "test", "trace_id": "trace-blocked"}
    os.environ["MUSCAL_MAX_ITERATIONS"] = "0"
    try:
        ctx = gs.process(ctx)
        assert "decision_id" in ctx
        assert ctx.get("governance_decision") == "blocked"
        assert ctx.get("_early_exit") is True
    finally:
        os.environ["MUSCAL_MAX_ITERATIONS"] = "25"


# ──────────────────────────────────────────────
# P6: Decision DB write and read
# ──────────────────────────────────────────────

@pytest.fixture
def tmp_db():
    with tempfile.TemporaryDirectory() as td:
        db_path = Path(td) / "test_provenance.db"
        from runtime.database import init_db, get_connection
        init_db(db_path)
        yield db_path


def test_write_and_read_decision(tmp_db):
    from features.provenance.decision_writer import write_decision, get_decision
    ok = write_decision(
        db_path=tmp_db,
        decision_id="dec-1",
        trace_id="trace-1",
        span_id="span-1",
        governance_action="allow",
        decision_status="active",
        reasoning="test decision",
    )
    assert ok

    dec = get_decision(tmp_db, "dec-1")
    assert dec is not None
    assert dec["id"] == "dec-1"
    assert dec["trace_id"] == "trace-1"
    assert dec["span_id"] == "span-1"
    assert dec["governance_action"] == "allow"
    assert dec["decision_status"] == "active"
    assert dec["reasoning"] == "test decision"


def test_read_missing_decision(tmp_db):
    from features.provenance.decision_writer import get_decision
    dec = get_decision(tmp_db, "nonexistent")
    assert dec is None


def test_decisions_by_trace(tmp_db):
    from features.provenance.decision_writer import write_decision, get_decisions_by_trace
    write_decision(tmp_db, decision_id="d1", trace_id="trace-g", governance_action="allow")
    write_decision(tmp_db, decision_id="d2", trace_id="trace-g", governance_action="block")
    write_decision(tmp_db, decision_id="d3", trace_id="other", governance_action="allow")

    decisions = get_decisions_by_trace(tmp_db, "trace-g")
    assert len(decisions) == 2
    assert decisions[0]["id"] in ("d1", "d2")
    assert decisions[1]["id"] in ("d1", "d2")


def test_decision_duplicate_id(tmp_db):
    from features.provenance.decision_writer import write_decision
    ok1 = write_decision(tmp_db, decision_id="dup-1", governance_action="allow")
    assert ok1
    ok2 = write_decision(tmp_db, decision_id="dup-1", governance_action="block")
    assert not ok2


# ──────────────────────────────────────────────
# P7: Retry semantics — trace_id stable, span_id new
# ──────────────────────────────────────────────

def test_retry_semantics():
    from features.provenance.context import ProvenanceContext
    from features.tool_runtime.tool_runtime import UnifiedToolRuntime
    ProvenanceContext.clear()
    trace_id = ProvenanceContext.generate_trace_id()
    decision_id = ProvenanceContext.generate_decision_id()

    utr = UnifiedToolRuntime()
    utr.register_executor("test.echo", lambda args: {"status": "ok", "output": "retry"})

    # First call
    ProvenanceContext.set_trace_id(trace_id)
    ProvenanceContext.set_decision_id(decision_id)
    r1 = utr.execute("test.echo", {})
    s1 = r1.receipt.span_id

    # Second call (simulated retry — same trace, same decision, new span)
    ProvenanceContext.set_trace_id(trace_id)
    ProvenanceContext.set_decision_id(decision_id)
    r2 = utr.execute("test.echo", {})
    s2 = r2.receipt.span_id

    assert r2.receipt.trace_id == trace_id
    assert r2.receipt.decision_id == decision_id
    assert s1 != s2


# ──────────────────────────────────────────────
# P8: ExecutionReceipt from_dict preserves provenance
# ──────────────────────────────────────────────

def test_tool_result_from_dict_preserves_provenance():
    from features.tool_runtime.tool_runtime import ToolResult, ExecutionReceipt
    er = ExecutionReceipt(tool_name="test", trace_id="t1", span_id="s1", decision_id="d1")
    tr = ToolResult(tool_name="test", success=True, receipt=er)
    d = tr.to_dict()
    tr2 = ToolResult.from_dict(d)
    assert tr2.receipt.trace_id == "t1"
    assert tr2.receipt.span_id == "s1"
    assert tr2.receipt.decision_id == "d1"


# ──────────────────────────────────────────────
# P9: GovernanceStage integration with ownership reasoning
# ──────────────────────────────────────────────

def test_provenance_authority_chain():
    from features.provenance.context import ProvenanceContext
    from features.pipeline.governance_stage import GovernanceStage
    ProvenanceContext.clear()

    gs = GovernanceStage(kernel=None)
    ctx = {"input_text": "authority-test"}

    # GovernanceStage generates trace_id and decision_id
    ctx = gs.process(ctx)
    trace_id = ctx["trace_id"]
    decision_id = ctx["decision_id"]

    # The IDs must be UUIDs, not agent-provided
    assert len(trace_id) == 36
    assert trace_id.count("-") == 4


# ──────────────────────────────────────────────
# P10: Decision table schema has new columns
# ──────────────────────────────────────────────

def test_decision_table_has_provenance_columns(tmp_db):
    from runtime.database import get_connection, _table_has_column
    conn = get_connection(tmp_db)
    assert _table_has_column(conn, "decisions", "trace_id")
    assert _table_has_column(conn, "decisions", "span_id")
    assert _table_has_column(conn, "decisions", "decision_type")
    assert _table_has_column(conn, "decisions", "decision_status")
    assert _table_has_column(conn, "decisions", "governance_action")
    assert _table_has_column(conn, "decisions", "parent_decision_id")
    conn.close()
