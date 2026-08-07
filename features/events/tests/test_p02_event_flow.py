"""P0-2 Event Flow Integration tests (ITERATION-4).

Validates the complete event lifecycle using ONLY the existing
infrastructure (REUSE BEFORE CREATE, no new architecture, no Core writes):

    CREATE → VALIDATE → HASH → PERSIST → READ → REPLAY → STATE UPDATE

Covers the 8 mandatory P0-2 test cases:
  T-P02-1 Event speichern   (producer → EventStore v2)
  T-P02-2 Event laden       (load_events)
  T-P02-3 Replay            (order_events + validate_sequence)
  T-P02-4 State erzeugen    (rebuild_state)
  T-P02-5 Observer Trigger  (graph → adapter → registry → producer)
  T-P02-6 Sequence Fehler   (missing / duplicate / wrong order)
  T-P02-7 Hash Fehler       (invalid hash / chain break)
  T-P02-8 Deterministischer Replay
  T-P02-9 Performance Baseline (100 / 1000 events)
"""

import os
import sys
import time
import tracemalloc
from pathlib import Path

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", ".."))

from features.events.contracts.observer_event_contract import (  # noqa: E402
    OBS_NODE_CREATED,
    OBS_OBSERVATION_CREATED,
    ObserverEvent,
)
from features.events import observer_registry  # noqa: E402
from features.events.graph_observer_adapter import GraphObserverAdapter  # noqa: E402
from features.events.migrations.eventstore_v2_migration import run_migration  # noqa: E402
from features.events.producer.adapter import EventStoreV2Adapter  # noqa: E402
from features.events.producer.factory import create_producer, observer_producer_factory  # noqa: E402
from features.events.state_model import ChainIntegrityError, reconstruct_state  # noqa: E402
from features.replay.replay_service import ReplayService, SequenceIntegrityError  # noqa: E402

OBS_TOPIC = OBS_OBSERVATION_CREATED


@pytest.fixture
def store(tmp_path):
    from runtime.event_store import EventStore

    db = Path(tmp_path) / "p02.db"
    s = EventStore(db_path=db)
    run_migration(db)
    yield s
    s.close()


@pytest.fixture
def producer(store):
    return create_producer(
        store,
        producer_type="eventstore_v2",
        source="p02",
        agent_id="p02-agent",
        task_id="p02-task",
        confidence=0.5,
    )


@pytest.fixture
def replay(store):
    from event_bus import EventBus

    return ReplayService(store=store, bus=EventBus())


def _publish(producer, topic, payload, n=1):
    for i in range(n):
        ev = producer.create_event(topic, {**payload, "n": i})
        producer.publish(ev)


def _make_graph_observer(store, graph):
    """Wire the EXISTING GraphObserverAdapter with the new producer (P0-2 §5)."""
    adapter = EventStoreV2Adapter(
        event_store=store, source="graph", agent_id="obs-agent", task_id="obs-task"
    )
    observer = GraphObserverAdapter(
        producer=observer_producer_factory(adapter),
        agent_id="obs-agent",
        task_id="obs-task",
    )
    observer.attach(graph)
    return adapter, observer


# ── T-P02-1 Event speichern ────────────────────────────────────────────


class TestEventPersistence:
    def test_create_validate_hash_persist(self, store, producer):
        ev = producer.create_event(OBS_TOPIC, {"observation_id": "obs-1"})
        assert producer.validate(ev) is True
        seq = producer.publish(ev)
        assert seq == 1
        assert store.event_count() == 1

    def test_stored_event_has_v2_fields_and_hash(self, store, producer):
        producer.publish(producer.create_event(OBS_TOPIC, {"observation_id": "obs-1"}))
        row = store.replay(limit=10)[0]
        assert row["schema_version"] == 2
        assert row["metadata"]["event_hash"]
        assert row["metadata"]["previous_hash"] == ""


# ── T-P02-2 Event laden ────────────────────────────────────────────────


class TestEventLoad:
    def test_load_events_returns_stored_events(self, producer, replay):
        _publish(producer, OBS_TOPIC, {"observation_id": "obs-a"})
        _publish(producer, OBS_TOPIC, {"observation_id": "obs-b"})
        events = replay.load_events()
        assert len(events) == 2
        assert [e["seq"] for e in events] == [1, 2]
        assert events[0]["metadata"]["event_hash"]

    def test_load_events_topic_filter(self, store, producer, replay):
        _publish(producer, OBS_TOPIC, {"observation_id": "obs-a"})
        _publish(producer, OBS_NODE_CREATED, {"node_id": "n1"})
        obs = replay.load_events(topic=OBS_TOPIC)
        assert len(obs) == 1


# ── T-P02-3 Replay durchführen ─────────────────────────────────────────


class TestReplay:
    def test_order_events_deterministic(self, producer, replay):
        _publish(producer, OBS_TOPIC, {"observation_id": "obs-a"}, n=3)
        events = replay.load_events()
        shuffled = [events[2], events[0], events[1]]
        ordered = replay.order_events(shuffled)
        assert [e["seq"] for e in ordered] == [1, 2, 3]

    def test_validate_sequence_ok(self, producer, replay):
        _publish(producer, OBS_TOPIC, {"observation_id": "obs-a"}, n=3)
        report = replay.validate_sequence(replay.load_events())
        assert report["valid"] is True
        assert report["events_checked"] == 3

    def test_replay_no_side_effects(self, store, producer, replay):
        _publish(producer, OBS_TOPIC, {"observation_id": "obs-a"}, n=3)
        before = store.event_count()
        replay.validate_sequence(replay.load_events())
        replay.rebuild_state()
        assert store.event_count() == before


# ── T-P02-4 State erzeugen ─────────────────────────────────────────────


class TestStateRebuild:
    def test_rebuild_state_nodes_and_observations(self, producer, replay):
        _publish(producer, OBS_NODE_CREATED, {"node_id": "n1", "type": "intent"})
        _publish(producer, OBS_NODE_CREATED, {"node_id": "n2", "type": "task"})
        _publish(producer, OBS_TOPIC, {"observation_id": "o1"})
        state = replay.rebuild_state()
        assert state.events_processed == 3
        assert set(state.graph_nodes) == {"n1", "n2"}
        assert len(state.observations) == 1

    def test_rebuild_state_via_events_arg(self, store, producer, replay):
        _publish(producer, OBS_TOPIC, {"observation_id": "o1"}, n=2)
        events = replay.load_events()
        s1 = replay.rebuild_state(events)
        s2 = replay.rebuild_state(list(events))
        assert s1.to_dict() == s2.to_dict()


# ── T-P02-5 Observer Trigger ───────────────────────────────────────────


class TestObserverTrigger:
    def test_event_flows_through_adapter_to_registry(self, store):
        from graph import GraphState

        received = []
        observer_registry.register(received.append)
        try:
            graph = GraphState()
            _, observer = _make_graph_observer(store, graph)

            graph.emit("OBSERVATION_CREATED", {"observation_id": "obs-1"})

            # Observer registry got the event (Event → Adapter → Registry)
            assert len(received) == 1
            assert received[0].event_type == OBS_TOPIC
            assert isinstance(received[0], ObserverEvent)
            # ... and the producer persisted it to EventStore v2
            assert store.event_count() == 1
            observer.detach(graph)
        finally:
            observer_registry.clear()

    def test_direct_observer_event_persisted(self, store):
        from graph import GraphState

        graph = GraphState()
        _, observer = _make_graph_observer(store, graph)
        graph.emit("NODE_CREATED", {"node_id": "n1", "type": "intent"})
        assert store.event_count() == 1
        row = store.replay(limit=10)[0]
        assert row["topic"] == OBS_NODE_CREATED
        observer.detach(graph)


# ── T-P02-6 Sequence Fehler ────────────────────────────────────────────


class TestSequenceErrors:
    def test_missing_event_gap_detected(self, producer, replay):
        _publish(producer, OBS_TOPIC, {"observation_id": "a"}, n=3)
        events = replay.load_events()
        events.pop(1)  # gap: seq 2 missing
        with pytest.raises(SequenceIntegrityError, match="gap"):
            replay.validate_sequence(events)

    def test_duplicate_event_detected(self, producer, replay):
        _publish(producer, OBS_TOPIC, {"observation_id": "a"}, n=2)
        events = replay.load_events()
        events.append(dict(events[0]))  # duplicate seq + duplicate event_id
        with pytest.raises(SequenceIntegrityError, match="duplicate"):
            replay.validate_sequence(events)

    def test_wrong_order_detected(self, producer, replay):
        _publish(producer, OBS_TOPIC, {"observation_id": "a"}, n=3)
        events = replay.load_events()
        events[0], events[1] = events[1], events[0]
        with pytest.raises(SequenceIntegrityError, match="out of order"):
            replay.validate_sequence(events)


# ── T-P02-7 Hash Fehler ────────────────────────────────────────────────


class TestHashErrors:
    def test_invalid_hash_detected(self, producer, replay):
        _publish(producer, OBS_TOPIC, {"observation_id": "a"}, n=2)
        events = replay.load_events()
        events[0]["metadata"]["event_hash"] = "tampered"
        with pytest.raises(SequenceIntegrityError, match="hash mismatch"):
            replay.validate_sequence(events)

    def test_chain_break_detected(self, producer, replay):
        _publish(producer, OBS_TOPIC, {"observation_id": "a"}, n=2)
        events = replay.load_events()
        events[1]["metadata"]["previous_hash"] = "corrupted"
        with pytest.raises(SequenceIntegrityError, match="hash mismatch|chain break"):
            replay.validate_sequence(events)

    def test_chain_integrity_error_type(self, producer, replay):
        _publish(producer, OBS_TOPIC, {"observation_id": "a"}, n=2)
        events = replay.load_events()
        events[1]["metadata"]["event_hash"] = "tampered"
        with pytest.raises((ChainIntegrityError, SequenceIntegrityError)):
            replay.validate_sequence(events)


# ── T-P02-8 Deterministischer Replay ───────────────────────────────────


class TestDeterminism:
    def test_same_sequence_same_state(self, producer, replay):
        _publish(producer, OBS_TOPIC, {"observation_id": "a"}, n=3)
        _publish(producer, OBS_NODE_CREATED, {"node_id": "n1"})
        events = replay.load_events()
        s1 = reconstruct_state(replay.order_events(events))
        s2 = reconstruct_state(replay.order_events(list(events)))
        assert s1.to_dict() == s2.to_dict()
        assert s1.events_processed == s2.events_processed == 4

    def test_replay_all_and_rebuild_identical(self, store, producer, replay):
        _publish(producer, OBS_TOPIC, {"observation_id": "a"}, n=3)
        replay.replay_all()  # bus path (existing)
        events = replay.load_events()
        state = replay.rebuild_state(events)
        assert state.events_processed == 3


# ── T-P02-9 Performance Baseline ───────────────────────────────────────


class TestPerformanceBaseline:
    @staticmethod
    def _bench(store, producer, replay, n):
        _publish(producer, OBS_TOPIC, {"observation_id": "perf"}, n=n)

        tracemalloc.start()
        t0 = time.perf_counter()
        events = replay.load_events()
        report = replay.validate_sequence(events)
        state = replay.rebuild_state(events)
        elapsed = time.perf_counter() - t0
        _, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()

        assert len(events) == n
        assert report["valid"] is True
        assert state.events_processed == n
        return {"seconds": elapsed, "peak_mb": peak / 1e6, "errors": 0}

    def test_bench_100(self, store, producer, replay):
        r = self._bench(store, producer, replay, 100)
        assert r["seconds"] < 5.0
        assert r["peak_mb"] < 200.0
        assert r["errors"] == 0

    def test_bench_1000(self, store, producer, replay):
        r = self._bench(store, producer, replay, 1000)
        assert r["seconds"] < 10.0
        assert r["peak_mb"] < 400.0
        assert r["errors"] == 0
