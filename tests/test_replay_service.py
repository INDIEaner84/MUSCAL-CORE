import os
import tempfile
import time
from pathlib import Path

import pytest
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


def _make_store(tmpdir: str):
    from runtime.event_store import EventStore

    db_path = Path(tmpdir) / "replay_test.db"
    return EventStore(db_path=db_path)


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


def _make_service(tmpdir: str):
    from event_bus import EventBus
    from features.replay.replay_service import ReplayService

    store = _make_store(tmpdir)
    bus = EventBus()
    service = ReplayService(store=store, bus=bus)
    return service, bus, store


# ── ReplayService Tests (10) ────────────────────────────────


def test_replay_all_publishes_to_bus():
    with tempfile.TemporaryDirectory() as tmpdir:
        service, bus, store = _make_service(tmpdir)
        store.append(_make_event(id="evt-001", topic="replay.basic", payload={"n": 1}))
        store.append(_make_event(id="evt-002", topic="replay.basic", payload={"n": 2}))

        received = []
        bus.subscribe("replay.basic", lambda msg: received.append(msg))

        count = service.replay_all()
        assert count == 2
        assert len(received) == 2
        assert received[0].payload["n"] == 1
        assert received[1].payload["n"] == 2
        store.close()
        bus.clear()


def test_replay_correct_fields():
    with tempfile.TemporaryDirectory() as tmpdir:
        service, bus, store = _make_service(tmpdir)
        store.append(_make_event(
            id="evt-fields", topic="replay.fields",
            payload={"data": "hello"}, source="field_src",
            priority="HIGH", timestamp=1234567890.0,
        ))

        received = []
        bus.subscribe("replay.fields", lambda msg: received.append(msg))

        service.replay_all()
        assert len(received) == 1
        msg = received[0]
        assert msg.topic == "replay.fields"
        assert msg.source == "field_src"
        assert msg.payload["data"] == "hello"
        store.close()
        bus.clear()


def test_replay_original_id_in_payload():
    with tempfile.TemporaryDirectory() as tmpdir:
        service, bus, store = _make_service(tmpdir)
        store.append(_make_event(id="evt-original-42", topic="replay.id"))

        received = []
        bus.subscribe("replay.id", lambda msg: received.append(msg))

        service.replay_all()
        assert len(received) == 1
        assert received[0].payload["_original_event_id"] == "evt-original-42"
        store.close()
        bus.clear()


def test_replay_topic_filter():
    with tempfile.TemporaryDirectory() as tmpdir:
        service, bus, store = _make_service(tmpdir)
        store.append(_make_event(id="evt-t1", topic="keep.me"))
        store.append(_make_event(id="evt-t2", topic="skip.me"))
        store.append(_make_event(id="evt-t3", topic="keep.me"))

        received_keep = []
        received_skip = []
        bus.subscribe("keep.me", lambda msg: received_keep.append(msg))
        bus.subscribe("skip.me", lambda msg: received_skip.append(msg))

        count = service.replay_topic("keep.me")
        assert count == 2
        assert len(received_keep) == 2
        assert len(received_skip) == 0
        store.close()
        bus.clear()


def test_replay_cursor_advancement():
    with tempfile.TemporaryDirectory() as tmpdir:
        service, bus, store = _make_service(tmpdir)
        for i in range(5):
            store.append(_make_event(id=f"evt-c{i}", topic="replay.cursor"))

        assert service.get_cursor() == 0
        count1 = service.replay_all(limit=3)
        assert count1 == 3
        cursor_after_first = service.get_cursor()
        assert cursor_after_first > 0

        count2 = service.replay_all(limit=3)
        assert count2 == 2
        assert service.get_cursor() > cursor_after_first
        store.close()
        bus.clear()


def test_replay_topic_does_not_advance_cursor():
    with tempfile.TemporaryDirectory() as tmpdir:
        service, bus, store = _make_service(tmpdir)
        store.append(_make_event(id="evt-a1", topic="topic.a"))
        store.append(_make_event(id="evt-b1", topic="topic.b"))
        store.append(_make_event(id="evt-a2", topic="topic.a"))

        cursor_before = service.get_cursor()
        service.replay_topic("topic.a")
        cursor_after = service.get_cursor()
        assert cursor_after == cursor_before
        store.close()
        bus.clear()


def test_replay_empty_store():
    with tempfile.TemporaryDirectory() as tmpdir:
        service, bus, store = _make_service(tmpdir)

        received = []
        bus.subscribe("*", lambda msg: received.append(msg))

        count = service.replay_all()
        assert count == 0
        assert len(received) == 0
        assert service.get_cursor() == 0
        store.close()
        bus.clear()


def test_replay_subscribers_triggered():
    with tempfile.TemporaryDirectory() as tmpdir:
        service, bus, store = _make_service(tmpdir)
        store.append(_make_event(id="evt-sub", topic="replay.sub"))

        sub_a = []
        sub_b = []
        bus.subscribe("replay.sub", lambda msg: sub_a.append(msg))
        bus.subscribe("*", lambda msg: sub_b.append(msg))

        service.replay_all()
        assert len(sub_a) == 1
        assert len(sub_b) == 1
        store.close()
        bus.clear()


def test_replay_store_error_propagates():
    with tempfile.TemporaryDirectory() as tmpdir:
        from event_bus import EventBus
        from features.replay.replay_service import ReplayService

        class FailingStore:
            def replay(self, cursor=None, topic=None, limit=100):
                raise ConnectionError("database unavailable")
            def get_cursor(self):
                return 0

        bus = EventBus()
        service = ReplayService(store=FailingStore(), bus=bus)

        with pytest.raises(ConnectionError, match="database unavailable"):
            service.replay_all()
        bus.clear()


def test_replay_returns_same_events_for_same_cursor():
    with tempfile.TemporaryDirectory() as tmpdir:
        service, bus, store = _make_service(tmpdir)
        for i in range(5):
            store.append(_make_event(id=f"evt-idem-{i}", topic="replay.idem"))

        batch1_events = []
        handler1 = lambda msg: batch1_events.append(msg)
        bus.subscribe("replay.idem", handler1)
        service.replay_all(limit=3)
        count1 = len(batch1_events)
        bus.unsubscribe("replay.idem", handler1)
        bus.clear()

        service.reset_cursor()
        batch2_events = []
        handler2 = lambda msg: batch2_events.append(msg)
        bus.subscribe("replay.idem", handler2)
        service.replay_all(limit=3)
        count2 = len(batch2_events)

        assert count1 == count2
        assert [e.payload for e in batch1_events] == [e.payload for e in batch2_events]
        store.close()
        bus.clear()


# ── Replay Suppression (3) ───────────────────────────────────


def test_replay_build_payload_includes_replayed():
    with tempfile.TemporaryDirectory() as tmpdir:
        service, bus, store = _make_service(tmpdir)
        event = {
            "topic": "test.replay.marker",
            "payload": {"data": "hello"},
            "source": "test",
            "id": "evt-marker-42",
        }
        payload = service._build_payload(event)
        assert payload["_replayed"] is True
        assert payload["_original_event_id"] == "evt-marker-42"
        assert payload["data"] == "hello"
        store.close()
        bus.clear()


def test_replay_all_suppresses_duplicates():
    with tempfile.TemporaryDirectory() as tmpdir:
        service, bus, store = _make_service(tmpdir)
        store.append(_make_event(id="evt-s1", topic="suppress.dup", payload={"n": 1}))
        store.append(_make_event(id="evt-s2", topic="suppress.dup", payload={"n": 2}))
        store.append(_make_event(id="evt-s3", topic="suppress.dup", payload={"n": 3}))
        assert store.event_count() == 3

        received = []
        bus.subscribe("suppress.dup", lambda msg: received.append(msg))

        count = service.replay_all()
        assert count == 3
        assert len(received) == 3
        assert received[0].payload["n"] == 1
        assert store.event_count() == 3
        store.close()
        bus.clear()


def test_replay_no_duplicate_growth():
    with tempfile.TemporaryDirectory() as tmpdir:
        service, bus, store = _make_service(tmpdir)
        store.append(_make_event(id="evt-g1", topic="suppress.growth", payload={"v": 10}))
        store.append(_make_event(id="evt-g2", topic="suppress.growth", payload={"v": 20}))
        count_before = store.event_count()

        bus.subscribe("suppress.growth", lambda msg: None)
        service.replay_all()
        assert store.event_count() == count_before

        service.reset_cursor()
        service.replay_all()
        assert store.event_count() == count_before

        service.reset_cursor()
        service.replay_all()
        assert store.event_count() == count_before
        store.close()
        bus.clear()
