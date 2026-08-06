"""State reconstruction tests (P0-3).

Covers: empty store, single event, multiple events, hash-chain validation,
determinism (same events ⇒ same state).
"""

import json
import os
import sys
from pathlib import Path

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", ".."))

from features.events.contracts.observer_event_contract import (  # noqa: E402
    OBS_OBSERVATION_CREATED,
)
from features.events.event_hash import calculate_event_hash  # noqa: E402
from features.events.graph_observer_adapter import (  # noqa: E402
    GraphObserverAdapter,
    default_producer_factory,
)
from features.events.migrations.eventstore_v2_migration import run_migration  # noqa: E402
from features.events.state_model import (  # noqa: E402
    ChainIntegrityError,
    reconstruct_from_store,
    reconstruct_state,
    validate_chain,
)


@pytest.fixture
def store(tmp_path):
    from runtime.event_store import EventStore

    db = Path(tmp_path) / "rec.db"
    s = EventStore(db_path=db)
    run_migration(db)
    return s


def _produce(store, graph, n: int):
    adapter = GraphObserverAdapter(
        producer=default_producer_factory(store),
        agent_id="test-agent",
        task_id="rec",
    )
    adapter.attach(graph)
    for i in range(n):
        graph.emit("OBSERVATION_CREATED", {"observation_id": f"obs-{i}", "value": i})


class TestReconstruction:
    def test_empty_store(self, store):
        state = reconstruct_from_store(store)
        assert state.events_processed == 0
        assert state.summary() == {
            "entities": 0,
            "graph_nodes": 0,
            "graph_edges": 0,
            "active_tasks": 0,
            "agents": 0,
            "observations": 0,
        }
        assert validate_chain([])["valid"] is True

    def test_single_event(self, store):
        from graph import GraphState

        _produce(store, GraphState(), 1)
        evs = store.replay(topic=OBS_OBSERVATION_CREATED, limit=100)
        state = reconstruct_state(evs)
        assert state.events_processed == 1
        assert len(state.observations) == 1
        assert state.observations[0]["observation_id"] == "obs-0"
        assert state.summary()["agents"] == 1

    def test_multiple_events(self, store):
        from graph import GraphState

        _produce(store, GraphState(), 5)
        state = reconstruct_from_store(store)
        assert state.events_processed == 5
        assert len(state.observations) == 5
        assert [o["observation_id"] for o in state.observations] == [
            f"obs-{i}" for i in range(5)
        ]

    def test_hash_chain_validation(self, store):
        from graph import GraphState

        _produce(store, GraphState(), 3)
        evs = store.replay(topic=OBS_OBSERVATION_CREATED, limit=100)
        report = validate_chain(evs)
        assert report["valid"] is True
        assert report["events_checked"] == 3
        # recompute last hash from stored metadata content
        last = evs[-1]
        md = last["metadata"]
        recomputed = calculate_event_hash(
            {
                "event_type": last["topic"],
                "source": last["source"],
                "payload": last["payload"],
                "agent_id": md["agent_id"],
                "task_id": md["task_id"],
                "confidence": float(md["confidence"]),
                "previous_hash": md["previous_hash"],
            }
        )
        assert recomputed == md["event_hash"]

    def test_chain_break_detected(self, store):
        from graph import GraphState

        _produce(store, GraphState(), 2)
        evs = store.replay(topic=OBS_OBSERVATION_CREATED, limit=100)
        evs[1]["metadata"]["previous_hash"] = "corrupted"
        with pytest.raises(ChainIntegrityError):
            validate_chain(evs)

    def test_determinism_same_events_same_state(self, store):
        from graph import GraphState

        _produce(store, GraphState(), 4)
        evs = store.replay(topic=OBS_OBSERVATION_CREATED, limit=100)
        a = reconstruct_state(evs)
        b = reconstruct_state(list(evs))  # same events, replayed again
        assert a.to_dict() == b.to_dict()

    def test_determinism_across_store_replay(self, store):
        from graph import GraphState

        _produce(store, GraphState(), 3)
        s1 = reconstruct_from_store(store)
        s2 = reconstruct_from_store(store)  # second replay pass
        assert s1.to_dict() == s2.to_dict()