import pytest


@pytest.mark.slow
def test_stress_100_iterations():
    from kernel import MuscalKernel
    kernel = MuscalKernel(enable_graph=True, enable_sphere=False)

    snapshots = []
    for i in range(100):
        result = kernel.run(f"test input {i}")
        g = kernel.graph
        snapshots.append({
            "iter": i,
            "success": result.success,
            "memory_id": result.memory_id,
            "graph_nodes": len(g.nodes) if g else 0,
            "graph_edges": len(g.edges) if g else 0,
            "focus": g.active_focus_node if g else "",
        })

    assert len(snapshots) == 100
    failures = [s["iter"] for s in snapshots if not s["success"]]
    assert len(failures) == 0, f"Failures at iterations: {failures}"

    r1 = kernel.run("drift check input")
    nodes_before = len(kernel.graph.nodes) if kernel.graph else 0
    r2 = kernel.run("drift check input")
    _ = len(kernel.graph.nodes) if kernel.graph else 0

    assert r1.success == r2.success
