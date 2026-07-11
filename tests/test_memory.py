import pytest
import memory


@pytest.fixture(autouse=True)
def _setup():
    memory._conn = None
    memory.init()


def test_store_and_retrieve():
    mem_id = memory.store_snapshot(
        "print hello",
        {"tasks": [{"section": "06_TASKS", "subject": "system", "predicate": "print", "object": "hello"}]},
        [{"printed": {"message": "hello"}}],
        feedback={"score": 0.9}
    )
    assert mem_id is not None and mem_id > 0
    retrieved = memory.retrieve_by_id(mem_id)
    assert retrieved is not None
    assert retrieved["input_text"] == "print hello"
    assert len(retrieved["result"]) == 1
    assert retrieved["feedback"]["score"] == 0.9


def test_search():
    memory.store_snapshot("add 5 and 3", {"tasks": []}, [{"result": 8}])
    search_results = memory.search_by_keyword("hello", limit=3)
    assert len(search_results) >= 1
    assert any("hello" in r["input_text"] for r in search_results)
    no_results = memory.search_by_keyword("zzzzz_nonexistent", limit=3)
    assert len(no_results) == 0


def test_recent():
    memory.store_snapshot("add 5 and 3", {"tasks": []}, [{"result": 8}])
    recent = memory.get_recent(limit=2)
    assert len(recent) >= 1
    assert "created_at" in recent[0]
    assert "input_text" in recent[0]
