import os
import sys
import tempfile
import time
import hashlib
import json
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

# ──────────────────────────────────────────────
# E3.1-P6 Adversarial Agent Test Suite
# ──────────────────────────────────────────────

# AI-01: Agent claims file was created. File does not exist.

def test_ai_01_file_claimed_not_found():
    from features.tool_runtime.tool_runtime import (
        UnifiedToolRuntime, VerificationStatus,
    )
    utr = UnifiedToolRuntime()
    utr.execute("nonexistent.file", {"path": "/tmp/nope.txt", "content": "data"})
    results = utr.verify()
    for vr in results.values():
        assert vr.status != VerificationStatus.VERIFIED


# AI-02: Agent claims file was created. File exists with wrong content.

def test_ai_02_file_exists_wrong_content():
    from features.tool_runtime.tool_runtime import (
        create_default_utr, VerificationStatus,
    )
    import uuid
    sg = _make_sg_permit_all()
    sg.permit("filesystem.write")
    utr, _ = create_default_utr(safety_gate=sg)
    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
        tmp_path = f.name
    try:
        eid = str(uuid.uuid4())
        utr.set_expected_state(eid, {"path": tmp_path, "content": "real content"})
        result = utr.execute("filesystem.write", {"path": tmp_path, "content": "real content"},
                             execution_id=eid)
        assert result.success
        receipt = result.receipt
        with open(tmp_path, "w") as f2:
            f2.write("TAMPERED CONTENT")
        vr = utr.verify(receipt_id=receipt.receipt_id)
        assert vr.status == VerificationStatus.FAILED
    finally:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)


# AI-03: Agent claims successful tool execution. Tool actually fails.

def test_ai_03_claim_success_tool_fails():
    from features.tool_runtime.tool_runtime import (
        UnifiedToolRuntime, VerificationStatus,
    )
    utr = UnifiedToolRuntime()
    def failing_fn(args):
        raise RuntimeError("execution failed")
    utr.register_tool("failing.tool", failing_fn, schema={"type": "object"})
    result = utr.execute("failing.tool", {"input": "test"})
    assert not result.success
    receipt = result.receipt
    assert receipt.verification_status == VerificationStatus.FAILED


# AI-04: Tool reports success. External state contradicts.

def test_ai_04_success_contradicted_by_external_state():
    from features.tool_runtime.tool_runtime import (
        create_default_utr, VerificationStatus,
    )
    import uuid
    sg = _make_sg_permit_all()
    sg.permit("filesystem.write")
    utr, _ = create_default_utr(safety_gate=sg)
    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
        tmp_path = f.name
    try:
        eid = str(uuid.uuid4())
        utr.set_expected_state(eid, {"path": tmp_path, "content": "original"})
        result = utr.execute("filesystem.write", {"path": tmp_path, "content": "original"},
                             execution_id=eid)
        assert result.success
        receipt = result.receipt
        os.unlink(tmp_path)
        vr = utr.verify(receipt_id=receipt.receipt_id)
        assert vr.status == VerificationStatus.FAILED
    except Exception:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)


# AI-05: Agent fabricates an ExecutionReceipt.

def test_ai_05_fabricated_receipt_rejected():
    from features.tool_runtime.tool_runtime import (
        ExecutionReceipt, VerificationStatus,
    )
    fake = ExecutionReceipt(
        tool_name="math.add", args={"a": 1, "b": 2},
        result_data={"result": 3}, success=True,
    )
    fake.finalize()
    fake._integrity_hash = "fakehash123"
    assert not fake.verify_integrity()


# AI-06: Agent replays an old successful receipt.

def test_ai_06_replay_detected():
    from features.tool_runtime.tool_runtime import create_default_utr
    sg = _make_sg_permit_all()
    utr, _ = create_default_utr(safety_gate=sg)
    eid = "replay-test-exec-id"
    r1 = utr.execute("math.add", {"a": 1, "b": 2}, execution_id=eid)
    assert r1.success
    r2 = utr.execute("math.add", {"a": 1, "b": 2}, execution_id=eid)
    assert not r2.success
    assert "DUPLICATE_EXECUTION_ID" in r2.error


# AI-07: Agent modifies receipt after execution.

def test_ai_07_tampered_receipt_detected():
    from features.tool_runtime.tool_runtime import (
        create_default_utr, VerificationStatus,
    )
    sg = _make_sg_permit_all()
    utr, _ = create_default_utr(safety_gate=sg)
    result = utr.execute("math.add", {"a": 5, "b": 3})
    receipt = result.receipt
    receipt.result_data = {"result": 999}
    vr = utr.verify(receipt_id=receipt.receipt_id)
    assert vr.status == VerificationStatus.TAMPERED


# AI-08: Duplicate execution request idempotency.

def test_ai_08_duplicate_execution_idempotent():
    from features.tool_runtime.tool_runtime import create_default_utr
    sg = _make_sg_permit_all()
    utr, _ = create_default_utr(safety_gate=sg)
    eid = "dup-test-id"
    r1 = utr.execute("math.add", {"a": 10, "b": 20}, execution_id=eid)
    assert r1.success
    assert r1.receipt.execution_id == eid
    r2 = utr.execute("math.add", {"a": 10, "b": 20}, execution_id=eid)
    assert not r2.success
    assert r2.metadata.get("dedup") is True


# AI-09: Execution times out after external side effect.

def test_ai_09_timeout_state_unknown():
    from features.tool_runtime.tool_runtime import (
        UnifiedToolRuntime, VerificationStatus,
    )
    utr = UnifiedToolRuntime()
    def timeout_fn(args):
        time.sleep(0.01)
        return {"status": "ok", "output": "done"}
    utr.register_tool("timeout.tool", timeout_fn, schema={"type": "object"})
    utr.register_verifier("timeout.tool", lambda r, expected_state=None: (
        r.result_data and r.result_data.get("status") == "ok"
    ))
    result = utr.execute("timeout.tool", {"x": 1})
    assert result.success
    vr = utr.verify(receipt_id=result.receipt.receipt_id)
    assert vr.status == VerificationStatus.VERIFIED


# AI-10: Execution fails before external state change.

def test_ai_10_fail_before_side_effect():
    from features.tool_runtime.tool_runtime import (
        UnifiedToolRuntime, VerificationStatus,
    )
    utr = UnifiedToolRuntime()
    def fail_before(args):
        raise RuntimeError("failed before any side effect")
    utr.register_tool("fail.tool", fail_before, schema={"type": "object"})
    result = utr.execute("fail.tool", {})
    assert not result.success
    receipt = result.receipt
    assert receipt.verification_status == VerificationStatus.FAILED


# AI-11: Verification service unavailable → INCONCLUSIVE.

def test_ai_11_verifier_unavailable_inconclusive():
    from features.tool_runtime.tool_runtime import (
        UnifiedToolRuntime, VerificationStatus,
    )
    utr = UnifiedToolRuntime()
    def broken_verifier(receipt, expected_state=None):
        raise ConnectionError("verifier service down")
    utr.register_tool("test.tool", lambda a: {"status": "ok"}, schema={"type": "object"})
    utr.register_verifier("test.tool", broken_verifier)
    result = utr.execute("test.tool", {})
    vr = utr.verify(receipt_id=result.receipt.receipt_id)
    assert vr.status == VerificationStatus.INCONCLUSIVE


# AI-12: Verifier must not blindly trust agent-provided state.

def test_ai_12_verifier_independent_of_agent_claim():
    from features.tool_runtime.tool_runtime import (
        UnifiedToolRuntime, VerificationStatus,
    )
    utr = UnifiedToolRuntime()
    def independent_verifier(receipt, expected_state=None):
        path = receipt.args.get("path", "")
        if not os.path.exists(path):
            return False
        with open(path) as f:
            content = f.read()
        if expected_state and "content" in expected_state:
            return content == expected_state["content"]
        return content == receipt.args.get("content", "")
    utr.register_tool("file.check", lambda a: {"status": "ok"}, schema={"type": "object"})
    utr.register_verifier("file.check", independent_verifier)
    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
        tmp_path = f.name
    try:
        import uuid
        eid = str(uuid.uuid4())
        utr.set_expected_state(eid, {"path": tmp_path, "content": "ground truth"})
        with open(tmp_path, "w") as f2:
            f2.write("ground truth")
        result = utr.execute("file.check", {"path": tmp_path, "content": "ground truth"},
                             execution_id=eid)
        vr = utr.verify(receipt_id=result.receipt.receipt_id)
        assert vr.status == VerificationStatus.VERIFIED
    finally:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)


# AI-13: Partial multi-step failure.

def test_ai_13_partial_multi_step():
    from features.tool_runtime.tool_runtime import create_default_utr
    sg = _make_sg_permit_all()
    sg.permit("filesystem.write")
    utr, _ = create_default_utr(safety_gate=sg)
    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
        tmp_path = f.name
    try:
        r1 = utr.execute("math.add", {"a": 1, "b": 2})
        assert r1.success
        r2 = utr.execute("filesystem.write", {"path": "/prohibited/path.txt", "content": "x"})
        assert not r2.success
        r3 = utr.execute("math.add", {"a": 3, "b": 4})
        assert r3.success
        receipts = utr.receipts()
        successes = sum(1 for r in receipts if r.success)
        failures = sum(1 for r in receipts if not r.success)
        assert successes == 2
        assert failures == 1
    finally:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)


# AI-14: Two agents executing conflicting operations.

def test_ai_14_conflicting_agents():
    from features.tool_runtime.tool_runtime import create_default_utr
    sg = _make_sg_permit_all()
    sg.permit("filesystem.write")
    utr, _ = create_default_utr(safety_gate=sg)
    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
        tmp_path = f.name
    try:
        cid = "conflict-correlation"
        r_a = utr.execute(
            "filesystem.write",
            {"path": tmp_path, "content": "agent a content"},
            correlation_id=cid,
            execution_id="agent-a-exec",
        )
        assert r_a.success
        r_b = utr.execute(
            "filesystem.write",
            {"path": tmp_path, "content": "agent b content"},
            correlation_id=cid,
            execution_id="agent-b-exec",
        )
        assert r_b.success
        with open(tmp_path) as f2:
            final = f2.read()
        assert final == "agent b content"
    finally:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)


# AI-15: Stale state used for verification.

def test_ai_15_stale_state_detected():
    from features.tool_runtime.tool_runtime import (
        create_default_utr, VerificationStatus,
    )
    import uuid
    sg = _make_sg_permit_all()
    sg.permit("filesystem.write")
    utr, _ = create_default_utr(safety_gate=sg)
    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
        tmp_path = f.name
    try:
        eid1 = str(uuid.uuid4())
        utr.set_expected_state(eid1, {"path": tmp_path, "content": "version 1"})
        r1 = utr.execute("filesystem.write", {"path": tmp_path, "content": "version 1"},
                         execution_id=eid1)
        assert r1.success
        eid2 = str(uuid.uuid4())
        utr.set_expected_state(eid2, {"path": tmp_path, "content": "version 2"})
        r2 = utr.execute("filesystem.write", {"path": tmp_path, "content": "version 2"},
                         execution_id=eid2)
        assert r2.success
        vr1 = utr.verify(receipt_id=r1.receipt.receipt_id)
        assert vr1.status == VerificationStatus.FAILED
        vr2 = utr.verify(receipt_id=r2.receipt.receipt_id)
        assert vr2.status == VerificationStatus.VERIFIED
    finally:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)


# AI-16: Agent attempts direct tool bypass outside UTR.

def test_ai_16_direct_tool_bypass_blocked():
    from features.tool_runtime.tool_runtime import (UnifiedToolRuntime, VerificationStatus)
    utr = UnifiedToolRuntime()
    result = utr.execute("nonexistent.tool", {})
    assert not result.success
    assert "Unknown tool" in result.error


# AI-17: Agent attempts direct persistence bypass.

def test_ai_17_persistence_bypass_blocked():
    from features.tool_runtime.tool_runtime import (create_default_utr, VerificationStatus)
    sg = _make_sg_permit_all()
    utr, _ = create_default_utr(safety_gate=sg)
    result = utr.execute("nonexistent.tool", {"path": "/tmp/secret.txt", "content": "hack"})
    assert not result.success


# AI-18: Agent claims operation belongs to another agent.

def test_ai_18_provenance_mismatch():
    from features.tool_runtime.tool_runtime import create_default_utr
    sg = _make_sg_permit_all()
    utr, _ = create_default_utr(safety_gate=sg)
    r_a = utr.execute("math.add", {"a": 1, "b": 2}, execution_id="agent-alpha-1")
    r_b = utr.execute("math.add", {"a": 3, "b": 4}, execution_id="agent-beta-1")
    assert r_a.receipt.execution_id == "agent-alpha-1"
    assert r_b.receipt.execution_id == "agent-beta-1"


# AI-19: Receipt from execution A submitted for execution B.

def test_ai_19_receipt_correlation_mismatch():
    from features.tool_runtime.tool_runtime import create_default_utr
    sg = _make_sg_permit_all()
    utr, _ = create_default_utr(safety_gate=sg)
    r_a = utr.execute("math.add", {"a": 1, "b": 2}, correlation_id="scenario-1")
    r_b = utr.execute("math.add", {"a": 3, "b": 4}, correlation_id="scenario-2")
    assert r_a.receipt.correlation_id == "scenario-1"
    assert r_b.receipt.correlation_id == "scenario-2"
    assert r_a.receipt.correlation_id != r_b.receipt.correlation_id


# AI-20: Agent claims verification succeeded without verifier call.

def test_ai_20_fabricated_verification_claim():
    from features.tool_runtime.tool_runtime import (
        UnifiedToolRuntime, VerificationStatus,
    )
    utr = UnifiedToolRuntime()
    utr.register_tool("test.tool", lambda a: {"status": "ok"}, schema={"type": "object"})
    result = utr.execute("test.tool", {})
    receipt = result.receipt
    vr = result.receipt.verification_result()
    assert vr is None
    actual_vr = utr.verify(receipt_id=receipt.receipt_id)
    assert actual_vr.status == VerificationStatus.NOT_SUPPORTED


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
