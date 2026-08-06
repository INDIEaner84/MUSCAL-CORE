"""End-to-end event chain tests (P0-2/P0-3 Integration).

Verifies the FIRST COMPLETE chain:

    graph.emit(OBSERVATION_CREATED)
        → observer (graph.on, existing infra)
        → ObserverEvent (contract, hashes)
        → producer (ConsolidatedEventWriter, existing pipeline)
        → EventStore v2 (temp DB, migrated)

Checks: Event Creation, Persistence, Replay Read, Hash Validation.
No Core changes; production DB untouched.
"""

import json
import os
import sqlite3
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


@pytest.fixture
def chain_env(tmp_path):
    from runtime.event_store import EventStore

    from graph import GraphState

    db = Path(tmp_path) / "chain.db"
    store = EventStore(db_path=db)
    run_migration(db)
    graph = GraphState()
    adapter = GraphObserverAdapter(
        producer=default_producer_factory(store),
        agent_id="test-agent",
        task_id="e2e",
    )
    adapter.attach(graph)
    return graph, store, adapter


class TestEventChain:
    def test_event_creation_via_graph_emit(self, chain_env):
        graph, store, adapter = chain_env
        graph.emit("OBSERVATION_CREATED", {"observation_id": "obs-0", "value": 42})
        evs = store.replay(topic=OBS_OBSERVATION_CREATED, limit=10)
        assert len(evs) == 1
        assert evs[0]["topic"] == OBS_OBSERVATION_CREATED
        assert evs[0]["payload"]["observation_id"] == "obs-0"

    def test_event_persistence_v2_columns(self, chain_env, tmp_path):
        graph, store, adapter = chain_env
        graph.emit("OBSERVATION_CREATED", {"observation_id": "obs-1"})
        conn = sqlite3.connect(str(Path(tmp_path) / "chain.db"))
        try:
            row = conn.execute(
                "SELECT schema_version, event_version, metadata FROM stored_events"
            ).fetchone()
        finally:
            conn.close()
        assert row is not None
        assert row[0] == 2  # schema_version = 2 (v2 row)
        assert row[1] == 2  # event_version column (default 2)
        metadata = json.loads(row[2])
        assert "event_hash" in metadata
        assert "previous_hash" in metadata

    def test_replay_reads_event(self, chain_env):
        graph, store, adapter = chain_env
        graph.emit("OBSERVATION_CREATED", {"observation_id": "obs-2"})
        evs = store.replay(topic=OBS_OBSERVATION_CREATED, limit=10)
        assert len(evs) == 1
        assert evs[0]["metadata"]["event_hash"] != ""
        assert evs[0]["prev_hash"] == ""  # genesis

    def test_hash_validation_roundtrip(self, chain_env):
        graph, store, adapter = chain_env
        graph.emit("OBSERVATION_CREATED", {"observation_id": "obs-3", "value": 7})
        evs = store.replay(topic=OBS_OBSERVATION_CREATED, limit=10)
        e = evs[0]
        md = e["metadata"]
        recomputed = calculate_event_hash(
            {
                "event_type": e["topic"],
                "source": e["source"],
                "payload": e["payload"],
                "agent_id": "test-agent",
                "task_id": "e2e",
                "confidence": 0.0,
                "previous_hash": md["previous_hash"],
            }
        )
        assert recomputed == md["event_hash"]
        # also verifiable from the replay prev_hash column
        assert e["prev_hash"] == md["previous_hash"]

    def test_hash_chain_links(self, chain_env):
        graph, store, adapter = chain_env
        for i in range(3):
            graph.emit("OBSERVATION_CREATED", {"observation_id": f"obs-{i}"})
        evs = store.replay(topic=OBS_OBSERVATION_CREATED, limit=10)
        assert len(evs) == 3
        # genesis
        assert evs[0]["metadata"]["previous_hash"] == ""
        # chain links
        assert evs[1]["metadata"]["previous_hash"] == evs[0]["metadata"]["event_hash"]
        assert evs[2]["metadata"]["previous_hash"] == evs[1]["metadata"]["event_hash"]
        # prev_hash column mirrors the chain
        assert evs[1]["prev_hash"] == evs[0]["metadata"]["event_hash"]
        assert evs[2]["prev_hash"] == evs[1]["metadata"]["event_hash"]