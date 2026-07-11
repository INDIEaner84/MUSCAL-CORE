import json
import memory
import mkc_rules


import pytest


@pytest.fixture(autouse=True)
def _setup():
    memory._conn = None
    mkc_rules.reset_state()


def test_replay_determinism():
    from kernel import MuscalKernel
    from schema import NODE_TYPE_MKC_STEP

    kernel = MuscalKernel(enable_graph=True, enable_sphere=False)
    INPUT_TEXT = "print hello"

    results = []
    for i in range(3):
        r = kernel.run(INPUT_TEXT)
        results.append(r)
        assert r is not None
        assert r.success is True

    tasks_set = set()
    for i, r in enumerate(results):
        tasks_json = json.dumps(
            [(t.subject, t.predicate, t.object) for t in r.mcxf.tasks],
            sort_keys=True, default=str
        )
        tasks_set.add(tasks_json)
        assert len(tasks_json) > 0
    assert len(tasks_set) == 1

    exec_set = set()
    for i, r in enumerate(results):
        exec_json = json.dumps(r.execution, sort_keys=True, default=str)
        exec_set.add(exec_json)
    assert len(exec_set) == 1

    mem_ids = [r.memory_id for r in results]
    assert len(set(mem_ids)) == 3

    for i, r in enumerate(results):
        exec_step = r.execution[0] if r.execution else {}
        assert exec_step.get("printed") == "hello"


def test_fresh_kernel_graph_consistency():
    from kernel import MuscalKernel
    from schema import NODE_TYPE_MKC_STEP

    for i in range(3):
        k = MuscalKernel(enable_graph=True, enable_sphere=False)
        r = k.run("print test")
        types = {n.type for nid, n in k.graph.nodes.items()}
        assert NODE_TYPE_MKC_STEP in types
