import pytest
import memory
import mkc_rules


@pytest.fixture(autouse=True)
def _setup():
    memory._conn = None
    mkc_rules.reset_state()


def test_full_pipeline():
    from kernel import MuscalKernel
    from debugger import DebugEngine
    from schema import (
        NODE_TYPE_RAG_CONTEXT, NODE_TYPE_MKC_STEP, NODE_TYPE_MCXF_SECTION,
        NODE_TYPE_EXECUTION_PLAN, NODE_TYPE_TOOL_EXECUTION, NODE_TYPE_MEMORY_ENTRY,
        NODE_TYPE_INTENT,
    )
    debugger = DebugEngine()
    kernel = MuscalKernel(enable_graph=True, enable_sphere=False, debugger=debugger)
    assert kernel is not None
    assert kernel.graph is not None
    assert kernel.memory is not None
    result = kernel.run("print hello")
    assert result is not None
    assert result.success is True
    assert result.mcxf is not None
    assert len(result.mcxf.tasks) > 0
    assert result.execution is not None
    assert len(result.execution) > 0
    assert result.memory_id is not None and result.memory_id > 0
    assert result.feedback is not None
    node_types = {n.type for nid, n in kernel.graph.nodes.items()}
    assert NODE_TYPE_RAG_CONTEXT in node_types or NODE_TYPE_INTENT in node_types
    assert NODE_TYPE_MKC_STEP in node_types
    assert NODE_TYPE_MCXF_SECTION in node_types
    assert NODE_TYPE_EXECUTION_PLAN in node_types
    assert NODE_TYPE_TOOL_EXECUTION in node_types
    assert NODE_TYPE_MEMORY_ENTRY in node_types
    assert len(kernel.graph.edges) > 0
    debug_nodes = list(debugger.graph.nodes.values())
    assert len(debug_nodes) > 0
    debug_types = {n.type for n in debug_nodes}
    assert len(debug_types) >= 1
    has_stage = any(
        "rag" in n.type.lower() or "mkc" in n.type.lower()
        or "bridge" in n.type.lower() or "mel" in n.type.lower()
        or "memory" in n.type.lower() for n in debug_nodes
    )
    assert has_stage
