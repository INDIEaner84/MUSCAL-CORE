import pytest
from schema import ExecutionPlan
from runtime.optimizer.pipeline import OptimizerPipeline, OptimizedPlan
from runtime.optimizer.graph import ExecutionDAG


def _plan(steps: list) -> ExecutionPlan:
    return ExecutionPlan(intent="test", steps=steps)


def test_optimize_empty_plan():
    pipe = OptimizerPipeline()
    opt_plan, report = pipe.optimize(_plan([]))
    assert isinstance(opt_plan, OptimizedPlan)
    assert opt_plan.num_layers == 0
    assert opt_plan.num_nodes == 0
    assert isinstance(report.node_count_before, int)
    assert report.node_count_before == 0


def test_optimize_single_step():
    pipe = OptimizerPipeline()
    opt_plan, report = pipe.optimize(_plan([
        {"tool": "console.print", "args": {"message": "hello"}}
    ]))
    assert opt_plan.num_nodes == 1
    assert opt_plan.num_layers >= 1
    assert opt_plan.layers[0][0]["tool"] == "console.print"
    assert report.node_count_before == 1
    assert report.node_count_after == 1


def test_optimize_skipped_tools_handled():
    pipe = OptimizerPipeline()
    opt_plan, report = pipe.optimize(_plan([
        {"tool": "console.print", "args": {"message": "a"}},
        {"tool": "UNMAPPED", "original_task": "do x", "reason": "No match"},
        {"tool": "math.add", "args": {"a": 1, "b": 2}},
    ]))
    assert report.node_count_before == 3
    assert report.verification.get("passed") is not False
    assert report.removed_nodes >= 0


def test_optimize_parallelization():
    pipe = OptimizerPipeline()
    opt_plan, report = pipe.optimize(_plan([
        {"tool": "console.print", "args": {"message": "a"}, "depends_on": []},
        {"tool": "math.add", "args": {"a": 1, "b": 2}, "depends_on": []},
    ]))
    assert opt_plan.num_layers >= 1
    assert report.parallel_layers >= 1


def test_optimize_verification_passes():
    pipe = OptimizerPipeline()
    _, report = pipe.optimize(_plan([
        {"tool": "console.print", "args": {"message": "hello"}},
        {"tool": "math.add", "args": {"a": 1, "b": 2}},
    ]))
    assert report.verification.get("passed") is not False
    assert len(report.passes_applied) == 3


def test_optimize_determinism():
    pipe = OptimizerPipeline()
    plan = _plan([
        {"tool": "console.print", "args": {"message": "hello"}},
        {"tool": "math.add", "args": {"a": 1, "b": 2}},
        {"tool": "console.print", "args": {"message": "done"}},
    ])
    opt1, rep1 = pipe.optimize(plan)
    opt2, rep2 = pipe.optimize(plan)
    assert opt1.num_nodes == opt2.num_nodes
    assert opt1.num_layers == opt2.num_layers
    assert opt1.to_dict()["layers"] == opt2.to_dict()["layers"]
    assert rep1.determinism == "PASS"


def test_optimize_total_cost():
    pipe = OptimizerPipeline()
    opt_plan, _ = pipe.optimize(_plan([
        {"tool": "console.print", "args": {"message": "a"}},
        {"tool": "console.print", "args": {"message": "b"}},
    ]))
    assert opt_plan.total_cost > 0
    assert isinstance(opt_plan.total_cost, float)


def test_optimize_to_dict():
    pipe = OptimizerPipeline()
    opt_plan, _ = pipe.optimize(_plan([
        {"tool": "console.print", "args": {"message": "hello"}},
    ]))
    d = opt_plan.to_dict()
    assert "layers" in d
    assert "total_cost" in d
    assert "num_nodes" in d
    assert "num_layers" in d
    assert d["num_nodes"] == 1
    assert d["num_layers"] >= 1


def test_optimize_report_to_dict():
    pipe = OptimizerPipeline()
    _, report = pipe.optimize(_plan([
        {"tool": "console.print", "args": {"message": "hello"}},
    ]))
    d = report.to_dict()
    assert "pass_count" in d
    assert "node_count" in d
    assert "verification" in d
    assert d["pass_count"] == 3
