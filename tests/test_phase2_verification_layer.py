import json
import os
import sys
import tempfile
import threading
import time
from pathlib import Path

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import config as _muscal_config

from event_bus import EventBus, EventMessage, EventPriority
from features.identity.execution_context import (
    ExecutionContext,
    get_context_manager,
)
from features.identity.reality import (
    normalize_verification_state,
    validate_state_transition,
)
from features.identity.uuid7 import uuid7, is_uuid7
from features.tool_runtime.tool_runtime import (
    ExecutionReceipt,
    VerificationResult,
    VerificationStatus,
    UnifiedToolRuntime,
)
from features.verification.verifier import (
    Verifier,
    MathVerifier,
    FilesystemVerifier,
    OpenCodeRunVerifier,
    IntegrityVerifier,
    BUILTIN_VERIFIERS,
)
from features.verification.orchestrator import VerificationOrchestrator
from features.verification.rules import (
    VerificationRule,
    HardRuleViolation,
    RuleEngine,
    HARD_RULES,
)
from features.verification import VERIFICATION_LAYER_VERSION


# ═══════════════════════════════════════════════════════════════════════
# K. Verification Layer — Verifier Unit Tests
# ═══════════════════════════════════════════════════════════════════════


class TestVerificationLayerVersion:
    def test_version_defined(self):
        assert VERIFICATION_LAYER_VERSION == "2.0.0"


class TestVerifierContract:
    def test_verifier_is_abstract(self):
        with pytest.raises(TypeError):
            Verifier()

    def test_builtin_verifiers_registered(self):
        assert "math.add" in BUILTIN_VERIFIERS
        assert isinstance(BUILTIN_VERIFIERS["math.add"], MathVerifier)
        assert "filesystem.write" in BUILTIN_VERIFIERS
        assert isinstance(BUILTIN_VERIFIERS["filesystem.write"], FilesystemVerifier)
        assert "file.write" in BUILTIN_VERIFIERS
        assert "opencode.run" in BUILTIN_VERIFIERS
        assert isinstance(BUILTIN_VERIFIERS["opencode.run"], OpenCodeRunVerifier)
        assert "integrity_check" in BUILTIN_VERIFIERS
        assert isinstance(BUILTIN_VERIFIERS["integrity_check"], IntegrityVerifier)

    def test_verifier_has_name(self):
        for name, v in BUILTIN_VERIFIERS.items():
            assert hasattr(v, "name")
            assert v.name in (name, "filesystem.write")


class TestIntegrityVerifier:
    def test_unfinalized_receipt_returns_tampered(self):
        v = IntegrityVerifier()
        receipt = ExecutionReceipt(tool_name="test", args={}, result_data={})
        result = v.verify(receipt)
        assert result.status == VerificationStatus.TAMPERED
        assert result.receipt_id == receipt.receipt_id
        assert result.verifier_id == "integrity_check"

    def test_finalized_valid_receipt_returns_executed(self):
        v = IntegrityVerifier()
        receipt = ExecutionReceipt(tool_name="test", args={"a": 1},
                                    result_data={"result": 2})
        receipt.finalize()
        result = v.verify(receipt)
        assert result.status == VerificationStatus.EXECUTED
        assert result.receipt_id == receipt.receipt_id

    def test_finalized_tampered_receipt_returns_tampered(self):
        v = IntegrityVerifier()
        receipt = ExecutionReceipt(tool_name="math.add", args={"a": 1, "b": 2},
                                    result_data={"result": 3})
        receipt.finalize()
        receipt.result_data = {"result": 999}
        result = v.verify(receipt)
        assert result.status == VerificationStatus.TAMPERED


class TestMathVerifier:
    def test_correct_math_returns_verified(self):
        v = MathVerifier()
        receipt = ExecutionReceipt(tool_name="math.add", args={"a": 2, "b": 3},
                                    result_data={"result": 5})
        result = v.verify(receipt)
        assert result.status == VerificationStatus.VERIFIED
        assert result.expected_state == {"result": 5}
        assert result.observed_state == {"result": 5}

    def test_incorrect_math_returns_failed(self):
        v = MathVerifier()
        receipt = ExecutionReceipt(tool_name="math.add", args={"a": 2, "b": 3},
                                    result_data={"result": 99})
        result = v.verify(receipt)
        assert result.status == VerificationStatus.FAILED
        assert result.expected_state == {"result": 5}
        assert result.observed_state == {"result": 99}

    def test_missing_result_data_returns_failed(self):
        v = MathVerifier()
        receipt = ExecutionReceipt(tool_name="math.add", args={"a": 2, "b": 3})
        result = v.verify(receipt)
        assert result.status == VerificationStatus.FAILED

    def test_verifier_id_is_math_add(self):
        v = MathVerifier()
        receipt = ExecutionReceipt(tool_name="math.add", args={"a": 1, "b": 1},
                                    result_data={"result": 2})
        result = v.verify(receipt)
        assert result.verifier_id == "math.add"


class TestFilesystemVerifier:
    def test_file_exists_returns_verified(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "test.txt")
            with open(path, "w") as f:
                f.write("hello")
            v = FilesystemVerifier(allowed_paths=[tmp])
            receipt = ExecutionReceipt(tool_name="filesystem.write",
                                        args={"path": path},
                                        result_data={"status": "written", "path": path})
            result = v.verify(receipt)
            assert result.status == VerificationStatus.VERIFIED

    def test_file_missing_returns_failed(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "missing.txt")
            v = FilesystemVerifier(allowed_paths=[tmp])
            receipt = ExecutionReceipt(tool_name="filesystem.write",
                                        args={"path": path},
                                        result_data={"status": "written", "path": path})
            result = v.verify(receipt)
            assert result.status == VerificationStatus.FAILED

    def test_content_match_returns_verified(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "match.txt")
            with open(path, "w") as f:
                f.write("expected content")
            v = FilesystemVerifier(allowed_paths=[tmp])
            receipt = ExecutionReceipt(tool_name="filesystem.write",
                                        args={"path": path},
                                        result_data={"status": "written"})
            result = v.verify(receipt, expected_state={"content": "expected content"})
            assert result.status == VerificationStatus.VERIFIED

    def test_content_mismatch_returns_failed(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "mismatch.txt")
            with open(path, "w") as f:
                f.write("actual content")
            v = FilesystemVerifier(allowed_paths=[tmp])
            receipt = ExecutionReceipt(tool_name="filesystem.write",
                                        args={"path": path},
                                        result_data={"status": "written"})
            result = v.verify(receipt, expected_state={"content": "expected content"})
            assert result.status == VerificationStatus.FAILED
            assert result.state_diff.get("content_mismatch") is True

    def test_not_allowed_path_returns_not_supported(self):
        v = FilesystemVerifier(allowed_paths=["/allowed"])
        receipt = ExecutionReceipt(tool_name="filesystem.write",
                                    args={"path": "/etc/passwd"},
                                    result_data={"status": "blocked"})
        result = v.verify(receipt)
        assert result.status == VerificationStatus.NOT_SUPPORTED


class TestOpenCodeRunVerifier:
    def test_ok_status_returns_verified(self):
        v = OpenCodeRunVerifier()
        receipt = ExecutionReceipt(tool_name="opencode.run",
                                    args={"command": "ls"},
                                    result_data={"status": "ok", "output": "file.txt"})
        result = v.verify(receipt)
        assert result.status == VerificationStatus.VERIFIED

    def test_blocked_status_returns_failed(self):
        v = OpenCodeRunVerifier()
        receipt = ExecutionReceipt(tool_name="opencode.run",
                                    args={"command": "rm -rf /"},
                                    result_data={"status": "blocked", "error": "Command not allowed"})
        result = v.verify(receipt)
        assert result.status == VerificationStatus.FAILED

    def test_no_result_data_returns_inconclusive(self):
        v = OpenCodeRunVerifier()
        receipt = ExecutionReceipt(tool_name="opencode.run",
                                    args={"command": "ls"},
                                    result_data=None)
        result = v.verify(receipt)
        assert result.status == VerificationStatus.INCONCLUSIVE

    def test_timeout_returns_failed(self):
        v = OpenCodeRunVerifier()
        receipt = ExecutionReceipt(tool_name="opencode.run",
                                    args={"command": "sleep 10"},
                                    result_data={"status": "timeout"})
        result = v.verify(receipt)
        assert result.status == VerificationStatus.FAILED


# ═══════════════════════════════════════════════════════════════════════
# L. Verification Orchestrator Tests
# ═══════════════════════════════════════════════════════════════════════


class TestVerificationOrchestrator:
    def test_orchestrator_has_builtin_verifiers(self):
        orch = VerificationOrchestrator()
        assert orch.get_verifier("math.add") is not None
        assert orch.get_verifier("filesystem.write") is not None
        assert orch.get_verifier("opencode.run") is not None
        assert orch.get_verifier("integrity_check") is not None

    def test_orchestrator_verify_math_verified(self):
        orch = VerificationOrchestrator()
        receipt = ExecutionReceipt(tool_name="math.add", args={"a": 2, "b": 3},
                                    result_data={"result": 5})
        receipt.finalize()
        vr = orch.verify(receipt, publish=False)
        assert vr.status == VerificationStatus.VERIFIED

    def test_orchestrator_verify_math_failed(self):
        orch = VerificationOrchestrator()
        receipt = ExecutionReceipt(tool_name="math.add", args={"a": 2, "b": 3},
                                    result_data={"result": 99})
        receipt.finalize()
        vr = orch.verify(receipt, publish=False)
        assert vr.status == VerificationStatus.FAILED

    def test_orchestrator_verify_no_verifier_returns_not_supported(self):
        orch = VerificationOrchestrator()
        receipt = ExecutionReceipt(tool_name="unknown.tool", args={},
                                    result_data={"status": "ok"})
        receipt.finalize()
        vr = orch.verify(receipt, publish=False)
        assert vr.status == VerificationStatus.NOT_SUPPORTED
        assert vr.verifier_id == "none"

    def test_orchestrator_verify_tampered_receipt(self):
        orch = VerificationOrchestrator()
        receipt = ExecutionReceipt(tool_name="math.add", args={"a": 1, "b": 2},
                                    result_data={"result": 3})
        receipt.finalize()
        receipt.result_data = {"result": 999}
        vr = orch.verify(receipt, publish=False)
        assert vr.status == VerificationStatus.TAMPERED

    def test_orchestrator_verification_results_stored(self):
        orch = VerificationOrchestrator()
        receipt = ExecutionReceipt(tool_name="math.add", args={"a": 1, "b": 1},
                                    result_data={"result": 2})
        receipt.finalize()
        vr = orch.verify(receipt, publish=False)
        stored = orch.verification_results()
        assert len(stored) == 1
        assert stored[0].verification_id == vr.verification_id

    def test_orchestrator_verification_results_filtered_by_execution(self):
        orch = VerificationOrchestrator()
        eid = uuid7()
        r1 = ExecutionReceipt(tool_name="math.add", args={"a": 1, "b": 1},
                               result_data={"result": 2}, execution_id=eid)
        r1.finalize()
        r2 = ExecutionReceipt(tool_name="math.add", args={"a": 2, "b": 2},
                               result_data={"result": 4}, execution_id=uuid7())
        r2.finalize()
        orch.verify(r1, publish=False)
        orch.verify(r2, publish=False)
        results = orch.verification_results(execution_id=eid)
        assert len(results) == 1

    def test_orchestrator_get_result_by_id(self):
        orch = VerificationOrchestrator()
        receipt = ExecutionReceipt(tool_name="math.add", args={"a": 1, "b": 1},
                                    result_data={"result": 2})
        receipt.finalize()
        vr = orch.verify(receipt, publish=False)
        assert orch.get_result(vr.verification_id) is vr
        assert orch.get_result("nonexistent") is None

    def test_orchestrator_register_custom_verifier(self):
        orch = VerificationOrchestrator()
        class CustomVerifier(Verifier):
            name = "custom"
            def verify(self, receipt, expected_state=None):
                return VerificationResult(
                    verification_id=uuid7(),
                    execution_id=receipt.execution_id,
                    receipt_id=receipt.receipt_id,
                    verifier_id="custom",
                    status=VerificationStatus.VERIFIED,
                    expected_state={},
                    observed_state={},
                )
        orch.register_verifier("custom", CustomVerifier())
        assert orch.get_verifier("custom") is not None

    def test_orchestrator_verify_execution_collects_receipts(self):
        orch = VerificationOrchestrator()
        eid = uuid7()
        utr = UnifiedToolRuntime()
        r1 = ExecutionReceipt(tool_name="math.add", args={"a": 1, "b": 1},
                               result_data={"result": 2}, execution_id=eid)
        r1.finalize()
        utr._put_receipt(r1)
        results = orch.verify_execution(eid, utr=utr, publish=False)
        assert len(results) == 1
        assert results[0].status == VerificationStatus.VERIFIED


class TestOrchestratorEventBusPublish:
    def test_verify_publishes_verification_passed_event(self):
        bus = EventBus()
        received = []
        def handler(msg):
            received.append(msg)
        bus.subscribe("VERIFICATION_PASSED", handler)

        orch = VerificationOrchestrator(event_bus=bus)
        ctx = ExecutionContext(execution_mode="real", execution_state="running")
        get_context_manager().set_context(ctx)

        receipt = ExecutionReceipt(tool_name="math.add", args={"a": 1, "b": 2},
                                    result_data={"result": 3})
        receipt.finalize()
        orch.verify(receipt, publish=True)

        assert len(received) == 1
        msg = received[0]
        assert msg.topic == "VERIFICATION_PASSED"
        payload = msg.payload
        assert payload["verification_state"] in ("verified", "unverified")
        assert payload["status"] == "verified"
        assert payload["verifier_id"] == "math.add"

    def test_verify_publishes_verification_failed_event(self):
        bus = EventBus()
        received = []
        def handler(msg):
            received.append(msg)
        bus.subscribe("VERIFICATION_FAILED", handler)

        orch = VerificationOrchestrator(event_bus=bus)
        ctx = ExecutionContext(execution_mode="real", execution_state="running")
        get_context_manager().set_context(ctx)

        receipt = ExecutionReceipt(tool_name="opencode.run",
                                    args={"command": "rm"},
                                    result_data={"status": "blocked", "error": "denied"})
        receipt.finalize()
        orch.verify(receipt, publish=True)

        assert len(received) == 1
        msg = received[0]
        assert msg.topic == "VERIFICATION_FAILED"
        assert msg.payload["status"] == "failed"

    def test_verify_publishes_tampered_event(self):
        bus = EventBus()
        received = []
        def handler(msg):
            received.append(msg)
        bus.subscribe("VERIFICATION_FAILED", handler)

        orch = VerificationOrchestrator(event_bus=bus)
        receipt = ExecutionReceipt(tool_name="math.add", args={"a": 1, "b": 2},
                                    result_data={"result": 3})
        receipt.finalize()
        receipt.result_data = {"result": 999}
        orch.verify(receipt, publish=True)

        assert len(received) >= 1

    def test_verify_publishes_not_supported_event(self):
        bus = EventBus()
        received = []
        def handler(msg):
            received.append(msg)
        bus.subscribe("VERIFICATION_FAILED", handler)

        orch = VerificationOrchestrator(event_bus=bus)
        receipt = ExecutionReceipt(tool_name="nonexistent.tool", args={},
                                    result_data={})
        receipt.finalize()
        orch.verify(receipt, publish=True)

        assert len(received) >= 1
        assert received[0].payload["status"] == "not_supported"


# ═══════════════════════════════════════════════════════════════════════
# M. Rule Engine Tests
# ═══════════════════════════════════════════════════════════════════════


class TestRuleEngine:
    def test_hard_rules_defined(self):
        assert len(HARD_RULES) >= 7
        rule_ids = [r.rule_id for r in HARD_RULES]
        assert "V-HARD-01" in rule_ids
        assert "V-HARD-02" in rule_ids
        assert "V-HARD-07" in rule_ids

    def test_rule_has_description(self):
        for rule in HARD_RULES:
            assert rule.description
            assert rule.rule_id

    def test_rule_engine_checks_passed_result(self):
        engine = RuleEngine()
        vr = VerificationResult(
            execution_id=uuid7(),
            receipt_id=uuid7(),
            verifier_id="math.add",
            status=VerificationStatus.VERIFIED,
            expected_state={"result": 3},
            observed_state={"result": 3},
        )
        violations = engine.check(vr)
        assert isinstance(violations, list)

    def test_rule_engine_checks_failed_result(self):
        engine = RuleEngine()
        vr = VerificationResult(
            execution_id=uuid7(),
            receipt_id=uuid7(),
            verifier_id="math.add",
            status=VerificationStatus.FAILED,
            expected_state={"result": 3},
            observed_state={"result": 99},
        )
        violations = engine.check(vr)
        assert isinstance(violations, list)

    def test_rule_engine_assert_violations_raises(self):
        engine = RuleEngine(rules=[
            VerificationRule("TEST-RULE", "Always fails", lambda vr: False),
        ])
        vr = VerificationResult(
            execution_id=uuid7(),
            receipt_id=uuid7(),
            verifier_id="test",
            status=VerificationStatus.VERIFIED,
            expected_state={},
            observed_state={},
        )
        with pytest.raises(HardRuleViolation):
            engine.assert_violations(vr)

    def test_rule_engine_assert_violations_passes(self):
        engine = RuleEngine(rules=[
            VerificationRule("TEST-RULE", "Always passes", lambda vr: True),
        ])
        vr = VerificationResult(
            execution_id=uuid7(),
            receipt_id=uuid7(),
            verifier_id="test",
            status=VerificationStatus.VERIFIED,
            expected_state={},
            observed_state={},
        )
        engine.assert_violations(vr)


# ═══════════════════════════════════════════════════════════════════════
# N. Verification Result — Canonical Form
# ═══════════════════════════════════════════════════════════════════════


class TestVerificationResultCanonical:
    def test_verification_result_has_all_required_fields(self):
        vr = VerificationResult(
            verification_id=uuid7(),
            execution_id=uuid7(),
            receipt_id=uuid7(),
            verifier_id="math.add",
            status=VerificationStatus.VERIFIED,
            expected_state={"result": 5},
            observed_state={"result": 5},
            state_diff={},
            evidence={"recomputed": True},
            verified_at=time.time(),
        )
        d = vr.to_dict()
        required = {"verification_id", "execution_id", "receipt_id", "verifier_id",
                     "status", "expected_state", "observed_state", "state_diff",
                     "evidence", "verified_at"}
        assert required.issubset(d.keys())

    def test_verification_result_serialization_roundtrip(self):
        vr = VerificationResult(
            verification_id=uuid7(),
            execution_id=uuid7(),
            receipt_id=uuid7(),
            verifier_id="math.add",
            status=VerificationStatus.VERIFIED,
            expected_state={"result": 5},
            observed_state={"result": 5},
            state_diff={},
            evidence={"recomputed": True},
            verified_at=time.time(),
        )
        d = vr.to_dict()
        vr2 = VerificationResult.from_dict(d)
        assert vr2.verification_id == vr.verification_id
        assert vr2.execution_id == vr.execution_id
        assert vr2.receipt_id == vr.receipt_id
        assert vr2.verifier_id == vr.verifier_id
        assert vr2.status == vr.status
        assert vr2.expected_state == vr.expected_state
        assert vr2.observed_state == vr.observed_state

    def test_verification_result_json_serializable(self):
        vr = VerificationResult(
            verification_id=uuid7(),
            execution_id=uuid7(),
            receipt_id=uuid7(),
            verifier_id="math.add",
            status=VerificationStatus.VERIFIED,
            expected_state={"result": 5},
            observed_state={"result": 5},
        )
        json_str = json.dumps(vr.to_dict(), default=str)
        assert json_str
        parsed = json.loads(json_str)
        assert parsed["status"] == "verified"
        assert parsed["verifier_id"] == "math.add"
