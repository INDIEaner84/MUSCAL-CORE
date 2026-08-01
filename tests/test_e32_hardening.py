import os


class TestM1WorkerHardening:
    def test_worker_determinism(self):
        from features.worker.worker import Worker
        from features.tool_runtime.tool_runtime import create_default_utr
        from features.safety.safety_gate import SafetyGate
        sg = SafetyGate(user_policy={"allow_high_risk": True})
        utr, _ = create_default_utr(safety_gate=sg)
        w = Worker(worker_id="det-1", tool_runtime=utr, safety_gate=sg)
        results = []
        for _ in range(3):
            r = w.execute({"tool": "math.add", "args": {"a": 2, "b": 3}, "task_type": "analytical"})
            results.append(r["status"])
        assert all(s == "success" for s in results)

    def test_worker_error_propagation(self):
        from features.worker.worker import Worker
        from features.tool_runtime.tool_runtime import create_default_utr
        from features.safety.safety_gate import SafetyGate
        sg = SafetyGate(user_policy={"allow_high_risk": True})
        utr, _ = create_default_utr(safety_gate=sg)
        w = Worker(worker_id="err-1", tool_runtime=utr, safety_gate=sg)
        result = w.execute({"tool": "math.add", "args": {"a": 1, "b": "not_a_number"}, "task_type": "analytical"})
        assert result["status"] == "error"

    def test_worker_safety_blocks_high_risk_without_permit(self):
        from features.worker.worker import Worker
        from features.safety.safety_gate import SafetyGate
        sg = SafetyGate(user_policy={"allow_high_risk": False})
        w = Worker(worker_id="safe-1", safety_gate=sg)
        result = w.execute({"tool": "opencode.run", "args": {"command": "ls"}, "task_type": "operational"})
        assert result["status"] == "blocked_by_safety"
        assert "HIGH_RISK_BLOCKED" in result.get("reason", "")

    def test_worker_no_bypass_without_safety_gate(self):
        from features.worker.worker import Worker
        from features.tool_runtime.tool_runtime import create_default_utr
        utr, _ = create_default_utr()
        w = Worker(worker_id="nobypass-1", tool_runtime=utr)
        result = w.execute({"tool": "console.print", "args": {"message": "test"}, "task_type": "operational"})
        assert result["status"] == "success"

    def test_worker_does_not_mutate_input(self):
        from features.worker.worker import Worker
        from features.tool_runtime.tool_runtime import create_default_utr
        from features.safety.safety_gate import SafetyGate
        sg = SafetyGate(user_policy={"allow_high_risk": True})
        utr, _ = create_default_utr(safety_gate=sg)
        w = Worker(worker_id="immut-1", tool_runtime=utr, safety_gate=sg)
        original = {"tool": "console.print", "args": {"message": "hello"}, "task_type": "operational"}
        import copy
        ctx = copy.deepcopy(original)
        w.execute(ctx)
        assert ctx == original


class TestM3EventHardening:
    def test_writer_to_eventstore_roundtrip_preserves_payload(self):
        from features.events.event_adapter import writer_to_eventstore, eventstore_to_writer
        original = {
            "type": "test.event",
            "actor": "kernel",
            "payload": {"value": 42, "nested": {"a": 1}},
            "ts": "2026-07-23T12:00:00",
            "severity": "info",
            "idempotency_key": "rt-001",
        }
        es = writer_to_eventstore(original)
        w = eventstore_to_writer(es)
        import json
        orig_payload = json.loads(w["payload"]) if isinstance(w["payload"], str) else w["payload"]
        assert orig_payload["value"] == 42
        assert orig_payload["nested"]["a"] == 1

    def test_event_adapter_determinism(self):
        from features.events.event_adapter import writer_to_eventstore
        event = {"type": "test", "ts": "2026-07-23T12:00:00"}
        r1 = writer_to_eventstore(event)
        r2 = writer_to_eventstore(event)
        assert r1 == r2

    def test_writer_event_with_no_type_defaults_to_system(self):
        from features.events.event_adapter import writer_to_eventstore
        es = writer_to_eventstore({"ts": "2026-07-23T12:00:00"})
        assert es["topic"] == "system"

    def test_eventstore_to_writer_preserves_payload(self):
        from features.events.event_adapter import eventstore_to_writer
        es_event = {"topic": "test", "payload": {"msg": "hello"}, "source": "kernel", "priority": "NORMAL", "id": "id-1"}
        w = eventstore_to_writer(es_event)
        import json
        payload = json.loads(w["payload"])
        assert payload["msg"] == "hello"


class TestCUWorkerHardening:
    def test_cu_worker_flow_governance_safety_utr(self):
        from features.cognitive_unit.cognitive_unit import CognitiveUnit
        from features.worker.worker import Worker
        from features.tool_runtime.tool_runtime import create_default_utr
        from features.safety.safety_gate import SafetyGate
        sg = SafetyGate(user_policy={"allow_high_risk": True})
        utr, _ = create_default_utr(safety_gate=sg)
        worker = Worker(worker_id="flow-1", tool_runtime=utr, safety_gate=sg)
        cu = CognitiveUnit(
            unit_id="flow-cu", agent_type="operational",
            worker=worker, tool_runtime=utr, safety_gate=sg,
        )
        result = cu.execute({"tool": "console.print", "args": {"message": "flow"}, "task_type": "operational"})
        assert result["status"] == "success"

    def test_cu_worker_blocked_by_governance(self):
        from features.cognitive_unit.cognitive_unit import CognitiveUnit
        from features.worker.worker import Worker
        from features.tool_runtime.tool_runtime import create_default_utr
        from features.safety.safety_gate import SafetyGate

        class DenyGovernance:
            def check(self, context):
                from types import SimpleNamespace
                return SimpleNamespace(allowed=False)

        sg = SafetyGate(user_policy={"allow_high_risk": True})
        utr, _ = create_default_utr(safety_gate=sg)
        worker = Worker(worker_id="deny-1", tool_runtime=utr, safety_gate=sg)
        cu = CognitiveUnit(
            unit_id="deny-cu", agent_type="operational",
            worker=worker, tool_runtime=utr, safety_gate=sg,
            governance=DenyGovernance(),
        )
        result = cu.execute({"tool": "console.print", "args": {"message": "secret"}, "task_type": "operational"})
        assert result["status"] == "blocked_by_governance"

    def test_cu_worker_blocked_by_safety(self):
        from features.cognitive_unit.cognitive_unit import CognitiveUnit
        from features.worker.worker import Worker
        from features.safety.safety_gate import SafetyGate
        sg = SafetyGate(user_policy={"allow_high_risk": False})
        worker = Worker(worker_id="block-1", safety_gate=sg)
        cu = CognitiveUnit(
            unit_id="block-cu", agent_type="operational",
            worker=worker, safety_gate=sg,
        )
        result = cu.execute({"tool": "opencode.run", "args": {"command": "ls"}, "task_type": "operational"})
        assert result["status"] == "blocked_by_safety"


class TestModeSwitching:
    def test_worker_disabled_in_inline_mode(self):
        from features.cognitive_unit.cognitive_unit import CognitiveUnit
        from features.worker.worker import Worker
        from features.tool_runtime.tool_runtime import create_default_utr
        from features.safety.safety_gate import SafetyGate
        sg = SafetyGate(user_policy={"allow_high_risk": True})
        utr, _ = create_default_utr(safety_gate=sg)
        cu = CognitiveUnit(
            unit_id="inline-cu", agent_type="operational",
            worker=None, tool_runtime=utr, safety_gate=sg,
        )
        result = cu.execute({"tool": "console.print", "args": {"message": "inline"}, "task_type": "operational"})
        assert result["status"] == "success"
        assert "worker_id" not in result

    def test_cu_no_worker_falls_back_to_direct(self):
        from features.cognitive_unit.cognitive_unit import CognitiveUnit
        from features.tool_runtime.tool_runtime import create_default_utr
        from features.safety.safety_gate import SafetyGate
        sg = SafetyGate(user_policy={"allow_high_risk": True})
        utr, _ = create_default_utr(safety_gate=sg)
        cu = CognitiveUnit(
            unit_id="fallback-cu", agent_type="general",
            tool_runtime=utr, safety_gate=sg,
        )
        result = cu.execute({"tool": "math.add", "args": {"a": 1, "b": 2}, "task_type": "analytical"})
        assert result["status"] == "success"
