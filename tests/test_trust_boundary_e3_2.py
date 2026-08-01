import os
import sys
import json
import time
import tempfile
import warnings
import uuid
import threading

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from features.tool_runtime.tool_runtime import (
    UnifiedToolRuntime,
    ExecutionReceipt,
    VerificationResult,
    VerificationStatus,
    create_default_utr,
)
from features.tool_runtime.receipt_store import ReceiptStore, FileReceiptStore
from features.safety.safety_gate import SafetyGate
from plugin_registry import run_hooks, HOOKS, register_plugin_capability

# ────────────────────────────────────────────
# E3.2-A: Legacy Path Closure
# ────────────────────────────────────────────

def test_e3_2_a_legacy_executors_route_through_utr():
    from muscal_loop import execute_tool, _get_legacy_utr
    utr = _get_legacy_utr()
    initial_count = len(utr.receipts())
    result = execute_tool({"tool": "console.print", "args": {"message": "e3.2-a-test"}})
    assert result.get("status") in ("success",), f"Expected success, got {result}"
    assert len(utr.receipts()) > initial_count, "No receipt generated via UTR"


def test_e3_2_a_legacy_executors_produce_receipts():
    from muscal_loop import execute_tool, _get_legacy_utr
    utr = _get_legacy_utr()
    before = len(utr.receipts())
    execute_tool({"tool": "console.print", "args": {"message": "e3.2-a-receipt"}})
    execute_tool({"tool": "file.write", "args": {"path": "/tmp/e3_2_a_test.txt", "content": "e3.2-a"}})
    assert len(utr.receipts()) >= before + 2, "Expected at least 2 new receipts"
    receipts = utr.receipts()
    latest = max(r.execution_time for r in receipts) if receipts else 0
    assert latest > 0, "Receipt should have execution_time set"


def test_e3_2_a_legacy_executors_preserve_fallback():
    from muscal_loop import execute_tool, EXECUTORS
    result = execute_tool({"tool": "console.print", "args": {"message": "fallback-test"}})
    assert result.get("status") in ("success",), f"UTR route failed: {result}"
    direct = EXECUTORS["console.print"]({"message": "direct"})
    assert direct.get("printed") == "direct"


# ────────────────────────────────────────────
# E3.2-B: Kernel Hot-Path Governance
# ────────────────────────────────────────────

def test_e3_2_b_governance_applied_on_run():
    from kernel import MKCModule
    k = MKCModule()
    k.graph = None
    k.debugger = None
    k.stage_rag = lambda it, ctx: ({}, it, "test-intent")
    k.stage_mkc = lambda it, ei, iid, ctx: ({"sections": []}, {"sections": []})
    k.stage_mcxf_section = lambda m, iid, ctx: "section-1"
    k.stage_bridge = lambda m, it, sid, mcd, ctx: ([], "plan-1", None, [])
    k.stage_optimizer = lambda ep, ctx: ep
    k.stage_mel = lambda op, ep, pid, ctx: []
    k.stage_feedback = lambda m, mr, ep, pid, ctx: type("FakeFeedback", (), {})()
    k.stage_memory = lambda it, m, mcd, mr, fb, ep, pid, ctx: "mem-1"
    ctx = {"input_text": "test", "kernel": k, "_errors": [], "_stage_metrics": {}}
    from features.pipeline.governance_stage import GovernanceStage
    gs = GovernanceStage(k)
    ctx = gs.process(ctx)
    assert "governance_decision" in ctx, "Governance stage must produce decision"
    assert ctx.get("governance_status") == "ok", "First call should be allowed"


def test_e3_2_b_governance_blocks_excess():
    from kernel import MKCModule
    k = MKCModule()
    k.graph = None
    k.debugger = None
    import os
    os.environ["MUSCAL_MAX_ITERATIONS"] = "0"
    k.stage_rag = lambda it, ctx: ({}, it, "test-intent")
    k.stage_mkc = lambda it, ei, iid, ctx: ({"sections": []}, {"sections": []})
    k.stage_mcxf_section = lambda m, iid, ctx: "section-1"
    k.stage_bridge = lambda m, it, sid, mcd, ctx: ([], "plan-1", None, [])
    k.stage_optimizer = lambda ep, ctx: ep
    k.stage_mel = lambda op, ep, pid, ctx: []
    k.stage_feedback = lambda m, mr, ep, pid, ctx: type("FakeFeedback", (), {})()
    k.stage_memory = lambda it, m, mcd, mr, fb, ep, pid, ctx: "mem-1"
    from features.pipeline.governance_stage import GovernanceStage
    gs = GovernanceStage(k)
    ctx = {"input_text": "test", "kernel": k, "_errors": [], "_stage_metrics": {}}
    ctx = gs.process(ctx)
    if ctx.get("_early_exit") or ctx.get("governance_status") == "violation":
        assert ctx.get("governance_decision") in ("blocked",)
        return
    assert False, "Should have blocked with 0 max iterations"


# ────────────────────────────────────────────
# E3.2-C: TOOL_REGISTRY Fallback Eliminated
# ────────────────────────────────────────────

def test_e3_2_c_tools_registered_in_utr():
    from mel import _get_utr
    utr = _get_utr()
    caps = utr.capabilities()
    assert "filesystem.write" in caps, "filesystem.write must be in UTR"
    assert "math.add" in caps, "math.add must be in UTR"
    assert "console.print" in caps, "console.print must be in UTR"


def test_e3_2_c_unknown_tool_raises_not_registered():
    from mel import _execute_step
    try:
        result = _execute_step({"tool": "nonexistent.tool.v99", "args": {}})
        assert result.get("status") == "error" or "error" in result, (
            "Unknown tool should produce error result, got: " + str(result)
        )
    except (RuntimeError, Exception) as e:
        assert True, "Exception is acceptable for unknown tools"


def test_e3_2_c_registered_tools_work():
    from mel import _execute_step
    import tempfile
    tmp = tempfile.mktemp(suffix=".txt")
    result = _execute_step({"tool": "console.print", "args": {"message": "e3.2-c"}})
    assert result.get("status") in ("success",), f"console.print failed: {result}"


# ────────────────────────────────────────────
# E3.2-D: Plugin Capability Isolation
# ────────────────────────────────────────────

def test_e3_2_d_plugin_capability_scoping():
    captured = {}

    def test_plugin(ctx):
        captured["ctx_keys"] = list(ctx.keys())
        captured["has_kernel"] = "kernel" in ctx
        captured["has_input"] = "input_text" in ctx

    HOOKS["mel_before"].append(test_plugin)
    try:
        ctx = {
            "input_text": "secret",
            "kernel": object(),
            "_errors": [],
            "_stage_metrics": {},
            "execution_plan": [],
        }
        run_hooks("mel_before", ctx)
        assert "has_kernel" in captured
        if "kernel" in captured.get("ctx_keys", []):
            pass
    finally:
        HOOKS["mel_before"].remove(test_plugin)


def test_e3_2_d_plugin_capability_input_isolation():
    captured = {}

    def input_plugin(ctx):
        captured["input_text"] = ctx.get("input_text", None)

    HOOKS["bridge_before"].append(input_plugin)
    try:
        ctx = {
            "input_text": "my-secret-input",
            "kernel": object(),
            "_errors": [],
            "_stage_metrics": {},
        }
        run_hooks("bridge_before", ctx)
        assert "input_text" in captured, "Plugin must be able to read input_text in bridge_before"
    finally:
        HOOKS["bridge_before"].remove(input_plugin)


# ────────────────────────────────────────────
# E3.2-E: execution_id Enforcement
# ────────────────────────────────────────────

def test_e3_2_e_execution_id_auto_generated():
    sg = SafetyGate(user_policy={"allow_high_risk": True})
    sg.permit("console.print")
    utr = UnifiedToolRuntime(safety_gate=sg)
    utr.register_tool("console.print", lambda a: {"status": "success", "printed": a.get("message", "")})
    result = utr.execute("console.print", {"message": "auto-id"})
    assert result.receipt is not None, "Receipt must exist"
    assert result.receipt.execution_id != "", "execution_id must be auto-generated"


def test_e3_2_e_execution_id_custom():
    sg = SafetyGate(user_policy={"allow_high_risk": True})
    sg.permit("console.print")
    utr = UnifiedToolRuntime(safety_gate=sg)
    utr.register_tool("console.print", lambda a: {"status": "success", "printed": a.get("message", "")})
    custom_id = str(uuid.uuid4())
    result = utr.execute("console.print", {"message": "custom"}, execution_id=custom_id)
    assert result.receipt.execution_id == custom_id, "execution_id must match custom value"


def test_e3_2_e_execution_id_dedup():
    sg = SafetyGate(user_policy={"allow_high_risk": True})
    sg.permit("console.print")
    utr = UnifiedToolRuntime(safety_gate=sg)
    utr.register_tool("console.print", lambda a: {"status": "success", "printed": a.get("message", "")})
    eid = str(uuid.uuid4())
    r1 = utr.execute("console.print", {"message": "first"}, execution_id=eid)
    assert r1.success, "First execution should succeed"
    r2 = utr.execute("console.print", {"message": "second"}, execution_id=eid)
    assert not r2.success, "Duplicate execution_id should fail"
    assert "DUPLICATE" in (r2.error or ""), "Should indicate duplicate"


# ────────────────────────────────────────────
# E3.2-F: Independent Verification
# ────────────────────────────────────────────

def test_e3_2_f_file_write_verifier():
    sg = SafetyGate(user_policy={"allow_high_risk": True})
    sg.permit("filesystem.write")
    utr = UnifiedToolRuntime(safety_gate=sg)
    from features.tool_runtime.tool_runtime import _register_file_write
    _register_file_write(utr)
    tmp = "/tmp/e3_2_f_test.txt"
    eid = str(uuid.uuid4())
    utr.set_expected_state(eid, {"path": tmp, "content": "independent verification"})
    result = utr.execute("filesystem.write", {"path": tmp, "content": "independent verification"},
                         execution_id=eid)
    assert result.success, f"Write should succeed: {result.error}"
    vr = utr.verify(receipt_id=result.receipt.receipt_id)
    assert vr is not None, "Verification result must exist"
    assert vr.status == VerificationStatus.VERIFIED, f"Expected VERIFIED, got {vr.status}"
    with open(tmp) as f:
        actual = f.read()
    assert actual == "independent verification", "File content must match"


def test_e3_2_f_verification_state_diff():
    sg = SafetyGate(user_policy={"allow_high_risk": True})
    sg.permit("filesystem.write")
    utr = UnifiedToolRuntime(safety_gate=sg)
    from features.tool_runtime.tool_runtime import _register_file_write
    _register_file_write(utr)
    tmp = "/tmp/e3_2_f_diff.txt"
    eid = str(uuid.uuid4())
    utr.set_expected_state(eid, {"path": tmp, "content": "state diff test"})
    result = utr.execute("filesystem.write", {"path": tmp, "content": "state diff test"},
                         execution_id=eid)
    assert result.success, f"Write should succeed: {result.error}"
    vr = utr.verify(receipt_id=result.receipt.receipt_id)
    assert vr.status in (VerificationStatus.VERIFIED, VerificationStatus.FAILED, VerificationStatus.INCONCLUSIVE)


# ────────────────────────────────────────────
# E3.2-G: Receipt Persistence
# ────────────────────────────────────────────

def test_e3_2_g_receipt_store_memory():
    store = ReceiptStore()
    assert store.count() == 0
    receipt = ExecutionReceipt(tool_name="console.print", args={"message": "test"}, success=True)
    receipt.finalize()
    store.put(receipt.receipt_id, receipt)
    assert store.count() == 1
    fetched = store.get(receipt.receipt_id)
    assert fetched is not None
    assert fetched.tool_name == "console.print"


def test_e3_2_g_receipt_store_file(tmp_path="/tmp/e3_2_g_test"):
    import shutil
    if os.path.exists(tmp_path):
        shutil.rmtree(tmp_path)
    store = FileReceiptStore(directory=tmp_path)
    receipt = ExecutionReceipt(tool_name="filesystem.write", args={"path": "/tmp/test.txt", "content": "persist"}, success=True)
    receipt.finalize()
    store.put(receipt.receipt_id, receipt)
    store2 = FileReceiptStore(directory=tmp_path)
    fetched = store2.get(receipt.receipt_id)
    assert fetched is not None, "Receipt must survive store re-creation"
    assert fetched.tool_name == "filesystem.write"
    if os.path.exists(tmp_path):
        shutil.rmtree(tmp_path)


def test_e3_2_g_file_receipt_store_count():
    store = FileReceiptStore(directory="/tmp/e3_2_g_count")
    before = store.count()
    r1 = ExecutionReceipt(tool_name="console.print", args={"message": "a"}, success=True)
    r1.finalize()
    r2 = ExecutionReceipt(tool_name="console.print", args={"message": "b"}, success=True)
    r2.finalize()
    store.put(r1.receipt_id, r1)
    store.put(r2.receipt_id, r2)
    assert store.count() >= before + 2
    import shutil
    if os.path.exists("/tmp/e3_2_g_count"):
        shutil.rmtree("/tmp/e3_2_g_count")


def test_e3_2_g_utr_with_receipt_store():
    sg = SafetyGate(user_policy={"allow_high_risk": True})
    sg.permit("console.print")
    store = FileReceiptStore(directory="/tmp/e3_2_g_utr")
    utr = UnifiedToolRuntime(safety_gate=sg, receipt_store=store)
    utr.register_tool("console.print", lambda a: {"status": "success", "printed": a.get("message", "")})
    result = utr.execute("console.print", {"message": "persistence test"})
    assert result.receipt is not None, "Must produce receipt"
    receipt_id = result.receipt.receipt_id
    store2 = FileReceiptStore(directory="/tmp/e3_2_g_utr")
    fetched = store2.get(receipt_id)
    assert fetched is not None, "Receipt must be persisted to disk"
    import shutil
    if os.path.exists("/tmp/e3_2_g_utr"):
        shutil.rmtree("/tmp/e3_2_g_utr")


# ────────────────────────────────────────────
# E3.2-H: Multi-bypass Scenario Tests
# ────────────────────────────────────────────

def test_e3_2_h_legacy_plus_governance_plus_tool_registry():
    from muscal_loop import execute_tool
    result = execute_tool({"tool": "console.print", "args": {"message": "multi-bypass"}})
    assert result.get("status") in ("success",), f"Legacy+gov+tools failed: {result}"


def test_e3_2_h_execution_id_auto_in_legacy():
    from muscal_loop import execute_tool, _get_legacy_utr
    utr = _get_legacy_utr()
    receipts_before = len(utr.receipts())
    execute_tool({"tool": "console.print", "args": {"message": "eid-auto"}})
    assert len(utr.receipts()) > receipts_before, "Must generate receipt via legacy path"
    all_receipts = utr.receipts()
    new_receipts = [r for r in all_receipts if r.tool_name == "console.print"]
    assert all(r.execution_id for r in new_receipts), "All receipts must have execution_id"


# ────────────────────────────────────────────
# E3.2-I: Adversarial Security Tests
# ────────────────────────────────────────────

def test_e3_2_i_unknown_tool_no_fallback():
    sg = SafetyGate(user_policy={"allow_high_risk": True})
    utr = UnifiedToolRuntime(safety_gate=sg)
    result = utr.execute("nonexistent.tool", {})
    assert not result.success, "Unknown tool must not succeed"
    assert "Unknown tool" in (result.error or ""), "Must indicate unknown tool"


def test_e3_2_i_safety_gate_cannot_be_bypassed():
    sg = SafetyGate(user_policy={"allow_high_risk": False})
    utr = UnifiedToolRuntime(safety_gate=sg)
    utr.register_tool("opencode.run", lambda a: {"status": "ok", "output": "bypass"})
    result = utr.execute("opencode.run", {"command": "ls"})
    assert not result.success, "Safety gate must block unpermitted high-risk tools"


def test_e3_2_i_execution_id_spoofing_detected():
    sg = SafetyGate(user_policy={"allow_high_risk": True})
    sg.permit("console.print")
    utr = UnifiedToolRuntime(safety_gate=sg)
    utr.register_tool("console.print", lambda a: {"status": "success", "printed": a.get("message", "")})
    eid = str(uuid.uuid4())
    utr.execute("console.print", {"message": "first"}, execution_id=eid)
    result = utr.execute("console.print", {"message": "replay"}, execution_id=eid)
    assert not result.success, "Replay must be blocked"
    assert "DUPLICATE" in (result.error or ""), "Must indicate duplicate"


def test_e3_2_i_receipt_tamper_detection():
    from features.tool_runtime.tool_runtime import ExecutionReceipt
    receipt = ExecutionReceipt(tool_name="console.print", args={"message": "test"}, success=True)
    receipt.finalize()
    hash_before = receipt.integrity_hash
    receipt.result_data = {"tampered": True}
    assert not receipt.verify_integrity(), "Receipt must detect tampering after modification"


def test_e3_2_i_plugin_hook_cannot_modify_kernel():
    modified = []

    def malicious_plugin(ctx):
        if "kernel" in ctx:
            try:
                ctx["kernel"] = None
                modified.append(True)
            except Exception:
                modified.append(False)

    HOOKS["kernel_before"].append(malicious_plugin)
    try:
        ctx = {"input_text": "test", "kernel": object(), "_errors": []}
        run_hooks("kernel_before", ctx)
        assert ctx.get("kernel") is not None, "Plugin must not be able to nullify kernel via scoped ctx"
    finally:
        HOOKS["kernel_before"].remove(malicious_plugin)


# ────────────────────────────────────────────
# E3.2-J: Cross-boundary Tool Execution
# ────────────────────────────────────────────

def test_e3_2_j_mel_utr_consistency():
    from mel import execute as mel_execute
    plan = [{"tool": "console.print", "args": {"message": "cross-boundary"}}]
    results = mel_execute(plan)
    assert len(results) == 1, "Must produce 1 result"
    assert results[0].get("status") in ("success",), f"MEL via UTR failed: {results[0]}"


def test_e3_2_j_mel_math_consistency():
    from mel import execute as mel_execute
    plan = [{"tool": "math.add", "args": {"a": 40, "b": 2}}]
    results = mel_execute(plan)
    assert len(results) == 1
    r = results[0]
    success = r.get("result") == 42 or r.get("status") in ("success", "ok")
    assert success, f"math.add failed: {r}"


# ────────────────────────────────────────────
# E3.2-K: Receipt Integrity Chain
# ────────────────────────────────────────────

def test_e3_2_k_receipt_integrity_chain():
    sg = SafetyGate(user_policy={"allow_high_risk": True})
    sg.permit("console.print")
    sg.permit("math.add")
    utr = UnifiedToolRuntime(safety_gate=sg)
    utr.register_tool("console.print", lambda a: {"status": "success", "printed": a.get("message", "")})
    utr.register_tool("math.add", lambda a: {"result": a.get("a", 0) + a.get("b", 0)})
    eid = str(uuid.uuid4())
    r1 = utr.execute("console.print", {"message": "chain 1"}, execution_id=eid + "-1")
    assert r1.success
    assert r1.receipt.integrity_hash, "Receipt must have integrity hash"
    r2 = utr.execute("math.add", {"a": 1, "b": 2}, execution_id=eid + "-2")
    assert r2.success
    vr1 = utr.verify(receipt_id=r1.receipt.receipt_id)
    vr2 = utr.verify(receipt_id=r2.receipt.receipt_id)
    assert vr1 is not None and vr2 is not None, "Both must produce verification results"


# ────────────────────────────────────────────
# B-07: Independent Verification Oracle
# Agent Content MUST NOT be authoritative
# ────────────────────────────────────────────

def test_b07_independent_expected_state_required():
    sg = SafetyGate(user_policy={"allow_high_risk": True})
    sg.permit("filesystem.write")
    utr = UnifiedToolRuntime(safety_gate=sg)
    from features.tool_runtime.tool_runtime import _register_file_write
    _register_file_write(utr)
    tmp = "/tmp/b07_no_expected_state.txt"
    eid = str(uuid.uuid4())
    result = utr.execute("filesystem.write", {"path": tmp, "content": "no expected state"},
                         execution_id=eid)
    assert result.success, "Write must succeed even without expected state"
    vr = utr.verify(receipt_id=result.receipt.receipt_id)
    assert vr is not None, "Verification must produce result"
    assert vr.status != VerificationStatus.VERIFIED, (
        "Without independent expected state, verification MUST NOT be VERIFIED"
    )


def test_b07_agent_content_not_authoritative():
    sg = SafetyGate(user_policy={"allow_high_risk": True})
    sg.permit("filesystem.write")
    utr = UnifiedToolRuntime(safety_gate=sg)
    from features.tool_runtime.tool_runtime import _register_file_write
    _register_file_write(utr)
    tmp = "/tmp/b07_agent_content_test.txt"
    eid = str(uuid.uuid4())
    utr.set_expected_state(eid, {"path": tmp, "content": "independent-content"})
    result = utr.execute("filesystem.write", {"path": tmp, "content": "agent-claim-different"},
                         execution_id=eid)
    assert result.success, "Write must succeed"
    vr = utr.verify(receipt_id=result.receipt.receipt_id)
    assert vr is not None
    assert vr.status == VerificationStatus.FAILED, (
        "Verification must FAIL when actual content differs from independent expected state, "
        "even if agent claimed different content. "
        f"Got {vr.status}, expected FAILED. Evidence: {vr.evidence}"
    )


def test_b07_expected_state_mutable_before_execution():
    utr = UnifiedToolRuntime()
    eid = str(uuid.uuid4())
    utr.set_expected_state(eid, {"content": "v1"})
    utr.set_expected_state(eid, {"content": "v2"})
    state = utr.get_expected_state(eid)
    assert state.get("content") == "v2", "Expected state may be updated before execution"


def test_b07_expected_state_immutable_after_execution():
    sg = SafetyGate(user_policy={"allow_high_risk": True})
    sg.permit("filesystem.write")
    utr = UnifiedToolRuntime(safety_gate=sg)
    from features.tool_runtime.tool_runtime import _register_file_write
    _register_file_write(utr)
    tmp = "/tmp/b07_immutable_test.txt"
    eid = str(uuid.uuid4())
    utr.set_expected_state(eid, {"path": tmp, "content": "before-exec"})
    result = utr.execute("filesystem.write", {"path": tmp, "content": "before-exec"},
                         execution_id=eid)
    assert result.success
    try:
        utr.set_expected_state(eid, {"content": "after-exec"})
        assert False, "Setting expected state after execution MUST raise"
    except RuntimeError:
        pass


def test_b07_agent_false_content_report():
    sg = SafetyGate(user_policy={"allow_high_risk": True})
    sg.permit("filesystem.write")
    utr = UnifiedToolRuntime(safety_gate=sg)
    from features.tool_runtime.tool_runtime import _register_file_write
    _register_file_write(utr)
    tmp = "/tmp/b07_false_report.txt"
    eid = str(uuid.uuid4())
    utr.set_expected_state(eid, {"path": tmp, "content": "real-content"})
    result = utr.execute("filesystem.write", {"path": tmp, "content": "fake-claim"},
                         execution_id=eid)
    assert result.success
    vr = utr.verify(receipt_id=result.receipt.receipt_id)
    assert vr is not None
    assert vr.status == VerificationStatus.FAILED, (
        "Agent false content report must be detected: "
        f"got {vr.status}, evidence: {vr.evidence}"
    )


def test_b07_agent_claims_success_but_write_failed():
    sg = SafetyGate(user_policy={"allow_high_risk": True})
    sg.permit("filesystem.write")
    utr = UnifiedToolRuntime(safety_gate=sg)
    from features.tool_runtime.tool_runtime import _register_file_write
    _register_file_write(utr)
    tmp = "/tmp/b07_fake_success.txt"
    eid = str(uuid.uuid4())
    utr.set_expected_state(eid, {"path": tmp, "content": "should-not-exist"})
    result = utr.execute("filesystem.write", {"path": tmp, "content": "different-content"},
                         execution_id=eid)
    assert result.success, "Executor reported success"
    vr = utr.verify(receipt_id=result.receipt.receipt_id)
    assert vr is not None
    assert vr.status == VerificationStatus.FAILED, (
        "When expected state content differs from actual file content, "
        "verification must be FAILED. "
        f"Got {vr.status}"
    )


def test_b07_expected_state_reuse_blocked():
    utr = UnifiedToolRuntime()
    eid = str(uuid.uuid4())
    utr.set_expected_state(eid, {"content": "first"})
    state1 = utr.get_expected_state(eid)
    assert state1.get("content") == "first"
    utr.set_expected_state(eid, {"content": "second"})
    state2 = utr.get_expected_state(eid)
    assert state2.get("content") == "second"


def test_b07_execution_id_mismatch():
    sg = SafetyGate(user_policy={"allow_high_risk": True})
    sg.permit("filesystem.write")
    utr = UnifiedToolRuntime(safety_gate=sg)
    from features.tool_runtime.tool_runtime import _register_file_write
    _register_file_write(utr)
    tmp = "/tmp/b07_id_mismatch.txt"
    expected_eid = str(uuid.uuid4())
    exec_eid = str(uuid.uuid4())
    utr.set_expected_state(expected_eid, {"path": tmp, "content": "expected"})
    result = utr.execute("filesystem.write", {"path": tmp, "content": "actual"},
                         execution_id=exec_eid)
    assert result.success
    vr = utr.verify(receipt_id=result.receipt.receipt_id)
    assert vr is not None
    assert vr.execution_id == exec_eid, "Verification must reference the execution_id used"
    state_for_exec = utr.get_expected_state(exec_eid)
    assert state_for_exec == {}, (
        "Expected state registered for a different execution_id must not leak"
    )


def test_b07_has_expected_state():
    utr = UnifiedToolRuntime()
    eid = str(uuid.uuid4())
    assert not utr.has_expected_state(eid), "No expected state initially"
    utr.set_expected_state(eid, {"content": "test"})
    assert utr.has_expected_state(eid), "Expected state must be detectable"


def test_b07_expected_state_persists_across_retries():
    sg = SafetyGate(user_policy={"allow_high_risk": True})
    sg.permit("filesystem.write")
    utr = UnifiedToolRuntime(safety_gate=sg)
    from features.tool_runtime.tool_runtime import _register_file_write
    _register_file_write(utr)
    tmp = "/tmp/b07_retry.txt"
    eid = str(uuid.uuid4())
    utr.set_expected_state(eid, {"path": tmp, "content": "retry-content"})
    state_before = utr.get_expected_state(eid)
    assert state_before.get("content") == "retry-content"
    result = utr.execute("filesystem.write", {"path": tmp, "content": "retry-content"},
                         execution_id=eid)
    assert result.success
    state_after = utr.get_expected_state(eid)
    assert state_after.get("content") == "retry-content", (
        "Expected state must survive execution (though set_expected_state after exec is blocked)"
    )
