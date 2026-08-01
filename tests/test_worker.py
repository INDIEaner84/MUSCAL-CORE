from features.worker.worker import Worker, WORKER_STATUS


class TestWorkerStatus:
    def test_worker_status_active(self):
        assert WORKER_STATUS == "ACTIVE"


class TestWorkerContract:
    def test_worker_accepts_dependencies(self):
        w = Worker(worker_id="test-1")
        assert w.id == "test-1"

    def test_worker_noop_without_tool(self):
        w = Worker(worker_id="test-1")
        result = w.execute({"task_type": "general"})
        assert result["status"] == "noop"
        assert result["worker_id"] == "test-1"

    def test_worker_noop_with_empty_context(self):
        w = Worker(worker_id="test-1")
        result = w.execute({})
        assert result["status"] == "noop"

    def test_worker_noop_with_none_context(self):
        w = Worker(worker_id="test-1")
        result = w.execute(None)
        assert result["status"] == "noop"

    def test_worker_to_dict(self):
        w = Worker(worker_id="test-1")
        d = w.to_dict()
        assert d["id"] == "test-1"

    def test_worker_safety_blocks_high_risk(self):
        from features.safety.safety_gate import SafetyGate
        sg = SafetyGate(user_policy={"allow_high_risk": False})
        w = Worker(worker_id="safe-1", safety_gate=sg)
        result = w.execute({"tool": "opencode.run", "args": {"command": "ls"}, "task_type": "operational"})
        assert result["status"] == "blocked_by_safety"
        assert "HIGH_RISK_BLOCKED" in result.get("reason", "")

    def test_worker_executes_tool(self):
        from features.tool_runtime.tool_runtime import create_default_utr
        from features.safety.safety_gate import SafetyGate
        sg = SafetyGate(user_policy={"allow_high_risk": True})
        utr, _ = create_default_utr(safety_gate=sg)
        w = Worker(worker_id="exec-1", tool_runtime=utr, safety_gate=sg)
        result = w.execute({"tool": "console.print", "args": {"message": "hello"}, "task_type": "operational"})
        assert result["status"] == "success"

    def test_worker_tool_failure_propagates(self):
        from features.tool_runtime.tool_runtime import create_default_utr
        from features.safety.safety_gate import SafetyGate
        sg = SafetyGate(user_policy={"allow_high_risk": True})
        utr, _ = create_default_utr(safety_gate=sg)
        w = Worker(worker_id="fail-1", tool_runtime=utr, safety_gate=sg)
        result = w.execute({"tool": "math.add", "args": {"a": 1, "b": "not_a_number"}, "task_type": "general"})
        assert result["status"] == "error"

    def test_worker_no_runtime(self):
        w = Worker(worker_id="no-rt-1")
        result = w.execute({"tool": "console.print", "args": {"text": "hello"}, "task_type": "operational"})
        assert result["status"] == "no_runtime"


class TestCognitiveUnitWorkerIntegration:
    def test_cu_delegates_to_worker(self):
        from features.cognitive_unit.cognitive_unit import CognitiveUnit
        from features.tool_runtime.tool_runtime import create_default_utr
        from features.safety.safety_gate import SafetyGate
        sg = SafetyGate(user_policy={"allow_high_risk": True})
        utr, _ = create_default_utr(safety_gate=sg)
        worker = Worker(worker_id="cu-worker-1", tool_runtime=utr, safety_gate=sg)
        cu = CognitiveUnit(
            unit_id="cu-1", agent_type="operational",
            worker=worker, tool_runtime=utr, safety_gate=sg,
        )
        result = cu.execute({"tool": "console.print", "args": {"message": "hello"}, "task_type": "operational"})
        assert result["status"] == "success"
        assert result["unit_id"] == "cu-1"
        assert result["worker_id"] == "cu-worker-1"

    def test_cu_worker_noop_when_no_tool(self):
        from features.cognitive_unit.cognitive_unit import CognitiveUnit
        worker = Worker(worker_id="cu-worker-2")
        cu = CognitiveUnit(unit_id="cu-2", agent_type="general", worker=worker)
        result = cu.execute({"task_type": "general"})
        assert result["status"] == "noop"
        assert result["unit_id"] == "cu-2"

    def test_cu_worker_does_not_bypass_governance(self):
        from features.cognitive_unit.cognitive_unit import CognitiveUnit
        from features.tool_runtime.tool_runtime import create_default_utr
        from features.safety.safety_gate import SafetyGate

        class MockGovernance:
            def check(self, context):
                from types import SimpleNamespace
                return SimpleNamespace(allowed=False)

        sg = SafetyGate(user_policy={"allow_high_risk": True})
        utr, _ = create_default_utr(safety_gate=sg)
        worker = Worker(worker_id="gov-test-1", tool_runtime=utr, safety_gate=sg)
        cu = CognitiveUnit(
            unit_id="cu-3", agent_type="operational",
            worker=worker, tool_runtime=utr, safety_gate=sg,
            governance=MockGovernance(),
        )
        result = cu.execute({"tool": "console.print", "args": {"text": "secret"}, "task_type": "operational"})
        assert result["status"] == "blocked_by_governance"

    def test_cu_without_worker_falls_back_to_direct_execution(self):
        from features.cognitive_unit.cognitive_unit import CognitiveUnit
        from features.tool_runtime.tool_runtime import create_default_utr
        from features.safety.safety_gate import SafetyGate
        sg = SafetyGate(user_policy={"allow_high_risk": True})
        utr, _ = create_default_utr(safety_gate=sg)
        cu = CognitiveUnit(
            unit_id="cu-4", agent_type="operational",
            tool_runtime=utr, safety_gate=sg,
        )
        result = cu.execute({"tool": "console.print", "args": {"message": "hello"}, "task_type": "operational"})
        assert result["status"] == "success"

    def test_cu_worker_safety_denial(self):
        from features.cognitive_unit.cognitive_unit import CognitiveUnit
        from features.safety.safety_gate import SafetyGate
        sg = SafetyGate(user_policy={"allow_high_risk": False})
        worker = Worker(worker_id="cu-safe-1", safety_gate=sg)
        cu = CognitiveUnit(
            unit_id="cu-5", agent_type="operational",
            worker=worker, safety_gate=sg,
        )
        result = cu.execute({"tool": "opencode.run", "args": {"command": "ls"}, "task_type": "operational"})
        assert result["status"] == "blocked_by_safety"


class TestWorkerE32Enrichment:
    def test_w1_single_step_execution(self):
        from features.tool_runtime.tool_runtime import create_default_utr
        from features.safety.safety_gate import SafetyGate
        sg = SafetyGate(user_policy={"allow_high_risk": True})
        utr, _ = create_default_utr(safety_gate=sg)
        w = Worker(worker_id="w1", tool_runtime=utr, safety_gate=sg)
        plan = w.plan({"tool": "console.print", "args": {"message": "hello"}, "task_type": "operational"})
        assert len(plan.steps) == 1
        assert plan.steps[0].tool == "console.print"
        result = w.execute_plan(plan)
        assert result.success is True
        assert result.plan_id == plan.plan_id

    def test_w2_multi_step_ordered_execution(self):
        from features.tool_runtime.tool_runtime import create_default_utr
        from features.safety.safety_gate import SafetyGate
        from features.worker.worker import WorkerStep, WorkerPlan
        sg = SafetyGate(user_policy={"allow_high_risk": True})
        utr, _ = create_default_utr(safety_gate=sg)
        w = Worker(worker_id="w2", tool_runtime=utr, safety_gate=sg)
        import uuid
        plan_id = str(uuid.uuid4())
        step1 = WorkerStep(step_id="s1", action="print_first", tool="console.print",
                           args={"message": "first"}, failure_policy="continue_independent")
        step2 = WorkerStep(step_id="s2", action="print_second", tool="console.print",
                           args={"message": "second"}, depends_on=["s1"],
                           failure_policy="continue_independent")
        plan = WorkerPlan(plan_id=plan_id, steps=[step1, step2])
        result = w.execute_plan(plan)
        assert result.success is True
        assert len(result.step_results) == 2
        assert result.step_results[0]["status"] == "success"
        assert result.step_results[1]["status"] == "success"

    def test_w3_fail_fast_on_failure(self):
        from features.tool_runtime.tool_runtime import create_default_utr
        from features.safety.safety_gate import SafetyGate
        from features.worker.worker import WorkerStep, WorkerPlan
        sg = SafetyGate(user_policy={"allow_high_risk": True})
        utr, _ = create_default_utr(safety_gate=sg)
        w = Worker(worker_id="w3", tool_runtime=utr, safety_gate=sg)
        import uuid
        plan_id = str(uuid.uuid4())
        step1 = WorkerStep(step_id="s1", action="fail_step", tool="math.add",
                           args={"a": 1, "b": "not_a_number"},
                           failure_policy="fail_fast")
        step2 = WorkerStep(step_id="s2", action="never_reached", tool="console.print",
                           args={"message": "never"}, failure_policy="fail_fast")
        plan = WorkerPlan(plan_id=plan_id, steps=[step1, step2])
        result = w.execute_plan(plan)
        assert result.success is False
        assert len(result.errors) >= 1

    def test_w4_continue_independent_continues(self):
        from features.tool_runtime.tool_runtime import create_default_utr
        from features.safety.safety_gate import SafetyGate
        from features.worker.worker import WorkerStep, WorkerPlan
        sg = SafetyGate(user_policy={"allow_high_risk": True})
        utr, _ = create_default_utr(safety_gate=sg)
        w = Worker(worker_id="w4", tool_runtime=utr, safety_gate=sg)
        import uuid
        plan_id = str(uuid.uuid4())
        step1 = WorkerStep(step_id="s1", action="fail_step", tool="math.add",
                           args={"a": 1, "b": "not_a_number"},
                           failure_policy="continue_independent")
        step2 = WorkerStep(step_id="s2", action="ok_step", tool="console.print",
                           args={"message": "still_running"},
                           failure_policy="continue_independent")
        plan = WorkerPlan(plan_id=plan_id, steps=[step1, step2])
        result = w.execute_plan(plan)
        assert result.step_results[1]["status"] == "success"
        assert len(result.errors) >= 1

    def test_w5_retryable_retries(self):
        from features.tool_runtime.tool_runtime import create_default_utr
        from features.safety.safety_gate import SafetyGate
        from features.worker.worker import WorkerStep, WorkerPlan
        call_count = [0]

        class RetryableRuntime:
            def execute(self, tool_name, args, **kwargs):
                call_count[0] += 1
                if call_count[0] < 2:
                    from types import SimpleNamespace
                    return SimpleNamespace(success=False, output=None, error="transient",
                                           receipt=None)
                from types import SimpleNamespace
                return SimpleNamespace(success=True, output="ok", error=None, receipt=None)

        sg = SafetyGate(user_policy={"allow_high_risk": True})
        w = Worker(worker_id="w5", tool_runtime=RetryableRuntime(), safety_gate=sg)
        import uuid
        plan_id = str(uuid.uuid4())
        step1 = WorkerStep(step_id="s1", action="retry_me", tool="console.print",
                           args={"message": "hello"}, failure_policy="retryable",
                           max_retries=2)
        plan = WorkerPlan(plan_id=plan_id, steps=[step1])
        result = w.execute_plan(plan)
        assert result.success is True
        assert call_count[0] >= 2

    def test_w6_retry_count_limit(self):
        from features.worker.worker import WorkerStep, WorkerPlan
        call_count = [0]

        class AlwaysFailRuntime:
            def execute(self, tool_name, args, **kwargs):
                call_count[0] += 1
                from types import SimpleNamespace
                return SimpleNamespace(success=False, output=None, error="persistent",
                                       receipt=None)

        w = Worker(worker_id="w6", tool_runtime=AlwaysFailRuntime())
        import uuid
        plan_id = str(uuid.uuid4())
        step1 = WorkerStep(step_id="s1", action="fail_always", tool="console.print",
                           args={"message": "x"}, failure_policy="retryable",
                           max_retries=3)
        plan = WorkerPlan(plan_id=plan_id, steps=[step1])
        result = w.execute_plan(plan)
        assert result.success is False
        assert call_count[0] == 4

    def test_w7_step_result_aggregation(self):
        from features.tool_runtime.tool_runtime import create_default_utr
        from features.safety.safety_gate import SafetyGate
        sg = SafetyGate(user_policy={"allow_high_risk": True})
        utr, _ = create_default_utr(safety_gate=sg)
        w = Worker(worker_id="w7", tool_runtime=utr, safety_gate=sg)
        plan = w.plan({"tool": "console.print", "args": {"message": "agg"},
                        "task_type": "general"})
        result = w.execute_plan(plan)
        assert len(result.step_results) == 1
        assert isinstance(result.step_results, list)
        assert result.step_results[0]["step_id"] is not None

    def test_w8_plan_decomposition(self):
        from features.tool_runtime.tool_runtime import create_default_utr
        from features.safety.safety_gate import SafetyGate
        sg = SafetyGate(user_policy={"allow_high_risk": True})
        utr, _ = create_default_utr(safety_gate=sg)
        w = Worker(worker_id="w8", tool_runtime=utr, safety_gate=sg)
        plan = w.plan({"tool": "console.print", "args": {"message": "d"},
                        "task_type": "general"})
        assert hasattr(plan, "steps")
        assert len(plan.steps) == 1

    def test_w9_worker_handles_unknown_tool(self):
        from features.safety.safety_gate import SafetyGate
        sg = SafetyGate(user_policy={"allow_high_risk": False})
        w = Worker(worker_id="w9", safety_gate=sg)
        result = w.execute({"tool": "nonexistent.tool", "args": {}, "task_type": "general"})
        assert result["status"] == "blocked_by_safety"

    def test_w10_safety_gate_per_step(self):
        from features.worker.worker import WorkerStep, WorkerPlan
        from features.safety.safety_gate import SafetyGate
        sg = SafetyGate(user_policy={"allow_high_risk": False})
        from features.tool_runtime.tool_runtime import create_default_utr
        utr, _ = create_default_utr(safety_gate=sg)
        w = Worker(worker_id="w10", tool_runtime=utr, safety_gate=sg)
        import uuid
        plan_id = str(uuid.uuid4())
        step1 = WorkerStep(step_id="s1", action="risky", tool="opencode.run",
                           args={"command": "ls"}, failure_policy="fail_fast")
        plan = WorkerPlan(plan_id=plan_id, steps=[step1])
        result = w.execute_plan(plan)
        assert result.success is False
        assert any("blocked_by_safety" in str(r) for r in result.step_results)

    def test_w11_plan_status_reporting(self):
        from features.tool_runtime.tool_runtime import create_default_utr
        from features.safety.safety_gate import SafetyGate
        sg = SafetyGate(user_policy={"allow_high_risk": True})
        utr, _ = create_default_utr(safety_gate=sg)
        w = Worker(worker_id="w11", tool_runtime=utr, safety_gate=sg)
        plan = w.plan({"tool": "console.print", "args": {"message": "hello"},
                        "task_type": "operational"})
        result = w.execute_plan(plan)
        assert result.to_dict()["plan_id"] == plan.plan_id
        assert "step_results" in result.to_dict()
        assert "errors" in result.to_dict()

    def test_w12_worker_dict_version(self):
        w = Worker(worker_id="w12")
        d = w.to_dict()
        assert d["id"] == "w12"
        assert "version" in d
        assert "status" in d

    def test_w13_plan_method_generates_valid_plan(self):
        from features.tool_runtime.tool_runtime import create_default_utr
        from features.safety.safety_gate import SafetyGate
        sg = SafetyGate(user_policy={"allow_high_risk": True})
        utr, _ = create_default_utr(safety_gate=sg)
        w = Worker(worker_id="w13", tool_runtime=utr, safety_gate=sg)
        plan = w.plan({"tool": "console.print", "args": {"message": "p"},
                        "task_type": "general"})
        assert plan.plan_id is not None
        for s in plan.steps:
            assert s.step_id is not None
            assert s.tool is not None

    def test_w14_empty_context_noop(self):
        w = Worker(worker_id="w14")
        plan = w.plan({})
        assert len(plan.steps) == 0

    def test_w15_null_context_noop(self):
        w = Worker(worker_id="w15")
        plan = w.plan(None)
        assert len(plan.steps) == 0
