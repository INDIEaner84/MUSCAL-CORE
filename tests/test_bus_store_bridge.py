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

    db_path = Path(tmpdir) / "bridge_test.db"
    return EventStore(db_path=db_path)


def _make_bus_and_store(tmpdir: str):
    from event_bus import EventBus
    from runtime.event_store import EventStore

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
    return bus, store


# ── Bridge Tests (7) ─────────────────────────────────────────


def test_bridge_persists_event():
    with tempfile.TemporaryDirectory() as tmpdir:
        bus, store = _make_bus_and_store(tmpdir)
        bus.publish("bridge.test", {"ok": True}, source="bridge_test")
        assert store.event_count() == 1
        results = store.replay(topic="bridge.test")
        assert len(results) == 1
        assert results[0]["payload"] == {"ok": True}
        store.close()
        bus.clear()


def test_bridge_correct_fields():
    with tempfile.TemporaryDirectory() as tmpdir:
        bus, store = _make_bus_and_store(tmpdir)
        ts = time.time()
        bus.publish(
            "bridge.fields",
            {"data": "hello"},
            source="field_test",
            priority="HIGH",
        )
        results = store.replay(topic="bridge.fields")
        assert len(results) == 1
        r = results[0]
        assert r["topic"] == "bridge.fields"
        assert r["payload"] == {"data": "hello"}
        assert r["source"] == "field_test"
        assert r["priority"] in ("HIGH", "2")
        assert isinstance(r["timestamp"], float)
        assert r["id"] != ""
        assert r["id"].startswith("bridge.fields")
        store.close()
        bus.clear()


def test_bridge_multiple_events_stable_order():
    with tempfile.TemporaryDirectory() as tmpdir:
        bus, store = _make_bus_and_store(tmpdir)
        for i in range(10):
            bus.publish(f"bridge.order.{i}", {"seq": i}, source="order_test")
        assert store.event_count() == 10
        results = store.replay()
        seqs = [r["seq"] for r in results]
        assert seqs == sorted(seqs)
        for i, r in enumerate(results):
            assert r["payload"]["seq"] == i
        store.close()
        bus.clear()


def test_bridge_eventstore_survives_restart():
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "restart.db"
        from event_bus import EventBus
        from runtime.event_store import EventStore

        bus1 = EventBus()
        store1 = EventStore(db_path=db_path)
        bus1.subscribe("*", lambda msg: store1.append({
            "topic": msg.topic,
            "payload": msg.payload,
            "source": msg.source,
            "priority": msg.priority,
            "timestamp": msg.timestamp,
            "id": msg.id,
        }))
        bus1.publish("bridge.restart", {"persist": True}, source="restart_test")
        bus1.publish("bridge.restart.2", {"persist": True}, source="restart_test")
        assert store1.event_count() == 2
        store1.close()
        bus1.clear()

        store2 = EventStore(db_path=db_path)
        assert store2.event_count() == 2
        results = store2.replay()
        assert len(results) == 2
        assert results[0]["topic"] == "bridge.restart"
        assert results[1]["topic"] == "bridge.restart.2"
        store2.close()


def test_bridge_store_error_isolates_bus():
    with tempfile.TemporaryDirectory() as tmpdir:
        from event_bus import EventBus
        from runtime.event_store import EventStore

        bus = EventBus()
        store = _make_store(tmpdir)
        error_count = [0]

        def failing_append(msg):
            error_count[0] += 1
            raise sqlite3.OperationalError("simulated failure")

        bus.subscribe("*", failing_append)

        received = []
        bus.subscribe("bridge.isolation", lambda msg: received.append(msg))
        bus.publish("bridge.isolation", {"v": 1}, source="isolation_test")
        bus.publish("bridge.isolation", {"v": 2}, source="isolation_test")

        assert len(received) == 2
        assert received[0].payload["v"] == 1
        assert received[1].payload["v"] == 2
        assert error_count[0] == 2
        assert store.event_count() == 0
        store.close()
        bus.clear()


def test_bridge_does_not_write_audit_log():
    with tempfile.TemporaryDirectory() as tmpdir:
        from runtime.event_store import EventStore

        db_path = Path(tmpdir) / "audit_check.db"
        store = EventStore(db_path=db_path)
        store.append({
            "topic": "bridge.audit",
            "payload": {"check": True},
            "source": "audit_test",
            "priority": "NORMAL",
            "timestamp": time.time(),
            "id": "evt-audit-001",
        })
        tables = [
            r[0]
            for r in store._conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ).fetchall()
        ]
        assert "stored_events" in tables
        assert "audit_log" not in tables
        store.close()


def test_bus_works_independently():
    with tempfile.TemporaryDirectory() as tmpdir:
        from event_bus import EventBus

        bus = EventBus()
        received = []
        bus.subscribe("independent.check", lambda msg: received.append(msg))
        bus.publish("independent.check", {"v": 1}, source="independent_test")
        bus.publish("independent.check", {"v": 2}, source="independent_test")
        bus.publish("other.topic", {"v": 3}, source="independent_test")

        assert len(received) == 2
        assert received[0].payload["v"] == 1
        assert received[1].payload["v"] == 2
        bus.clear()
