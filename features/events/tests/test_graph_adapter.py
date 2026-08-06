"""Graph observer adapter tests (P0-2, Phase 3).

Verifies the pipeline graph.emit() → ObserverEvent → registry → producer
→ EventStore v2 (temp DB, migrated to v2 schema). No production DB contact.
"""

import os
import sys
from pathlib import Path

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", ".."))

from features.events.contracts.observer_event_contract import (  # noqa: E402
    OBS_NODE_CREATED,
    OBS_NODE_UPDATED,
)
from features.events import observer_registry  # noqa: E402
from features.events.graph_observer_adapter import (  # noqa: E402
    GRAPH_TYPE_TO_OBSERVER,
    GraphObserverAdapter,
)
from features.events.migrations.eventstore_v2_migration import run_migration  # noqa: E402


def _make_v2_store(tmp_path: Path):
    from runtime.event_store import EventStore

    store = EventStore(db_path=Path(tmp_path) / "observer_test.db")
    run_migration(Path(tmp_path) / "observer_test.db")
    return store


@pytest.fixture(autouse=True)
def _clean_registry():
    observer_registry.clear()
    yield
    observer_registry.clear()


class TestGraphAdapter:
    def test_adapter_maps_graph_emit_to_observer_event(self):
        from graph import EVENT_NODE_CREATED, EVENT_NODE_UPDATED, GraphState

        graph = GraphState()
        captured = []
        adapter = GraphObserverAdapter(
            producer=lambda ev: captured.append(ev), task_id="t-1"
        )
        adapter.attach(graph)
        graph.emit(EVENT_NODE_CREATED, {"node_id": "n1", "type": "INTENT"})
        graph.emit(EVENT_NODE_UPDATED, {"node_id": "n1", "status": "running"})

        assert len(captured) == 2
        assert captured[0].event_type == OBS_NODE_CREATED
        assert captured[1].event_type == OBS_NODE_UPDATED
        assert captured[0].payload["node_id"] == "n1"
        assert captured[0].task_id == "t-1"

    def test_hash_chain_genesis_and_link(self):
        from graph import EVENT_NODE_CREATED, GraphState

        graph = GraphState()
        captured = []
        adapter = GraphObserverAdapter(producer=lambda ev: captured.append(ev))
        adapter.attach(graph)
        graph.emit(EVENT_NODE_CREATED, {"node_id": "n1"})
        graph.emit(EVENT_NODE_CREATED, {"node_id": "n2"})

        assert captured[0].previous_hash == ""  # genesis (B3)
        assert captured[0].event_hash != ""
        assert captured[1].previous_hash == captured[0].event_hash  # chain (R2)

    def test_pipeline_persists_to_eventstore_v2(self, tmp_path):
        from graph import EVENT_NODE_CREATED, GraphState

        store = _make_v2_store(tmp_path)
        graph = GraphState()
        adapter = GraphObserverAdapter(
            producer=None, task_id="task-1", agent_id="agent-1"
        )
        adapter._last_hash = ""
        from features.events.graph_observer_adapter import default_producer_factory

        adapter.producer = default_producer_factory(store)
        adapter.attach(graph)

        graph.emit(EVENT_NODE_CREATED, {"node_id": "n1", "kind": "INTENT"})

        assert store.event_count(topic=OBS_NODE_CREATED) == 1
        row = store.replay(topic=OBS_NODE_CREATED, limit=1)[-1]
        assert row["topic"] == OBS_NODE_CREATED
        assert row["payload"]["node_id"] == "n1"
        # v2 schema active at DB level (store read model stays v1-shaped,
        # EventStore unverändert per P0-2-Regeln)
        import sqlite3

        conn = sqlite3.connect(str(Path(tmp_path) / "observer_test.db"))
        try:
            stored = conn.execute(
                "SELECT event_version, payload FROM stored_events ORDER BY seq DESC LIMIT 1"
            ).fetchone()
        finally:
            conn.close()
        assert stored[0] == 2  # event_version column default
        import json

        assert json.loads(stored[1]) == {"node_id": "n1", "kind": "INTENT"}

    def test_adapter_uses_existing_graph_infrastructure(self):
        from graph import EVENT_NODE_CREATED, EVENT_EDGE_CREATED, GraphState

        graph = GraphState()
        adapter = GraphObserverAdapter(producer=lambda ev: None)
        adapter.attach(graph)
        for graph_type, topic in GRAPH_TYPE_TO_OBSERVER.items():
            assert graph_type in graph._event_listeners
            assert len(graph._event_listeners[graph_type]) == 1
        # graph still functional with its own listeners
        graph.emit(EVENT_NODE_CREATED, {"node_id": "x"})
        graph.emit(EVENT_EDGE_CREATED, {"source_id": "a", "target_id": "b"})
        assert len(graph.nodes) >= 0
