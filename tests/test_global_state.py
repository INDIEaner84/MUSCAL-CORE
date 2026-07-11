import threading
import memory
import mkc_rules
import mel


import pytest


@pytest.fixture(autouse=True)
def _setup():
    memory._conn = None
    mkc_rules.reset_state()


def test_memory_lock():
    assert hasattr(memory, "_lock")
    assert memory._lock is not None
    acquired = memory._lock.acquire(timeout=1)
    assert acquired
    reacquired = memory._lock.acquire(timeout=1)
    assert reacquired
    memory._lock.release()
    memory._lock.release()


def test_memory_operations():
    memory.init()
    memory_id = memory.store_snapshot("test_input", {"key": "val"}, {"ok": True}, {"msg": "good"})
    assert memory_id is not None and memory_id > 0
    retrieved = memory.retrieve_by_id(memory_id)
    assert retrieved is not None
    assert retrieved["input_text"] == "test_input"
    recent = memory.get_recent(limit=1)
    assert len(recent) == 1


def test_mkc_rules_lock():
    assert hasattr(mkc_rules, "_lock")
    acquired = mkc_rules._lock.acquire(timeout=1)
    assert acquired
    reacquired = mkc_rules._lock.acquire(timeout=1)
    assert reacquired
    mkc_rules._lock.release()
    mkc_rules._lock.release()


def test_mkc_rules_operations():
    snapshot = mkc_rules.get_signal_rules_snapshot()
    assert "DECISIONS" in snapshot
    assert "TASKS" in snapshot
    classified = mkc_rules.classify_statement("we will build")
    assert classified["section"] is not None
    assert classified["confidence"] > 0.5
    conf = mkc_rules.get_effective_confidence("TASKS")
    assert conf > 0.0
    mkc_rules.reset_state()
    assert mkc_rules._keyword_additions_count == 0
    assert len(mkc_rules._tool_failure_history) == 0


def test_mel_lock():
    assert hasattr(mel, "_lock")
    acquired = mel._lock.acquire(timeout=1)
    assert acquired
    reacquired = mel._lock.acquire(timeout=1)
    assert reacquired
    mel._lock.release()
    mel._lock.release()


def test_trace_engine():
    from trace_engine import TraceEngine, _TRACE, log, reset_trace
    engine = TraceEngine()
    assert hasattr(engine, "_lock")
    engine.log("COMPUTE", "test_event", {"msg": "hello"})
    snap = engine.snapshot()
    assert len(snap) == 1
    assert snap[0]["type"] == "test_event"
    engine.clear()
    snap = engine.snapshot()
    assert len(snap) == 0
    log("OBSERVABILITY", "ping", {"val": 1}, trace_level=0)
    snap = _TRACE.snapshot()
    assert len(snap) >= 1
    reset_trace()
    snap = _TRACE.snapshot()
    assert len(snap) == 0


def test_concurrent_memory_writes():
    memory.init()
    concurrent_errors = []

    def thread_write(tid):
        try:
            mid = memory.store_snapshot(f"concurrent_{tid}", {"t": tid}, {"ok": True})
            r = memory.retrieve_by_id(mid)
            if r is None or r["input_text"] != f"concurrent_{tid}":
                concurrent_errors.append(f"Thread {tid}: retrieve mismatch")
        except Exception as e:
            concurrent_errors.append(f"Thread {tid}: {e}")

    threads = [threading.Thread(target=thread_write, args=(i,)) for i in range(10)]
    for t in threads:
        t.start()
    for t in threads:
        t.join(timeout=10)
    assert len(concurrent_errors) == 0
