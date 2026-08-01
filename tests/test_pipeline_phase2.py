import os
import threading
from unittest.mock import MagicMock

import pytest

from features.pipeline.governance_stage import GovernanceStage
from features.pipeline.routing_stage import RoutingStage
from kernel import MuscalKernel
from runtime.kernel.governance import GovernanceSync, GovernanceLimits
from runtime.kernel.scheduler import RoutingPolicy


@pytest.fixture(autouse=True)
def storage_dir():
    os.makedirs("storage", exist_ok=True)


# ═══════════════════════════════════════════════════════════════════
# T1: GovernanceStage allows execution within configured limits
# ═══════════════════════════════════════════════════════════════════

def test_governance_allows_within_limits():
    k = MuscalKernel(enable_graph=False, enable_sphere=False)
    stage = GovernanceStage(k)
    stage._governance = GovernanceSync(limits=GovernanceLimits(max_iterations=10))

    ctx = {"input_text": "test", "kernel": k, "_errors": [], "_stage_metrics": {}}
    ctx = stage.process(ctx)

    assert ctx["governance_decision"] == "allowed"
    assert ctx["governance_status"] == "ok"
    assert ctx["governance_reason"] is None
    assert ctx.get("_early_exit") is None or ctx["_early_exit"] is False


# ═══════════════════════════════════════════════════════════════════
# T2: GovernanceStage blocks when iteration limit exceeded
# ═══════════════════════════════════════════════════════════════════

def test_governance_blocks_when_limit_exceeded():
    k = MuscalKernel(enable_graph=False, enable_sphere=False)
    stage = GovernanceStage(k)
    stage._governance = GovernanceSync(limits=GovernanceLimits(max_iterations=0))

    ctx = {"input_text": "test", "kernel": k, "_errors": [], "_stage_metrics": {}}
    ctx = stage.process(ctx)

    assert ctx["governance_decision"] == "blocked"
    assert ctx["governance_status"] == "violation"
    assert isinstance(ctx["governance_reason"], str)
    assert ctx.get("_early_exit") is True


# ═══════════════════════════════════════════════════════════════════
# T3: RoutingStage routes a known task_type
# ═══════════════════════════════════════════════════════════════════

def test_routing_known_task_type():
    k = MuscalKernel(enable_graph=False, enable_sphere=False)
    stage = RoutingStage(k)

    ctx = {
        "input_text": "print hello",
        "kernel": k,
        "mcxf_dict": {
            "tasks": [{"predicate": "print", "object": "hello"}]
        },
        "_errors": [],
        "_stage_metrics": {},
    }
    ctx = stage.process(ctx)

    assert ctx["routing_status"] == "routed"
    assert isinstance(ctx["routing_decision"], str)
    assert isinstance(ctx["routing_worker"], str)
    assert ctx["routing_task_type"] == "print_console"


# ═══════════════════════════════════════════════════════════════════
# T4: RoutingStage handles unknown task_type with deterministic fallback
# ═══════════════════════════════════════════════════════════════════

def test_routing_unknown_task_type():
    k = MuscalKernel(enable_graph=False, enable_sphere=False)
    stage = RoutingStage(k)

    ctx = {
        "input_text": "xyzzy flurbo",
        "kernel": k,
        "mcxf_dict": {
            "tasks": [{"predicate": "xyzzy", "object": "flurbo"}]
        },
        "_errors": [],
        "_stage_metrics": {},
    }
    ctx = stage.process(ctx)

    assert ctx["routing_status"] == "unknown"
    assert isinstance(ctx["routing_decision"], str)
    assert isinstance(ctx["routing_worker"], str)
    assert ctx["routing_task_type"] == "general"


# ═══════════════════════════════════════════════════════════════════
# T5: Pipeline registration includes Governance and Routing
# ═══════════════════════════════════════════════════════════════════

def test_pipeline_registration_includes_governance_and_routing():
    k = MuscalKernel(enable_graph=False, enable_sphere=False)
    stage_names = [s.name for s in k._pipeline]

    assert "governance" in stage_names
    assert "routing" in stage_names


# ═══════════════════════════════════════════════════════════════════
# T6: Pipeline ordering is correct
# ═══════════════════════════════════════════════════════════════════

def test_pipeline_ordering():
    from plugin_registry import STAGES
    STAGES.clear()
    k = MuscalKernel(enable_graph=False, enable_sphere=False)
    stage_order = [(s.name, s.order) for s in k._pipeline]

    expected = [
        ("governance", 5),
        ("rag", 10),
        ("mkc", 20),
        ("routing", 25),
        ("cognitive_unit", 27),
        ("mcxf", 30),
        ("bridge", 40),
        ("optimizer", 50),
        ("mel", 60),
        ("feedback", 70),
        ("memory", 80),
    ]
    assert stage_order == expected, f"Order mismatch:\n  got:      {stage_order}\n  expected: {expected}"


# ═══════════════════════════════════════════════════════════════════
# T7: Pipeline execution with governance violation blocks downstream
# ═══════════════════════════════════════════════════════════════════

def test_governance_block_stops_downstream_stages():
    k = MuscalKernel(enable_graph=False, enable_sphere=False)

    for stage in k._pipeline:
        if stage.name == "governance":
            stage._governance = GovernanceSync(limits=GovernanceLimits(max_iterations=0))

    executed = []

    for stage in k._pipeline:
        orig = stage.process
        def _make_tracked(name, orig_process):
            def tracked(ctx):
                executed.append(name)
                return orig_process(ctx)
            return tracked
        stage.process = _make_tracked(stage.name, orig)

    result = k._run_pipeline("test")

    assert executed == ["governance"], (
        f"Expected only governance to execute, got: {executed}"
    )
    assert result is not None, "_run_pipeline returned None instead of KernelResult"
    assert result.success is False
    assert hasattr(result, "errors")
    assert len(result.errors) > 0


# ═══════════════════════════════════════════════════════════════════
# T8: Inline execution remains unchanged
# ═══════════════════════════════════════════════════════════════════

def test_inline_path_no_governance_routing():
    k = MuscalKernel(enable_graph=False, enable_sphere=False)
    r = k.run("test hello")

    assert r is not None
    assert hasattr(r, "success")
    assert hasattr(r, "mcxf")
    assert hasattr(r, "execution_plan")


# ═══════════════════════════════════════════════════════════════════
# T9: Identical to baseline — covered by full suite run
# ═══════════════════════════════════════════════════════════════════

# T10: Differential test — inline vs pipeline
# ═══════════════════════════════════════════════════════════════════

def test_differential_inline_vs_pipeline_allowed():
    k_inline = MuscalKernel(enable_graph=False, enable_sphere=False)
    r_inline = k_inline.run("test hello")

    k_pipe = MuscalKernel(enable_graph=False, enable_sphere=False)

    pipeline_final_ctx = {}
    for s in k_pipe._pipeline:
        orig = s.process
        def _capture_ctx(name, orig_fn):
            def captured(ctx):
                result = orig_fn(ctx)
                pipeline_final_ctx.update(ctx)
                return result
            return captured
        s.process = _capture_ctx(s.name, orig)

    r_pipe = k_pipe._run_pipeline("test hello")

    assert type(r_inline) == type(r_pipe), "Result types differ"
    assert r_inline.success == r_pipe.success, "Success flags differ"

    assert "governance_decision" in pipeline_final_ctx
    assert "governance_status" in pipeline_final_ctx
    assert "routing_decision" in pipeline_final_ctx
    assert "routing_status" in pipeline_final_ctx

    assert pipeline_final_ctx["governance_decision"] == "allowed"
    assert pipeline_final_ctx["routing_status"] == "routed"


# ═══════════════════════════════════════════════════════════════════
# EIT-1: Governance-blocked request does NOT create downstream record
# ═══════════════════════════════════════════════════════════════════

def test_governance_block_no_downstream():
    stage = GovernanceStage(MuscalKernel(enable_graph=False, enable_sphere=False))
    stage._governance = GovernanceSync(limits=GovernanceLimits(max_iterations=0))

    ctx = {"input_text": "test", "_errors": [], "_stage_metrics": {}}
    ctx = stage.process(ctx)

    assert ctx["governance_decision"] == "blocked"
    assert "mcxf" not in ctx
    assert "execution_plan" not in ctx
    assert "mel_result" not in ctx


# ═══════════════════════════════════════════════════════════════════
# EIT-2: Unknown routing target NOT represented as specialized execution
# ═══════════════════════════════════════════════════════════════════

def test_unknown_route_not_specialized():
    k = MuscalKernel(enable_graph=False, enable_sphere=False)
    stage = RoutingStage(k)

    ctx = {
        "input_text": "xyzzy flurbo",
        "kernel": k,
        "mcxf_dict": {
            "tasks": [{"predicate": "xyzzy", "object": "flurbo"}]
        },
        "_errors": [],
        "_stage_metrics": {},
    }
    ctx = stage.process(ctx)

    assert ctx["routing_status"] == "unknown"
    assert ctx["routing_task_type"] == "general"


# ═══════════════════════════════════════════════════════════════════
# EIT-3: Pipeline context distinguishes routing proposal from execution
# ═══════════════════════════════════════════════════════════════════

def test_routing_metadata_distinct_from_execution():
    k = MuscalKernel(enable_graph=False, enable_sphere=False)
    stage = RoutingStage(k)

    ctx = {
        "input_text": "print hello",
        "kernel": k,
        "mcxf_dict": {
            "tasks": [{"predicate": "print", "object": "hello"}]
        },
        "_errors": [],
        "_stage_metrics": {},
    }
    ctx = stage.process(ctx)

    assert "routing_decision" in ctx
    assert "routing_worker" in ctx
    assert "routing_status" in ctx
    assert ctx["routing_status"] == "routed"
