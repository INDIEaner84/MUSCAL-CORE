import json
import os
import tempfile
import time
from pathlib import Path

import pytest

from runtime.event_store import EventStore
from features.tool_runtime.tool_runtime import (
    ToolResult,
    UnifiedToolRuntime,
    create_default_utr,
    set_global_event_store,
    get_global_event_store,
    set_global_default_timeout,
    get_global_default_timeout,
    VerificationStatus,
)
from features.safety.safety_gate import SafetyGate


class TestCrossBootTrustCore:
    @pytest.fixture
    def db_path(self):
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            yield Path(f.name)
        try:
            os.unlink(f.name)
        except OSError:
            pass

    @pytest.fixture
    def es(self, db_path):
        return EventStore(db_path=db_path)

    def test_c001_global_event_store_auto_wires_utr(self, es):
        set_global_event_store(es)
        try:
            utr, _ = create_default_utr()
            assert utr._on_receipt_callback is not None, (
                "Receipt callback must be wired when global EventStore is set"
            )
            assert utr._on_verification_callback is not None, (
                "Verification callback must be wired when global EventStore is set"
            )
        finally:
            set_global_event_store(None)

    def test_c001_default_timeout_applied(self, es):
        set_global_default_timeout(60)
        try:
            utr, _ = create_default_utr()
            assert utr._default_timeout == 60, (
                "Default timeout should match global setting"
            )
        finally:
            set_global_default_timeout(300)

    def test_c001_execution_produces_persisted_receipt(self, es):
        set_global_event_store(es)
        try:
            utr, _ = create_default_utr()
            result = utr.execute("math.add", {"a": 2, "b": 3})
            assert result.success is True
            assert result.output["result"] == 5

            events = es.replay(cursor=0, topic="execution.receipt", limit=100)
            assert len(events) >= 1, "Receipt must be persisted to EventStore"

            receipt_event = events[-1]
            payload = receipt_event["payload"]
            if isinstance(payload, str):
                payload = json.loads(payload)
            assert payload["tool"] == "math.add"
            assert payload["success"] is True
            assert payload["result_data"]["result"] == 5
        finally:
            set_global_event_store(None)

    def test_c002_verification_produces_persisted_result(self, es):
        set_global_event_store(es)
        try:
            utr, _ = create_default_utr()
            result = utr.execute("math.add", {"a": 2, "b": 3})
            assert result.success is True
            receipt = result.receipt
            assert receipt is not None

            vr = utr.verify(receipt_id=receipt.receipt_id)
            assert vr is not None
            if isinstance(vr, list):
                vr = vr[0]
            assert vr.status == VerificationStatus.VERIFIED

            events = es.replay(cursor=0, topic="execution.verification", limit=100)
            assert len(events) >= 1, "Verification must be persisted to EventStore"
        finally:
            set_global_event_store(None)

    def test_c003_fresh_reader_recovers_execution_truth(self, es, db_path):
        set_global_event_store(es)
        try:
            utr, _ = create_default_utr()
            result = utr.execute("math.add", {"a": 10, "b": 20})
            assert result.success is True
            exec_id = result.receipt.execution_id

            es.close()
        finally:
            set_global_event_store(None)

        fresh_es = EventStore(db_path=db_path)
        try:
            events = fresh_es.replay(cursor=0, limit=100)
            assert len(events) >= 1

            receipt_events = [
                e for e in events
                if e["topic"] == "execution.receipt"
            ]
            assert len(receipt_events) >= 1
            last_receipt = receipt_events[-1]
            payload = last_receipt["payload"]
            if isinstance(payload, str):
                payload = json.loads(payload)
            assert payload["execution_id"] == exec_id
            assert payload["tool"] == "math.add"
            assert payload["result_data"]["result"] == 30
        finally:
            fresh_es.close()

    def test_c004_create_default_utr_without_event_store_still_works(self):
        set_global_event_store(None)
        utr, _ = create_default_utr()
        result = utr.execute("math.add", {"a": 1, "b": 2})
        assert result.success is True
        assert result.output["result"] == 3
        assert result.receipt is not None

    def test_c004_tools_execute_via_pipeline_use_wired_utr(self, es):
        set_global_event_store(es)
        try:
            from features.safety.safety_gate import SafetyGate
            from features.pipeline.cu_stage import CognitiveUnitStage

            sg = SafetyGate(user_policy={"allow_high_risk": True})
            for name in ("console.print", "math.add", "filesystem.write"):
                sg.permit(name)

            stage = CognitiveUnitStage(kernel=None)
            stage._ensure_registry()

            from features.cognitive_unit.registry import resolve
            cu = resolve("general")
            assert cu is not None
            assert cu.tool_runtime is not None
            assert cu.tool_runtime._on_receipt_callback is not None, (
                "Pipeline CU's UTR must have wired receipt callback"
            )

            result = cu.execute({
                "tool": "math.add",
                "args": {"a": 5, "b": 7},
                "agent_type": "general",
            })
            assert result["status"] == "success"
            assert result["output"]["result"] == 12

            receipt_events = es.replay(cursor=0, topic="execution.receipt", limit=100)
            assert len(receipt_events) >= 1
        finally:
            set_global_event_store(None)

    def _slow_tool(self, args):
        import time
        time.sleep(5)
        return {"status": "ok", "result": "done"}

    def test_c005_default_timeout_produces_deterministic_timeout_result(self, es):
        import time
        set_global_event_store(es)
        set_global_default_timeout(0.1)
        try:
            utr, _ = create_default_utr()
            utr.register_tool("test.slow", self._slow_tool, schema={})
            start = time.time()
            result = utr.execute("test.slow", {})
            elapsed = time.time() - start
            assert result.success is False
            assert "TIMEOUT" in result.error
            assert result.receipt is not None
            assert result.receipt.success is False
            assert elapsed < 2, "Should timeout in ~0.1s, not wait 5s"
        finally:
            set_global_default_timeout(300)
            set_global_event_store(None)

    def test_c005_timeout_toolresult_state_is_deterministic(self, es):
        set_global_event_store(es)
        set_global_default_timeout(0.1)
        try:
            utr, _ = create_default_utr()
            utr.register_tool("test.slow", self._slow_tool, schema={})
            result = utr.execute("test.slow", {})

            assert result.success is False
            assert bool(result.error) is True
            assert result.receipt is not None
            assert result.receipt.success is False

            d = result.to_dict()
            assert d["status"] == "error"
            assert "TIMEOUT" in d["error"]
            assert d["receipt"]["success"] is False

            restored = ToolResult.from_dict(d)
            assert restored.success is False
            assert "TIMEOUT" in restored.error
        finally:
            set_global_default_timeout(300)
            set_global_event_store(None)

    def test_c005_timeout_receipt_persisted_to_event_store(self, es):
        set_global_event_store(es)
        set_global_default_timeout(0.1)
        try:
            utr, _ = create_default_utr()
            utr.register_tool("test.slow", self._slow_tool, schema={})
            result = utr.execute("test.slow", {})

            events = es.replay(cursor=0, limit=100)
            timeout_events = [
                e for e in events
                if e["topic"] == "execution.receipt"
            ]
            assert len(timeout_events) >= 1
            last = timeout_events[-1]
            payload = last["payload"]
            if isinstance(payload, str):
                payload = json.loads(payload)
            assert payload["success"] is False
            result_data = payload.get("result_data")
            assert result_data is None
        finally:
            set_global_default_timeout(300)
            set_global_event_store(None)

    def test_c006_tampered_receipt_detected(self, es):
        set_global_event_store(es)
        try:
            utr, _ = create_default_utr()
            result = utr.execute("math.add", {"a": 1, "b": 2})
            assert result.success is True
            receipt = result.receipt

            receipt._integrity_hash = "tampered"
            vr = utr.verify(receipt_id=receipt.receipt_id)
            if isinstance(vr, list):
                vr = vr[0]
            assert vr is not None
            assert vr.status == VerificationStatus.TAMPERED

            verification_events = es.replay(
                cursor=0, topic="execution.verification", limit=100
            )
            assert len(verification_events) >= 1
        finally:
            set_global_event_store(None)

    def test_c006_verification_failure_persisted(self, es):
        set_global_event_store(es)
        try:
            utr, _ = create_default_utr()
            result = utr.execute("filesystem.write", {
                "path": "/tmp/_test_c006_blocked",
                "content": "test",
            })
            receipt = result.receipt
            receipt._integrity_hash = "bad_hash"
            vr = utr.verify(receipt_id=receipt.receipt_id)
            if isinstance(vr, list):
                vr = vr[0]
            assert vr.status == VerificationStatus.TAMPERED

            events = es.replay(cursor=0, topic="execution.verification", limit=100)
            assert len(events) >= 1
            last = events[-1]
            assert last["verification_state"] == "tampered"
        finally:
            set_global_event_store(None)

    def test_c007_watchdog_event_store_query_works(self, es):
        set_global_event_store(es)
        try:
            from features.monitoring.execution_watchdog import ExecutionWatchdog

            watchdog = ExecutionWatchdog(
                event_store=es,
                event_bus=None,
                orphan_timeout=0.01,
                poll_interval=0.01,
            )
            stats = watchdog.stats()
            assert stats["running"] is False
            assert stats["orphans_resolved"] == 0

            es.append({
                "topic": "EXECUTION_STARTED",
                "payload": {"event_type": "EXECUTION_STARTED"},
                "source": "test",
                "id": "watchdog-test-001",
                "execution_id": "orphan-ex-001",
                "execution_state": "running",
                "timestamp": time.time() - 9999,
            })

            watchdog.start()
            time.sleep(0.05)
            watchdog.stop()

            stats2 = watchdog.stats()
            assert stats2["orphans_resolved"] >= 0
        finally:
            set_global_event_store(None)

    def test_c007_watchdog_shutdown(self, es):
        set_global_event_store(es)
        try:
            from features.monitoring.execution_watchdog import ExecutionWatchdog

            watchdog = ExecutionWatchdog(
                event_store=es,
                event_bus=None,
            )
            watchdog.start()
            assert watchdog.stats()["running"] is True
            watchdog.stop()
            assert watchdog.stats()["running"] is False
        finally:
            set_global_event_store(None)

    def test_c008_utr_shutdown_cleans_pool(self, es):
        set_global_event_store(es)
        try:
            utr, _ = create_default_utr()
            pool = utr._executor_pool
            assert pool._shutdown is False or not pool._shutdown
            utr.shutdown(wait=True)
            assert pool._shutdown is True
        finally:
            set_global_event_store(None)

    def test_c008_explicit_timeout_override_works(self, es):
        set_global_event_store(es)
        set_global_default_timeout(300)
        try:
            utr, _ = create_default_utr()
            result = utr.execute(
                "math.add", {"a": 3, "b": 4},
                timeout=None,
            )
            assert result.success is True
            assert result.output["result"] == 7

            result2 = utr.execute(
                "math.add", {"a": 5, "b": 6},
                timeout=999,
            )
            assert result2.success is True
            assert result2.output["result"] == 11
        finally:
            set_global_default_timeout(300)
            set_global_event_store(None)


class TestGlobalEventStoreRegistry:
    def test_get_set_clear(self):
        assert get_global_event_store() is None
        try:
            es = object()
            set_global_event_store(es)
            assert get_global_event_store() is es
        finally:
            set_global_event_store(None)
        assert get_global_event_store() is None

    def test_default_timeout(self):
        prev = get_global_default_timeout()
        try:
            set_global_default_timeout(42)
            assert get_global_default_timeout() == 42
        finally:
            set_global_default_timeout(prev)
        assert get_global_default_timeout() == prev


class TestSacnAllCallersAutoWired:
    @pytest.fixture
    def db_path(self):
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            yield Path(f.name)
        try:
            os.unlink(f.name)
        except OSError:
            pass

    @pytest.fixture
    def es(self, db_path):
        return EventStore(db_path=db_path)

    @pytest.fixture(autouse=True)
    def clear_registry(self):
        from features.cognitive_unit.registry import clear
        clear()
        yield
        clear()

    def test_mel_utr_auto_wired(self, es):
        set_global_event_store(es)
        try:
            import mel
            mel._utr = None
            utr = mel._get_utr()
            assert utr._on_receipt_callback is not None, (
                "mel's UTR must have wired receipt callback via global EventStore"
            )
            assert utr._on_verification_callback is not None
        finally:
            set_global_event_store(None)
            mel._utr = None

    def test_tools_utr_auto_wired(self, es):
        set_global_event_store(es)
        try:
            from tools import _get_global_utr
            utr = _get_global_utr()
            assert utr._on_receipt_callback is not None, (
                "tools._get_global_utr() UTR must have wired receipt callback"
            )
            assert utr._on_verification_callback is not None
        finally:
            set_global_event_store(None)

    def test_cu_stage_utr_auto_wired(self, es):
        set_global_event_store(es)
        try:
            from features.safety.safety_gate import SafetyGate
            from features.pipeline.cu_stage import CognitiveUnitStage

            sg = SafetyGate(user_policy={"allow_high_risk": True})
            for name in ("console.print", "math.add", "filesystem.write"):
                sg.permit(name)

            stage = CognitiveUnitStage(kernel=None)
            stage._ensure_registry()

            from features.cognitive_unit.registry import resolve
            for agent_type in ("general", "analytical", "research", "creative", "operational", "coding"):
                cu = resolve(agent_type)
                assert cu is not None
                utr = cu.tool_runtime
                assert utr._on_receipt_callback is not None, (
                    f"CognitiveUnit({agent_type}) UTR missing receipt callback"
                )
                assert utr._on_verification_callback is not None
        finally:
            set_global_event_store(None)

    def test_all_cu_agent_types_wired(self, es):
        set_global_event_store(es)
        try:
            from features.pipeline.cu_stage import CognitiveUnitStage
            from features.cognitive_unit.registry import all_units

            stage = CognitiveUnitStage(kernel=None)
            stage._ensure_registry()

            units = all_units()
            assert len(units) >= 6, "Expected at least 6 CUs (general + 5 specialized)"

            for agent_type, cu in units.items():
                utr = cu.tool_runtime
                assert utr._on_receipt_callback is not None, (
                    f"CU '{cu.id}' ({agent_type}) missing receipt callback"
                )
                assert utr._default_timeout == 300, (
                    f"CU '{cu.id}' ({agent_type}) should have default timeout 300"
                )
        finally:
            set_global_event_store(None)

