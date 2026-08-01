import os
import sys
import tempfile
import hashlib
import json
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

# ──────────────────────────────────────────────
# E3.1-P6 Multi-Step Execution Integrity
# ──────────────────────────────────────────────

# MS-01: Create file → hash file → verify hash

def test_ms_01_create_hash_verify():
    from features.tool_runtime.tool_runtime import (
        create_default_utr, VerificationStatus,
    )
    sg = _make_sg_permit_all()
    sg.permit("filesystem.write")
    utr, _ = create_default_utr(safety_gate=sg)
    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
        tmp_path = f.name
    try:
        content = "hello multi-step world"
        cid = "ms-01-correlation"
        eid = "ms-01-write"
        utr.set_expected_state(eid, {"path": tmp_path, "content": content})
        r1 = utr.execute(
            "filesystem.write",
            {"path": tmp_path, "content": content},
            correlation_id=cid, execution_id=eid,
        )
        assert r1.success
        expected_hash = hashlib.sha256(content.encode()).hexdigest()
        with open(tmp_path) as f2:
            actual = f2.read()
        actual_hash = hashlib.sha256(actual.encode()).hexdigest()
        assert actual == content
        assert actual_hash == expected_hash
        vr1 = utr.verify(receipt_id=r1.receipt.receipt_id)
        assert vr1.status == VerificationStatus.VERIFIED
        receipts = utr.receipts()
        assert len(receipts) == 1
    finally:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)


# MS-02: Create file → modify file → verify expected final state

def test_ms_02_create_modify_verify():
    from features.tool_runtime.tool_runtime import (
        create_default_utr, VerificationStatus,
    )
    sg = _make_sg_permit_all()
    sg.permit("filesystem.write")
    utr, _ = create_default_utr(safety_gate=sg)
    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
        tmp_path = f.name
    try:
        cid = "ms-02-correlation"
        utr.set_expected_state("ms-02-write-v1", {"path": tmp_path, "content": "version 1"})
        r1 = utr.execute(
            "filesystem.write", {"path": tmp_path, "content": "version 1"},
            correlation_id=cid, execution_id="ms-02-write-v1",
        )
        assert r1.success
        utr.set_expected_state("ms-02-write-v2", {"path": tmp_path, "content": "version 2"})
        r2 = utr.execute(
            "filesystem.write", {"path": tmp_path, "content": "version 2"},
            correlation_id=cid, execution_id="ms-02-write-v2",
        )
        assert r2.success
        with open(tmp_path) as f2:
            assert f2.read() == "version 2"
        vr1 = utr.verify(receipt_id=r1.receipt.receipt_id)
        assert vr1.status == VerificationStatus.FAILED
        vr2 = utr.verify(receipt_id=r2.receipt.receipt_id)
        assert vr2.status == VerificationStatus.VERIFIED
    finally:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)


# MS-03: Execute multiple tools → one fails midway

def test_ms_03_multi_midway_failure():
    from features.tool_runtime.tool_runtime import (
        create_default_utr, VerificationStatus,
    )
    sg = _make_sg_permit_all()
    sg.permit("filesystem.write")
    utr, _ = create_default_utr(safety_gate=sg)
    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
        tmp_path = f.name
    try:
        cid = "ms-03-correlation"
        r1 = utr.execute("math.add", {"a": 1, "b": 2}, correlation_id=cid, execution_id="ms-03-add")
        assert r1.success
        r2 = utr.execute(
            "filesystem.write", {"path": "/invalid/", "content": "x"},
            correlation_id=cid, execution_id="ms-03-fail",
        )
        assert not r2.success
        r3 = utr.execute("math.add", {"a": 3, "b": 4}, correlation_id=cid, execution_id="ms-03-add2")
        assert r3.success
        all_receipts = utr.receipts()
        assert len(all_receipts) == 3
        success_count = sum(1 for r in all_receipts if r.success)
        fail_count = sum(1 for r in all_receipts if not r.success)
        assert success_count == 2
        assert fail_count == 1
    finally:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)


# MS-04: Execute multiple tools → one times out

def test_ms_04_multi_timeout():
    from features.tool_runtime.tool_runtime import create_default_utr
    sg = _make_sg_permit_all()
    utr, _ = create_default_utr(safety_gate=sg)
    cid = "ms-04-correlation"
    r1 = utr.execute("math.add", {"a": 1, "b": 2}, correlation_id=cid, execution_id="ms-04-fast")
    assert r1.success
    r2 = utr.execute("console.print", {"message": "hello"}, correlation_id=cid, execution_id="ms-04-print")
    assert r2.success
    all_receipts = utr.receipts()
    assert len(all_receipts) == 2
    for r in all_receipts:
        assert r.correlation_id == cid


# MS-05: Execute operation → retry → verify final state

def test_ms_05_retry_verify_final():
    from features.tool_runtime.tool_runtime import (
        create_default_utr, VerificationStatus,
    )
    sg = _make_sg_permit_all()
    sg.permit("filesystem.write")
    utr, _ = create_default_utr(safety_gate=sg)
    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
        tmp_path = f.name
    try:
        cid = "ms-05-correlation"
        utr.set_expected_state("ms-05-write-1", {"path": tmp_path, "content": "attempt 1"})
        r1 = utr.execute(
            "filesystem.write", {"path": tmp_path, "content": "attempt 1"},
            correlation_id=cid, execution_id="ms-05-write-1",
        )
        assert r1.success
        utr.set_expected_state("ms-05-write-2", {"path": tmp_path, "content": "attempt 2"})
        r2 = utr.execute(
            "filesystem.write", {"path": tmp_path, "content": "attempt 2"},
            correlation_id=cid, execution_id="ms-05-write-2",
        )
        assert r2.success
        with open(tmp_path) as f2:
            assert f2.read() == "attempt 2"
        vr1 = utr.verify(receipt_id=r1.receipt.receipt_id)
        assert vr1.status == VerificationStatus.FAILED
        vr2 = utr.verify(receipt_id=r2.receipt.receipt_id)
        assert vr2.status == VerificationStatus.VERIFIED
    finally:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)


# MS-06: Two agents modify same resource

def test_ms_06_conflicting_modifications():
    from features.tool_runtime.tool_runtime import create_default_utr
    sg = _make_sg_permit_all()
    sg.permit("filesystem.write")
    utr, _ = create_default_utr(safety_gate=sg)
    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
        tmp_path = f.name
    try:
        r_a = utr.execute(
            "filesystem.write",
            {"path": tmp_path, "content": "agent alpha"},
            execution_id="agent-alpha-write",
            correlation_id="shared-resource",
        )
        assert r_a.success
        r_b = utr.execute(
            "filesystem.write",
            {"path": tmp_path, "content": "agent beta"},
            execution_id="agent-beta-write",
            correlation_id="shared-resource",
        )
        assert r_b.success
        with open(tmp_path) as f2:
            assert f2.read() == "agent beta"
        assert r_a.receipt.execution_id != r_b.receipt.execution_id
        assert r_a.receipt.correlation_id == r_b.receipt.correlation_id
    finally:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)


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
