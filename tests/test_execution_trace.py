import memory
import mkc_rules


import pytest


@pytest.fixture(autouse=True)
def _setup():
    memory._conn = None
    mkc_rules.reset_state()


def test_execution_trace():
    from kernel import MuscalKernel
    from debugger import DebugEngine

    debugger = DebugEngine()
    kernel = MuscalKernel(enable_graph=True, enable_sphere=False, debugger=debugger)
    result = kernel.run("print trace_test")
    assert result.success is True

    debug_nodes = list(debugger.graph.nodes.values())
    assert len(debug_nodes) > 0

    debug_types = {}
    for n in debug_nodes:
        t = n.type
        debug_types[t] = debug_types.get(t, 0) + 1
    assert len(debug_types) >= 2

    has_stage = any(
        "rag" in t.lower() or "mkc" in t.lower()
        or "bridge" in t.lower() or "mel" in t.lower()
        or "memory" in t.lower() for t in debug_types
    )
    assert has_stage

    assert len(debugger.graph.edges) >= 0

    snapshot = debugger.get_debug_snapshot()
    assert "execution_path" in snapshot
    assert "graph_state" in snapshot
    assert "metrics" in snapshot
    assert "total_execution_time" in snapshot.get("metrics", {})

    output = debugger.get_full_output()
    assert output is not None
    assert "status" in output
    assert "debug_snapshot" in output
    assert "warnings" in output
    assert "performance_summary" in output

    ps = output.get("performance_summary", {})
    assert ps.get("total_execution_time", 0) > 0
    assert ps.get("stages_monitored", [])
    assert ps.get("total_nodes", 0) > 0

    assert debugger._memory_write_count >= 1
