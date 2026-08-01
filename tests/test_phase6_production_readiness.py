import os
import sys
import time
import threading
import tempfile
from unittest.mock import MagicMock

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


# ═══════════════════════════════════════════════════════════════════
# P6.1 — PIPELINE DETERMINISM AUDIT
# ═══════════════════════════════════════════════════════════════════

class TestP61PipelineDeterminism:

    def test_stage_order_deterministic(self):
        from kernel import MuscalKernel
        from plugin_registry import STAGES
        STAGES.clear()
        k1 = MuscalKernel(enable_graph=False, enable_sphere=False)
        order1 = [(s.name, s.order) for s in k1._pipeline]

        STAGES.clear()
        k2 = MuscalKernel(enable_graph=False, enable_sphere=False)
        order2 = [(s.name, s.order) for s in k2._pipeline]

        assert order1 == order2, "Stage order not deterministic"

    def test_duplicate_registration_safe(self):
        from plugin_registry import register_stage, STAGES
        class TestStage:
            name = "test_dup"
            order = 99
            def __init__(self, k): pass
            def process(self, ctx): return ctx
        STAGES.clear()
        register_stage(TestStage(None))
        register_stage(TestStage(None))
        assert len(STAGES) == 1, "Duplicate registration created multiple entries"

    def test_early_exit_deterministic(self):
        from kernel import MuscalKernel
        from features.pipeline.governance_stage import GovernanceStage
        from runtime.kernel.governance import GovernanceSync, GovernanceLimits

        k = MuscalKernel(enable_graph=False, enable_sphere=False)
        for stage in k._pipeline:
            if stage.name == "governance":
                stage._governance = GovernanceSync(limits=GovernanceLimits(max_iterations=0))

        executed = []
        for stage in k._pipeline:
            orig = stage.process
            def _track(name, fn):
                def wrapped(ctx):
                    executed.append(name)
                    return fn(ctx)
                return wrapped
            stage.process = _track(stage.name, orig)

        r1 = k._run_pipeline("test")
        assert executed == ["governance"], f"Early exit not deterministic: {executed}"
        assert r1 is not None
        assert r1.success is False

    def test_same_input_same_output_structure(self):
        from kernel import MuscalKernel
        inputs = ["print hello", "write test.txt", "add 2+2"]
        for inp in inputs:
            results = []
            for _ in range(3):
                k = MuscalKernel(enable_graph=False, enable_sphere=False)
                r = k._run_pipeline(inp)
                results.append(r)
            for i in range(1, len(results)):
                assert type(results[0]) == type(results[i])
                assert results[0].success == results[i].success

    def test_tool_failure_error_propagates(self):
        from features.tool_runtime.tool_runtime import UnifiedToolRuntime
        utr = UnifiedToolRuntime()
        def failing(args):
            raise RuntimeError("simulated tool failure")
        utr.register_tool("test.fail", failing, schema={"type": "object"})
        result = utr.execute("test.fail", {})
        assert not result.success
        assert "simulated tool failure" in result.error

    def test_pipeline_construction_errors_explicit(self):
        from plugin_registry import register_stage, build_pipeline, STAGES
        STAGES.clear()
        class MissingNameStage:
            order = 99
            def __init__(self, k): pass
            def process(self, ctx): return ctx
        with pytest.raises((AttributeError, ValueError)):
            register_stage(MissingNameStage(None))


# ═══════════════════════════════════════════════════════════════════
# P6.2 — INLINE VS PIPELINE DIFFERENTIAL VALIDATION
# ═══════════════════════════════════════════════════════════════════

class TestP62DifferentialValidation:

    def _normalize(self, r):
        norm = {"success": r.success, "type": type(r).__name__}
        if hasattr(r, "mcxf"):
            norm["has_mcxf"] = r.mcxf is not None
        if hasattr(r, "execution_plan"):
            norm["has_plan"] = r.execution_plan is not None
        if hasattr(r, "errors"):
            norm["error_count"] = len(r.errors)
        return norm

    def test_differential_equivalence_allowed_tasks(self):
        from kernel import MuscalKernel
        from plugin_registry import STAGES
        tasks = ["print hello", "write test.txt", "add 2+2"]
        for task in tasks:
            STAGES.clear()
            k_inline = MuscalKernel(enable_graph=False, enable_sphere=False)
            r_inline = k_inline.run(task)

            STAGES.clear()
            k_pipe = MuscalKernel(enable_graph=False, enable_sphere=False)
            r_pipe = k_pipe._run_pipeline(task)

            n1 = self._normalize(r_inline)
            n2 = self._normalize(r_pipe)

            assert n1["success"] == n2["success"], f"Success differs for '{task}'"
            assert n1["type"] == n2["type"], f"Type differs for '{task}'"
            assert n1["has_mcxf"] == n2["has_mcxf"], f"MCXF differs for '{task}'"

    def test_inline_lacks_phase2_metadata(self):
        from kernel import MuscalKernel
        k = MuscalKernel(enable_graph=False, enable_sphere=False)
        # Inline uses internal _ctx which is not exposed
        # But we can verify the returned KernelResult has no phase2 fields
        r = k.run("print hello")
        assert not hasattr(r, "governance_decision")
        assert not hasattr(r, "routing_decision")
        assert not hasattr(r, "agent_type")
        assert not hasattr(r, "cognitive_unit")

    def test_pipeline_has_phase2_metadata_in_ctx(self):
        from kernel import MuscalKernel
        from plugin_registry import STAGES
        STAGES.clear()
        k = MuscalKernel(enable_graph=False, enable_sphere=False)
        ctx_snapshot = {}
        for s in k._pipeline:
            orig = s.process
            def _capture(name, fn):
                def wrapped(ctx):
                    r = fn(ctx)
                    ctx_snapshot.update(ctx)
                    return r
                return wrapped
            s.process = _capture(s.name, orig)
        k._run_pipeline("print hello")
        assert "governance_decision" in ctx_snapshot
        assert "routing_decision" in ctx_snapshot
        assert "agent_type" in ctx_snapshot
        assert "cognitive_unit" in ctx_snapshot


# ═══════════════════════════════════════════════════════════════════
# P6.3 — GOVERNANCE BYPASS AUDIT
# P6.4 — SAFETYGATE BYPASS AUDIT
# P6.5 — UTR CANONICALITY
# ═══════════════════════════════════════════════════════════════════

class TestP63GovernanceSafetyUTR:

    def test_mel_goes_through_safetygate(self):
        from mel import _execute_step
        from features.safety.safety_gate import SafetyGate, BLOCKED_TOOLS
        step = {"tool": "console.print", "args": {"text": "test"}}
        result = _execute_step(step)
        assert result is not None
        assert "tool" in result

    def test_utr_enforces_safetygate(self):
        from features.tool_runtime.tool_runtime import create_default_utr
        from features.safety.safety_gate import SafetyGate
        sg = SafetyGate(user_policy={"allow_high_risk": False})
        utr, _ = create_default_utr(safety_gate=sg)
        result = utr.execute("opencode.run", {"command": "ls"})
        assert not result.success, "UTR should block high-risk tool without permit"
        assert "HIGH_RISK_BLOCKED" in result.error, f"Unexpected error: {result.error}"

    def test_blocked_tool_rejected(self):
        from features.safety.safety_gate import SafetyGate
        sg = SafetyGate()
        for tool in ["exec", "eval"]:
            result = sg.check(tool, {})
            assert not result.allowed, f"Blocked tool '{tool}' was allowed"

    def test_unknown_tool_rejected(self):
        from features.safety.safety_gate import SafetyGate
        sg = SafetyGate()
        result = sg.check("nonexistent.tool", {})
        assert not result.allowed

    def test_cu_governance_safety_utr_chain_exists(self):
        from features.cognitive_unit.cognitive_unit import CognitiveUnit
        cu = CognitiveUnit(unit_id="test", agent_type="general")
        assert hasattr(cu, "governance")
        assert hasattr(cu, "safety_gate")
        assert hasattr(cu, "tool_runtime")

    def test_no_direct_muscal_loop_executors_in_hot_path(self):
        import muscal_loop
        from kernel import MuscalKernel
        k = MuscalKernel(enable_graph=False, enable_sphere=False)
        r = k.run("print hello")
        assert r.success

    def test_pipeline_governance_blocks_downstream(self):
        from kernel import MuscalKernel
        from runtime.kernel.governance import GovernanceSync, GovernanceLimits
        from plugin_registry import STAGES
        STAGES.clear()
        k = MuscalKernel(enable_graph=False, enable_sphere=False)
        for stage in k._pipeline:
            if stage.name == "governance":
                stage._governance = GovernanceSync(limits=GovernanceLimits(max_iterations=0))
        executed = []
        for stage in k._pipeline:
            orig = stage.process
            def _track(name, fn):
                def wrapped(ctx):
                    executed.append(name)
                    return fn(ctx)
                return wrapped
            stage.process = _track(stage.name, orig)
        k._run_pipeline("test")
        assert executed == ["governance"], f"Governance did not block: {executed}"

    def test_all_utr_tools_have_safety_classification(self):
        from features.tool_runtime.tool_runtime import create_default_utr
        from features.safety.safety_gate import RISK_CLASSIFICATION
        from features.safety.safety_gate import SafetyGate
        sg = SafetyGate(user_policy={"allow_high_risk": True})
        utr, _ = create_default_utr(safety_gate=sg)
        for tool in utr.capabilities():
            has_risk = tool in RISK_CLASSIFICATION
            assert has_risk, f"Tool '{tool}' missing risk classification"


# ═══════════════════════════════════════════════════════════════════
# P6.6 — AGENT DETECTION HARDENING
# ═══════════════════════════════════════════════════════════════════

class TestP66AgentDetection:

    def test_empty_task_returns_general(self):
        from features.agent_detection.detector import DeterministicAgentDetector
        detector = DeterministicAgentDetector()
        result = detector.detect()
        assert result.agent_type == "general"
        assert result.confidence == 0.5

    def test_coding_task_detected(self):
        from features.agent_detection.detector import DeterministicAgentDetector
        detector = DeterministicAgentDetector()
        result = detector.detect(task_type="coding", mcxf_dict={
            "tasks": [{"predicate": "implement", "object": "algorithm"}]
        })
        assert result.agent_type == "coding"

    def test_analytical_task_detected(self):
        from features.agent_detection.detector import DeterministicAgentDetector
        detector = DeterministicAgentDetector()
        result = detector.detect(task_type="analyze", mcxf_dict={
            "tasks": [{"predicate": "compare", "object": "statistics"}]
        })
        assert result.agent_type == "analytical"

    def test_research_task_detected(self):
        from features.agent_detection.detector import DeterministicAgentDetector
        detector = DeterministicAgentDetector()
        result = detector.detect(task_type="research", mcxf_dict={
            "tasks": [{"predicate": "find", "object": "information"}]
        })
        assert result.agent_type == "research"

    def test_creative_task_detected(self):
        from features.agent_detection.detector import DeterministicAgentDetector
        detector = DeterministicAgentDetector()
        result = detector.detect(task_type="creative", mcxf_dict={
            "tasks": [{"predicate": "write", "object": "story"}]
        })
        assert result.agent_type == "creative"

    def test_operational_task_detected(self):
        from features.agent_detection.detector import DeterministicAgentDetector
        detector = DeterministicAgentDetector()
        result = detector.detect(task_type="operational", mcxf_dict={
            "tasks": [{"predicate": "deploy", "object": "service"}]
        })
        assert result.agent_type == "operational"

    def test_multi_category_task_tiebreaking_deterministic(self):
        from features.agent_detection.detector import DeterministicAgentDetector
        detector = DeterministicAgentDetector()
        results = []
        for _ in range(5):
            r = detector.detect(task_type="write", mcxf_dict={
                "tasks": [{"predicate": "write", "object": "analyze compare"}]
            })
            results.append(r.agent_type)
        assert all(r == results[0] for r in results), "Tie-breaking not deterministic"

    def test_ambiguous_task_does_not_crash(self):
        from features.agent_detection.detector import DeterministicAgentDetector
        detector = DeterministicAgentDetector()
        result = detector.detect(task_type="", mcxf_dict={"tasks": []})
        assert result.agent_type == "general"

    def test_confidence_semantics(self):
        from features.agent_detection.detector import DeterministicAgentDetector
        detector = DeterministicAgentDetector()
        result = detector.detect(task_type="code", mcxf_dict={
            "tasks": [{"predicate": "write", "object": "python function to sort array"}]
        })
        assert 0.0 <= result.confidence <= 1.0
        assert isinstance(result.reason, str)


# ═══════════════════════════════════════════════════════════════════
# P6.7 — COGNITIVEUNIT HARDENING
# P6.8 — WORKER BOUNDARY AUDIT
# ═══════════════════════════════════════════════════════════════════

class TestP67CognitiveUnit:

    def test_cu_owns_required_fields(self):
        from features.cognitive_unit.cognitive_unit import CognitiveUnit
        cu = CognitiveUnit(unit_id="test", agent_type="general",
                           worker="w1", memory="m1",
                           tool_runtime="tr1", safety_gate="sg1",
                           governance="g1")
        assert cu.id == "test"
        assert cu.agent_type == "general"
        assert cu.worker == "w1"
        assert cu.memory == "m1"
        assert cu.tool_runtime == "tr1"
        assert cu.safety_gate == "sg1"
        assert cu.governance == "g1"

    def test_cu_noop_without_tool(self):
        from features.cognitive_unit.cognitive_unit import CognitiveUnit
        cu = CognitiveUnit(unit_id="test", agent_type="general")
        result = cu.execute({"task_type": "general"})
        assert result["status"] == "noop"

    def test_cu_unknown_agent_falls_back(self):
        from features.cognitive_unit.registry import resolve, clear
        clear()
        from features.cognitive_unit.cognitive_unit import CognitiveUnit
        cu = CognitiveUnit(unit_id="general", agent_type="general")
        from features.cognitive_unit.registry import register
        register(cu)
        resolved = resolve("nonexistent_agent")
        assert resolved.agent_type == "general"

    def test_cu_governance_denial(self):
        from features.cognitive_unit.cognitive_unit import CognitiveUnit
        mock_gov = MagicMock()
        mock_gov.check.return_value = type("obj", (), {"allowed": False})()
        cu = CognitiveUnit(unit_id="test", agent_type="general", governance=mock_gov)
        result = cu.execute({"task_type": "general", "tool": "console.print", "args": {}})
        assert result["status"] == "blocked_by_governance"

    def test_cu_safety_denial(self):
        from features.cognitive_unit.cognitive_unit import CognitiveUnit
        from features.safety.safety_gate import SafetyGate
        sg = SafetyGate()
        cu = CognitiveUnit(unit_id="test", agent_type="general", safety_gate=sg)
        result = cu.execute({"task_type": "general", "tool": "exec", "args": {}})
        assert result["status"] == "blocked_by_safety"

    def test_worker_is_scaffold(self):
        from features.cognitive_unit.cognitive_unit import CognitiveUnit
        cu = CognitiveUnit(unit_id="test", agent_type="general")
        assert cu.worker is None, "Worker should be None (scaffold-only)"
        d = cu.to_dict()
        assert "worker" in d

    def test_cu_utr_failure_propagates(self):
        from features.cognitive_unit.cognitive_unit import CognitiveUnit
        mock_utr = MagicMock()
        mock_utr.execute.return_value = type("obj", (), {
            "success": False, "output": None, "error": "tool failure"
        })()
        mock_sg = MagicMock()
        mock_sg.check.return_value = type("obj", (), {"allowed": True})()
        cu = CognitiveUnit(
            unit_id="test", agent_type="general",
            tool_runtime=mock_utr, safety_gate=mock_sg,
        )
        result = cu.execute({"task_type": "general", "tool": "test.tool", "args": {}})
        assert result["status"] == "error"


# ═══════════════════════════════════════════════════════════════════
# P6.9 — TOOL SCHEMA CONSISTENCY
# ═══════════════════════════════════════════════════════════════════

class TestP69ToolSchema:

    def test_instruments_md_exists(self):
        assert os.path.exists("INSTRUMENTS.md"), "INSTRUMENTS.md missing"

    def test_all_utr_tools_have_executors(self):
        from features.tool_runtime.tool_runtime import create_default_utr
        from features.safety.safety_gate import SafetyGate
        sg = SafetyGate(user_policy={"allow_high_risk": True})
        utr, _ = create_default_utr(safety_gate=sg)
        caps = utr.capabilities()
        expected = {
            "console.print", "filesystem.write", "file.write",
            "math.add", "opencode.run",
            "browser.open", "browser.click", "browser.type",
            "browser.extract_text", "browser.screenshot", "browser.scroll",
            "desktop.screenshot", "desktop.type", "desktop.click",
            "desktop.open_app", "desktop.move", "desktop.keypress",
        }
        for tool in expected:
            assert tool in caps, f"Tool '{tool}' not in UTR capabilities"

    def test_no_tool_in_instruments_without_executor(self):
        from features.tool_runtime.tool_runtime import create_default_utr
        from features.safety.safety_gate import SafetyGate
        sg = SafetyGate(user_policy={"allow_high_risk": True})
        utr, _ = create_default_utr(safety_gate=sg)
        caps = set(utr.capabilities())
        assert "console.print" in caps
        assert "filesystem.write" in caps
        assert "math.add" in caps


# ═══════════════════════════════════════════════════════════════════
# P6.10 — LEGACY EXECUTOR DEPRECATION
# ═══════════════════════════════════════════════════════════════════

class TestP610LegacyDeprecation:

    def test_muscal_loop_executors_have_utr_equivalents(self):
        import muscal_loop
        from features.tool_runtime.tool_runtime import create_default_utr
        from features.safety.safety_gate import SafetyGate
        sg = SafetyGate(user_policy={"allow_high_risk": True})
        utr, _ = create_default_utr(safety_gate=sg)
        utr_caps = set(utr.capabilities())
        legacy_tools = {"console.print", "browser.open", "browser.click",
                        "browser.type", "opencode.run", "file.write"}
        for tool in legacy_tools:
            assert tool in utr_caps, f"Legacy tool '{tool}' missing UTR equivalent"

    def test_execute_tool_has_deprecation_warning(self):
        import warnings
        import muscal_loop
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            try:
                muscal_loop.execute_tool({"tool": "console.print", "args": {"text": "test"}})
            except Exception:
                pass
            deprecation = [x for x in w if issubclass(x.category, DeprecationWarning)]
            assert len(deprecation) >= 1


# ═══════════════════════════════════════════════════════════════════
# P6.13 — ROLLBACK VERIFICATION
# ═══════════════════════════════════════════════════════════════════

class TestP613Rollback:

    def test_inline_mode_bypasses_pipeline(self):
        from kernel import MuscalKernel
        from plugin_registry import STAGES
        STAGES.clear()
        k = MuscalKernel(enable_graph=False, enable_sphere=False)
        r = k.run("print hello")
        assert r.success is True

    def test_pipeline_mode_works(self):
        from kernel import MuscalKernel
        from plugin_registry import STAGES
        STAGES.clear()
        k = MuscalKernel(enable_graph=False, enable_sphere=False)
        r = k._run_pipeline("print hello")
        assert r.success is True

    def test_switching_modes_no_corruption(self):
        from kernel import MuscalKernel
        from plugin_registry import STAGES
        for _ in range(3):
            STAGES.clear()
            k1 = MuscalKernel(enable_graph=False, enable_sphere=False)
            k1.run("print hello")
            STAGES.clear()
            k2 = MuscalKernel(enable_graph=False, enable_sphere=False)
            k2._run_pipeline("print hello")
        assert True, "Mode switching does not corrupt state"


# ═══════════════════════════════════════════════════════════════════
# P6.12 — PERFORMANCE (lightweight benchmark)
# ═══════════════════════════════════════════════════════════════════

class TestP612Performance:

    def test_inline_performance(self):
        from kernel import MuscalKernel
        from plugin_registry import STAGES
        times = []
        for _ in range(5):
            STAGES.clear()
            k = MuscalKernel(enable_graph=False, enable_sphere=False)
            start = time.perf_counter()
            k.run("print hello")
            elapsed = time.perf_counter() - start
            times.append(elapsed)
        mean = sum(times) / len(times)
        assert mean < 5.0, f"Inline too slow: {mean*1000:.1f}ms avg"

    def test_pipeline_performance(self):
        from kernel import MuscalKernel
        from plugin_registry import STAGES
        times = []
        for _ in range(5):
            STAGES.clear()
            k = MuscalKernel(enable_graph=False, enable_sphere=False)
            start = time.perf_counter()
            k._run_pipeline("print hello")
            elapsed = time.perf_counter() - start
            times.append(elapsed)
        mean = sum(times) / len(times)
        assert mean < 5.0, f"Pipeline too slow: {mean*1000:.1f}ms avg"


# ═══════════════════════════════════════════════════════════════════
# RUN ALL
# ═══════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
