import pytest
import memory


@pytest.fixture(autouse=True)
def _setup():
    memory._conn = None
    memory.init()


def test_store_and_retrieve_round_trip():
    input_text = "test input alpha"
    mcxf_data = {"decisions": [{"subject": "test", "predicate": "is", "object": "data"}],
                 "tasks": [{"tool": "console.print", "args": {"message": "hello"}}]}
    result_data = [{"tool": "console.print", "message": "hello", "status": "ok"}]
    feedback_data = {"summary": "test feedback", "confidence_adjustments": {}}

    mem_id = memory.store_snapshot(input_text, mcxf_data, result_data, feedback_data)
    assert mem_id is not None and mem_id > 0

    retrieved = memory.retrieve_by_id(mem_id)
    assert retrieved is not None
    assert retrieved["input_text"] == input_text
    assert isinstance(retrieved["mcxf"], dict)
    assert retrieved["mcxf"].get("decisions") == mcxf_data["decisions"]
    assert retrieved["result"] == result_data
    assert retrieved["feedback"] == feedback_data
    assert "created_at" in retrieved and retrieved["created_at"] is not None


def test_multiple_snapshots_independent():
    mem_id = memory.store_snapshot(
        "test input alpha",
        {"decisions": [{"subject": "test", "predicate": "is", "object": "data"}],
         "tasks": [{"tool": "console.print", "args": {"message": "hello"}}]},
        [{"tool": "console.print", "message": "hello", "status": "ok"}],
        {"summary": "test feedback", "confidence_adjustments": {}}
    )
    mem_id_2 = memory.store_snapshot(
        "second input beta",
        {"tasks": [{"tool": "math.add", "args": {"a": 1, "b": 2}}]},
        [{"tool": "math.add", "result": 3, "status": "ok"}],
        None
    )

    r1 = memory.retrieve_by_id(mem_id)
    r2 = memory.retrieve_by_id(mem_id_2)
    assert r1["input_text"] == "test input alpha"
    assert r2["input_text"] == "second input beta"
    assert r1["mcxf"] != r2["mcxf"]


def test_search_by_keyword():
    memory.store_snapshot("test input alpha",
        {"tasks": [{"tool": "console.print", "args": {"message": "hello"}}]},
        [{"tool": "console.print", "message": "hello", "status": "ok"}],
        None
    )
    results = memory.search_by_keyword("alpha")
    assert len(results) >= 1
    assert any("alpha" in r["input_text"] for r in results)


def test_recent_newest_first():
    memory.store_snapshot("first input", {"tasks": []}, [{"ok": True}], None)
    memory.store_snapshot("second input", {"tasks": []}, [{"ok": True}], None)
    recent = memory.get_recent(limit=2)
    assert len(recent) == 2
    assert recent[0]["id"] > recent[1]["id"]
    assert recent[0]["input_text"] == "second input"


def test_kernel_stores_memory():
    from kernel import MuscalKernel
    k = MuscalKernel(enable_graph=False, enable_sphere=False)
    pipe_result = k.run("print consistency_check")
    assert pipe_result.memory_id is not None and pipe_result.memory_id > 0
    pipe_mem = memory.retrieve_by_id(pipe_result.memory_id)
    assert pipe_mem is not None
    assert pipe_mem["input_text"] == "print consistency_check"
    assert "mcxf" in pipe_mem
    assert "result" in pipe_mem
    assert "feedback" in pipe_mem
