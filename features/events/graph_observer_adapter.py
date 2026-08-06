"""Graph observer adapter (P0-2, Phase 3).

Bridges the existing GraphState event infrastructure to the Observer Event
Contract and — via the existing writer pipeline (ConsolidatedEventWriter) —
to the EventStore v2.

Mapping:

    graph.emit() / graph._push_event()
        → graph.on() listener (existing infrastructure, NO graph.py rewrite)
        → ObserverEvent (contract)
        → observer_registry.emit()
        → producer (default: ConsolidatedEventWriter → EventStore v2)

Hash chain (H2 contract R1/R2, B3/B6): the adapter tracks the previous
``event_hash``; the first event in a session is the genesis event
(previous_hash = "").
"""

from __future__ import annotations

import logging
import uuid
from typing import Any, Callable, Dict, Optional

from .contracts.observer_event_contract import (
    OBS_EDGE_CREATED,
    OBS_EDGE_REMOVED,
    OBS_EXECUTION_FINISHED,
    OBS_EXECUTION_STARTED,
    OBS_FOCUS_CHANGED,
    OBS_GRAPH_PRUNED,
    OBS_NODE_CREATED,
    OBS_NODE_REMOVED,
    OBS_NODE_UPDATED,
    OBS_OBSERVATION_CREATED,
    OBS_REBUILD_COMPLETED,
    OBS_SNAPSHOT_CREATED,
    OBS_STATE_RESTORED,
    ObserverEvent,
)
from .event_hash import calculate_event_hash
from . import observer_registry

log = logging.getLogger(__name__)

ADAPTER_VERSION = "1.0.0"

# graph.py event type strings (schema.py EVENT_* constants) → observer topics
GRAPH_TYPE_TO_OBSERVER: Dict[str, str] = {
    "NODE_CREATED": OBS_NODE_CREATED,          # E1
    "NODE_UPDATED": OBS_NODE_UPDATED,          # E2
    "NODE_REMOVED": OBS_NODE_REMOVED,          # E3 (future)
    "EDGE_CREATED": OBS_EDGE_CREATED,          # E4
    "EDGE_REMOVED": OBS_EDGE_REMOVED,          # E5 (future)
    "GRAPH_PRUNED": OBS_GRAPH_PRUNED,          # E6 (future)
    "FOCUS_CHANGED": OBS_FOCUS_CHANGED,        # E7 (future)
    "STATE_RESTORED": OBS_STATE_RESTORED,      # E8 (future)
    "SNAPSHOT_CREATED": OBS_SNAPSHOT_CREATED,  # E9 (future)
    "REBUILD_COMPLETED": OBS_REBUILD_COMPLETED,  # E10 (future)
    "EXECUTION_STARTED": OBS_EXECUTION_STARTED,
    "EXECUTION_FINISHED": OBS_EXECUTION_FINISHED,
    "OBSERVATION_CREATED": OBS_OBSERVATION_CREATED,  # P0-2/3 Integration
}


def default_producer_factory(event_store) -> Callable[[ObserverEvent], Optional[int]]:
    """Producer using the existing writer pipeline (ConsolidatedEventWriter)."""
    from .event_consolidation import ConsolidatedEventWriter

    writer = ConsolidatedEventWriter(event_store=event_store)

    def _produce(event: ObserverEvent) -> Optional[int]:
        # Chain + hash-content fields travel through existing store fields
        # (EventStore module unverändert): metadata carries the canonical hash
        # content so stored events are self-verifiable (P0-3 reconstruction).
        metadata = {
            "event_hash": event.event_hash,
            "previous_hash": event.previous_hash,
            "agent_id": event.agent_id,
            "task_id": event.task_id,
            "confidence": event.confidence,
        }
        return writer.write_event(
            topic=event.event_type,
            payload=event.payload,
            source=event.source,
            event_id=str(uuid.uuid4()),
            execution_id=event.task_id or "",
            execution_state="observed",
            metadata=metadata,
            prev_hash=event.previous_hash,
            schema_version=2,
            agent_id=event.agent_id,
            task_id=event.task_id,
            confidence=event.confidence,
            event_version=2,
        )

    return _produce


class GraphObserverAdapter:
    """Attaches observer listeners to a GraphState instance (no rewrite)."""

    def __init__(
        self,
        producer: Optional[Callable[[ObserverEvent], Any]] = None,
        registry=observer_registry,
        agent_id: str = "graph_observer",
        task_id: str = "",
    ):
        self.producer = producer
        self.registry = registry
        self.agent_id = agent_id
        self.task_id = task_id
        self._attached_graphs: list = []
        self._last_hash: str = ""

    def attach(self, graph) -> None:
        """Register listeners on the graph's existing event infrastructure."""
        for graph_type in GRAPH_TYPE_TO_OBSERVER:
            graph.on(graph_type, self._on_graph_event)
        self._attached_graphs.append(graph)

    def detach(self, graph) -> None:
        for graph_type in GRAPH_TYPE_TO_OBSERVER:
            graph.reset_event_listeners(graph_type)
        if graph in self._attached_graphs:
            self._attached_graphs.remove(graph)

    def _on_graph_event(self, entry: Dict[str, Any]) -> None:
        graph_type = entry.get("type", "")
        topic = GRAPH_TYPE_TO_OBSERVER.get(graph_type)
        if topic is None:
            log.debug("graph event type not mapped: %s", graph_type)
            return

        payload = dict(entry.get("payload") or {})
        event = ObserverEvent(
            event_type=topic,
            payload=payload,
            source=payload.get("source", "graph"),
            timestamp=float(entry.get("timestamp", 0.0)) or payload.get("ts", 0.0),
            agent_id=payload.get("agent_id", self.agent_id),
            task_id=payload.get("task_id", self.task_id),
            confidence=float(payload.get("confidence", 0.0)),
            previous_hash=self._last_hash,  # genesis: "" (H2 contract R1/B3)
        )
        event.event_hash = calculate_event_hash(event)

        self.registry.emit(event)

        if self.producer is not None:
            try:
                self.producer(event)
            except Exception:
                log.exception("producer failed for %s", event.event_type)
                return
        self._last_hash = event.event_hash

    def reset_chain(self) -> None:
        """Reset the hash chain (new genesis)."""
        self._last_hash = ""
