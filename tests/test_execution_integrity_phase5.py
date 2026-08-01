import os
import sys
import tempfile
import time
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

# ──────────────────────────────────────────────
# TEST SUITE: E3.1-P5/6 Execution Integrity
# ──────────────────────────────────────────────

# ── EI-01: Every execution produces a receipt ──

def test_receipt_generated_for_every_execution():
    from features.tool_runtime.tool_runtime import create_default_utr
    sg = _make_sg_permit_all()
    utr, _ = create_default_utr(safety_gate=sg)
    result = utr.execute("math.add", {"a": 1, "b": 2})
    assert result.receipt is not None
    assert result.receipt.receipt_id != ""
    assert result.receipt.tool_name == "math.add"

# ── EI-02: Verification lifecycle ──

def test_verification_lifecycle():
    from features.tool_runtime.tool_runtime import (
        create_default_utr, VerificationStatus,
    )
    sg = _make_sg_permit_all()
    utr, _ = create_default_utr(safety_gate=sg)
    result = utr.execute("math.add", {"a": 3, "b": 5})
    receipt = result.receipt
    vr = utr.verify(receipt_id=receipt.receipt_id)
    assert vr.status == VerificationStatus.VERIFIED

# ── EI-03: Verifiable tools verify correctly ──

def test_math_add_verifiable():
    from features.tool_runtime.tool_runtime import (
        create_default_utr, VerificationStatus,
    )
    sg = _make_sg_permit_all()
    utr, _ = create_default_utr(safety_gate=sg)
    result = utr.execute("math.add", {"a": 10, "b": 20})
    assert result.success
    assert result.output["result"] == 30
    receipt = result.receipt
    vr = utr.verify(receipt_id=receipt.receipt_id)
    assert vr.status == VerificationStatus.VERIFIED

def test_filesystem_write_verifiable():
    from features.tool_runtime.tool_runtime import (
        create_default_utr, VerificationStatus,
    )
    import uuid
    sg = _make_sg_permit_all()
    utr, _ = create_default_utr(safety_gate=sg)
    sg.permit("filesystem.write")
    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
        tmp_path = f.name
    try:
        eid = str(uuid.uuid4())
        utr.set_expected_state(eid, {"path": tmp_path, "content": "verify me"})
        result = utr.execute("filesystem.write", {"path": tmp_path, "content": "verify me"},
                             execution_id=eid)
        assert result.success
        receipt = result.receipt
        vr = utr.verify(receipt_id=receipt.receipt_id)
        assert vr.status == VerificationStatus.VERIFIED
    finally:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)

def test_opencode_run_verifiable():
    from features.tool_runtime.tool_runtime import (
        create_default_utr, VerificationStatus,
    )
    sg = _make_sg_permit_all()
    utr, _ = create_default_utr(safety_gate=sg)
    sg.permit("opencode.run")
    result = utr.execute("opencode.run", {"command": "echo hello"})
    assert result.success
    receipt = result.receipt
    vr = utr.verify(receipt_id=receipt.receipt_id)
    assert vr.status == VerificationStatus.VERIFIED

# ── EI-04: Non-verifiable tool ──

def test_console_print_not_verifiable():
    from features.tool_runtime.tool_runtime import (
        create_default_utr, VerificationStatus,
    )
    sg = _make_sg_permit_all()
    utr, _ = create_default_utr(safety_gate=sg)
    result = utr.execute("console.print", {"message": "test"})
    receipt = result.receipt
    vr = utr.verify(receipt_id=receipt.receipt_id)
    assert vr.status == VerificationStatus.NOT_SUPPORTED

# ── EI-05: Safety gate blocked → verification FAILED ──

def test_safety_gate_blocked_receipt():
    from features.tool_runtime.tool_runtime import (
        UnifiedToolRuntime, VerificationStatus,
    )
    from features.safety.safety_gate import SafetyGate
    sg = SafetyGate()
    utr = UnifiedToolRuntime(safety_gate=sg)
    utr.register_tool("test.tool", lambda a: {"status": "ok"}, schema={"type": "object"})
    result = utr.execute("test.tool", {"x": 1})
    assert not result.success
    receipt = result.receipt
    assert receipt.verification_status == VerificationStatus.FAILED

# ── EI-06: Unknown tool gets receipt ──

def test_unknown_tool_receipt():
    from features.tool_runtime.tool_runtime import create_default_utr
    sg = _make_sg_permit_all()
    utr, _ = create_default_utr(safety_gate=sg)
    result = utr.execute("nonexistent.tool", {"x": 1})
    assert not result.success
    assert result.receipt is not None
    assert not result.receipt.success

# ── EI-07: Executor exception gets receipt ──

def test_executor_exception_receipt():
    from features.tool_runtime.tool_runtime import (
        UnifiedToolRuntime, VerificationStatus,
    )
    utr = UnifiedToolRuntime()
    def faulty(args):
        raise RuntimeError("simulated failure")
    utr.register_tool("faulty.tool", faulty, schema={"type": "object"})
    result = utr.execute("faulty.tool", {})
    assert not result.success
    receipt = result.receipt
    assert receipt.verification_status == VerificationStatus.FAILED

# ── EI-08: Tampered result fails verification ──

def test_tampered_filesystem_fails_verification():
    from features.tool_runtime.tool_runtime import (
        create_default_utr, VerificationStatus,
    )
    import uuid
    sg = _make_sg_permit_all()
    utr, _ = create_default_utr(safety_gate=sg)
    sg.permit("filesystem.write")
    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
        tmp_path = f.name
    try:
        eid = str(uuid.uuid4())
        utr.set_expected_state(eid, {"path": tmp_path, "content": "original content"})
        result = utr.execute("filesystem.write", {"path": tmp_path, "content": "original content"},
                             execution_id=eid)
        assert result.success
        receipt = result.receipt
        with open(tmp_path, "w") as f:
            f.write("TAMPERED CONTENT")
        vr = utr.verify(receipt_id=receipt.receipt_id)
        assert vr.status == VerificationStatus.FAILED
    finally:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)

# ── EI-09: Multiple receipts stored ──

def test_multiple_receipts_stored():
    from features.tool_runtime.tool_runtime import create_default_utr
    sg = _make_sg_permit_all()
    utr, _ = create_default_utr(safety_gate=sg)
    for i in range(5):
        utr.execute("math.add", {"a": i, "b": i * 2})
    all_receipts = utr.receipts()
    assert len(all_receipts) == 5

# ── EI-10: Receipt serialisation round-trip ──

def test_receipt_serialisation_roundtrip():
    from features.tool_runtime.tool_runtime import (
        create_default_utr, ToolResult,
    )
    sg = _make_sg_permit_all()
    utr, _ = create_default_utr(safety_gate=sg)
    result = utr.execute("math.add", {"a": 7, "b": 8})
    d = result.to_dict()
    restored = ToolResult.from_dict(d)
    assert restored.receipt is not None
    assert restored.receipt.tool_name == "math.add"
    assert restored.receipt.receipt_id == result.receipt.receipt_id
    assert restored.receipt.finalized == result.receipt.finalized

# ── EI-11: Performance — 100 fast tools ──

def test_performance_100_executions():
    from features.tool_runtime.tool_runtime import create_default_utr
    sg = _make_sg_permit_all()
    utr, _ = create_default_utr(safety_gate=sg)
    start = time.time()
    for i in range(100):
        utr.execute("math.add", {"a": i, "b": i + 1})
    elapsed = time.time() - start
    assert elapsed < 2.0, f"100 executions took {elapsed:.3f}s (expected < 2.0s)"

# ── EI-12: Safety gate blocks high-risk by default ──

def test_safety_gate_blocks_high_risk_by_default():
    from features.tool_runtime.tool_runtime import UnifiedToolRuntime
    from features.safety.safety_gate import SafetyGate
    sg = SafetyGate()
    utr = UnifiedToolRuntime(safety_gate=sg)
    utr.register_tool("opencode.run", lambda a: {"status": "ok"})
    result = utr.execute("opencode.run", {"command": "ls"})
    assert not result.success

# ── EI-13: Verify by tool name ──

def test_verify_by_tool_name():
    from features.tool_runtime.tool_runtime import (
        create_default_utr, VerificationStatus,
    )
    sg = _make_sg_permit_all()
    utr, _ = create_default_utr(safety_gate=sg)
    for i in range(3):
        utr.execute("math.add", {"a": i, "b": i})
    results = utr.verify(name="math.add")
    assert len(results) == 3
    for vr in results:
        assert vr.status == VerificationStatus.VERIFIED

# ── EI-14: Verify all tools ──

def test_verify_all():
    from features.tool_runtime.tool_runtime import (
        create_default_utr, VerificationStatus,
    )
    sg = _make_sg_permit_all()
    utr, _ = create_default_utr(safety_gate=sg)
    utr.execute("math.add", {"a": 1, "b": 2})
    utr.execute("console.print", {"message": "hi"})
    results = utr.verify()
    assert isinstance(results, dict)
    assert len(results) == 2
    statuses = [vr.status for vr in results.values()]
    assert VerificationStatus.VERIFIED in statuses
    assert VerificationStatus.NOT_SUPPORTED in statuses

# ── EI-15: receipt() look-up ──

def test_receipt_lookup():
    from features.tool_runtime.tool_runtime import create_default_utr
    sg = _make_sg_permit_all()
    utr, _ = create_default_utr(safety_gate=sg)
    result = utr.execute("math.add", {"a": 1, "b": 2})
    rid = result.receipt.receipt_id
    found = utr.receipt(rid)
    assert found is not None
    assert found.receipt_id == rid
    assert utr.receipt("nonexistent") is None


# ── helpers ──

def _make_sg_permit_all():
    from features.safety.safety_gate import SafetyGate
    sg = SafetyGate(user_policy={"allow_high_risk": True})
    for name in [
        "console.print", "math.add", "filesystem.write", "file.write",
        "opencode.run", "browser.open", "browser.click", "browser.type",
        "browser.extract_text", "browser.screenshot", "browser.scroll",
        "desktop.screenshot", "desktop.type", "desktop.click",
        "desktop.open_app", "desktop.move", "desktop.keypress",
    ]:
        sg.permit(name)
    return sg
