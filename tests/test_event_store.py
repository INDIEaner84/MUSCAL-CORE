import json
import os
import sqlite3
import tempfile
import time
from pathlib import Path

import pytest
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


def _make_store(tmpdir: str):
    from runtime.event_store import EventStore

    db_path = Path(tmpdir) / "test_event_store.db"
    store = EventStore(db_path=db_path)
    return store


def _make_event(**overrides):
    ev = {
        "topic": "test.event",
        "payload": {"key": "value"},
        "source": "test",
        "priority": "NORMAL",
        "timestamp": time.time(),
        "id": f"evt-{int(time.time() * 1000)}",
    }
    ev.update(overrides)
    return ev


# ── Storage (7) ──────────────────────────────────────────────


def test_db_init_creates_table():
    with tempfile.TemporaryDirectory() as tmpdir:
        store = _make_store(tmpdir)
        tables = [
            r[0]
            for r in store._conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ).fetchall()
        ]
        assert "stored_events" in tables
        store.close()


def test_append_single_event():
    with tempfile.TemporaryDirectory() as tmpdir:
        store = _make_store(tmpdir)
        ev = _make_event(id="evt-001", topic="unit.single", payload={"a": 1})
        seq = store.append(ev)
        assert seq == 1
        results = store.replay()
        assert len(results) == 1
        assert results[0]["topic"] == "unit.single"
        assert results[0]["payload"] == {"a": 1}
        assert results[0]["id"] == "evt-001"
        store.close()


def test_append_multiple_events():
    with tempfile.TemporaryDirectory() as tmpdir:
        store = _make_store(tmpdir)
        seqs = []
        for i in range(5):
            seqs.append(store.append(_make_event(id=f"evt-{i:03d}", topic=f"unit.{i}")))
        assert seqs == sorted(seqs)
        assert store.event_count() == 5
        store.close()


def test_append_persists_across_reopen():
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "reopen.db"
        from runtime.event_store import EventStore

        store1 = EventStore(db_path=db_path)
        store1.append(_make_event(id="evt-persist", topic="unit.persist", payload={"x": 99}))
        store1.close()

        store2 = EventStore(db_path=db_path)
        results = store2.replay()
        assert len(results) == 1
        assert results[0]["id"] == "evt-persist"
        assert results[0]["payload"] == {"x": 99}
        store2.close()


def test_append_ordering():
    with tempfile.TemporaryDirectory() as tmpdir:
        store = _make_store(tmpdir)
        for i in range(10):
            store.append(_make_event(id=f"evt-order-{i}", topic="unit.order"))
        results = store.replay()
        seqs = [r["seq"] for r in results]
        assert seqs == sorted(seqs)
        store.close()


def test_append_immutable_record():
    with tempfile.TemporaryDirectory() as tmpdir:
        store = _make_store(tmpdir)
        assert not hasattr(store, "update")
        assert not hasattr(store, "delete")
        assert not hasattr(store, "modify")
        store.close()


def test_append_duplicate_event_id():
    with tempfile.TemporaryDirectory() as tmpdir:
        store = _make_store(tmpdir)
        store.append(_make_event(id="evt-dup"))
        with pytest.raises(sqlite3.IntegrityError):
            store.append(_make_event(id="evt-dup"))
        assert store.event_count() == 1
        store.close()


# ── Replay (7) ───────────────────────────────────────────────


def test_replay_full():
    with tempfile.TemporaryDirectory() as tmpdir:
        store = _make_store(tmpdir)
        for i in range(5):
            store.append(_make_event(id=f"evt-replay-{i}", topic="unit.replay"))
        results = store.replay()
        assert len(results) == 5
        store.close()


def test_replay_cursor():
    with tempfile.TemporaryDirectory() as tmpdir:
        store = _make_store(tmpdir)
        for i in range(5):
            store.append(_make_event(id=f"evt-cursor-{i}", topic="unit.cursor"))
        results = store.replay(cursor=2)
        assert len(results) == 3
        assert all(r["seq"] > 2 for r in results)
        store.close()


def test_replay_cursor_exact_boundary():
    with tempfile.TemporaryDirectory() as tmpdir:
        store = _make_store(tmpdir)
        for i in range(5):
            store.append(_make_event(id=f"evt-bound-{i}", topic="unit.bound"))
        results = store.replay(cursor=3)
        assert len(results) == 2
        assert results[0]["seq"] == 4
        assert results[1]["seq"] == 5
        store.close()


def test_replay_topic_filter():
    with tempfile.TemporaryDirectory() as tmpdir:
        store = _make_store(tmpdir)
        store.append(_make_event(id="evt-t1", topic="keep.me"))
        store.append(_make_event(id="evt-t2", topic="skip.me"))
        store.append(_make_event(id="evt-t3", topic="keep.me"))
        results = store.replay(topic="keep.me")
        assert len(results) == 2
        assert all(r["topic"] == "keep.me" for r in results)
        store.close()


def test_replay_cursor_and_topic():
    with tempfile.TemporaryDirectory() as tmpdir:
        store = _make_store(tmpdir)
        for i in range(5):
            topic = "keep" if i % 2 == 0 else "skip"
            store.append(_make_event(id=f"evt-ct-{i}", topic=topic))
        results = store.replay(cursor=1, topic="keep")
        assert len(results) == 2
        assert all(r["topic"] == "keep" and r["seq"] > 1 for r in results)
        store.close()


def test_replay_empty_result():
    with tempfile.TemporaryDirectory() as tmpdir:
        store = _make_store(tmpdir)
        results = store.replay()
        assert results == []
        store.close()


def test_replay_past_end():
    with tempfile.TemporaryDirectory() as tmpdir:
        store = _make_store(tmpdir)
        for i in range(3):
            store.append(_make_event(id=f"evt-end-{i}", topic="unit.end"))
        results = store.replay(cursor=999)
        assert results == []
        store.close()


# ── Integration (2) ──────────────────────────────────────────


def test_event_store_receives_from_bus():
    with tempfile.TemporaryDirectory() as tmpdir:
        from event_bus import EventBus

        bus = EventBus()
        store = _make_store(tmpdir)
        bus.subscribe("*", lambda msg: store.append({
            "topic": msg.topic,
            "payload": msg.payload,
            "source": msg.source,
            "priority": msg.priority,
            "timestamp": msg.timestamp,
            "id": msg.id,
        }))
        bus.publish("integration.test", {"ok": True}, source="bus_test")
        bus.publish("integration.other", {"n": 42}, source="bus_test")
        assert store.event_count() == 2
        results = store.replay(topic="integration.test")
        assert len(results) == 1
        assert results[0]["payload"] == {"ok": True}
        store.close()
        bus.clear()


def test_event_store_lifecycle():
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "lifecycle.db"
        from runtime.event_store import EventStore

        store = EventStore(db_path=db_path)
        store.append(_make_event(id="evt-lc-1", topic="lifecycle.a"))
        store.append(_make_event(id="evt-lc-2", topic="lifecycle.b"))
        assert store.event_count() == 2
        store.close()

        store2 = EventStore(db_path=db_path)
        assert store2.event_count() == 2
        results = store2.replay()
        assert len(results) == 2
        store2.close()


# ── Regression (2) ───────────────────────────────────────────


def test_event_store_does_not_break_bus():
    with tempfile.TemporaryDirectory() as tmpdir:
        from event_bus import EventBus

        bus = EventBus()
        received = []
        bus.subscribe("regression.check", lambda msg: received.append(msg))
        bus.publish("regression.check", {"v": 1}, source="reg")
        assert len(received) == 1
        assert received[0].payload["v"] == 1
        bus.clear()


def test_event_store_independent_of_audit_log():
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "isolated.db"
        from runtime.event_store import EventStore

        store = EventStore(db_path=db_path)
        store.append(_make_event(id="evt-iso", topic="isolation.test"))
        rows = store._conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        ).fetchall()
        table_names = [r[0] for r in rows]
        assert "stored_events" in table_names
        store.close()
