"""State reconstruction (P0-3).

Event Sourcing fold over the EventStore v2 replay stream:

    events (seq-asc, from EventStore.replay)
        → per-event state update
        → ReconstructedState (final state)

Features:
* deterministic: same events (same order) ⇒ same final state
* chain validation: previous_hash/event_hash verified per event (H2 contract)
* payload-driven updates for graph.* topics (E1-E10) and OBSERVATION_CREATED

No Core changes; works purely on stored data (self-verifiable metadata).
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from .event_hash import calculate_event_hash

log = logging.getLogger(__name__)

RECONSTRUCTION_VERSION = "1.0.0"

# graph.* topics that feed the reconstructed graph nodes/edges
NODE_CREATE_TOPICS = ("graph.node_created", "graph.state_restored")
NODE_UPDATE_TOPICS = ("graph.node_updated",)
EDGE_CREATE_TOPICS = ("graph.edge_created",)
EDGE_REMOVE_TOPICS = ("graph.edge_removed", "graph.pruned")
OBSERVATION_TOPICS = ("graph.observation_created",)


@dataclass
class ReconstructedState:
    """Deterministic runtime state rebuilt from the event stream."""

    entities: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    graph_nodes: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    graph_edges: List[Dict[str, Any]] = field(default_factory=list)
    active_tasks: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    agents: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    observations: List[Dict[str, Any]] = field(default_factory=list)

    # chain bookkeeping (validation trail)
    events_processed: int = 0
    last_event_hash: str = ""

    def apply(self, event: Dict[str, Any]) -> None:
        """Fold one stored event into the state (deterministic update)."""
        topic = event.get("topic", "")
        payload = dict(event.get("payload") or {})
        seq = event.get("seq", 0)

        node_id = payload.get("node_id") or payload.get("id") or str(seq)
        agent_id = payload.get("agent_id") or event.get("source", "system")

        if topic in NODE_CREATE_TOPICS:
            self.graph_nodes[node_id] = dict(payload)
            self.entities[f"node:{node_id}"] = dict(payload)
        elif topic in NODE_UPDATE_TOPICS:
            node = self.graph_nodes.setdefault(node_id, {})
            node.update(payload)
            self.entities.setdefault(f"node:{node_id}", {}).update(payload)
        elif topic in EDGE_CREATE_TOPICS:
            self.graph_edges.append(
                {
                    "source_id": payload.get("source_id"),
                    "target_id": payload.get("target_id"),
                    "payload": payload,
                }
            )
        elif topic in EDGE_REMOVE_TOPICS:
            self.graph_edges = [
                e
                for e in self.graph_edges
                if not (
                    payload.get("source_id")
                    and payload.get("target_id")
                    and e["source_id"] == payload["source_id"]
                    and e["target_id"] == payload["target_id"]
                )
            ]
        elif topic in OBSERVATION_TOPICS:
            self.observations.append(dict(payload))
            self.entities[f"observation:{node_id}"] = dict(payload)
        elif topic.endswith("execution_started"):
            task_id = payload.get("task_id") or event.get("execution_id") or str(seq)
            self.active_tasks[task_id] = {"status": "running", **payload}
        elif topic.endswith("execution_finished"):
            task_id = payload.get("task_id") or event.get("execution_id") or str(seq)
            task = self.active_tasks.get(task_id, {})
            task.update({"status": "finished", **payload})
            self.active_tasks[task_id] = task
        else:
            # generic entity slot (future topics)
            self.entities.setdefault(topic, []).append(dict(payload))

        self.agents.setdefault(agent_id, {"agent_id": agent_id, "event_count": 0})
        self.agents[agent_id]["event_count"] += 1

        self.events_processed += 1
        self.last_event_hash = _metadata_of(event).get("event_hash", "")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "entities": self.entities,
            "graph_nodes": self.graph_nodes,
            "graph_edges": self.graph_edges,
            "active_tasks": self.active_tasks,
            "agents": self.agents,
            "observations": self.observations,
            "events_processed": self.events_processed,
        }

    def summary(self) -> Dict[str, int]:
        """Compact counts (demo output)."""
        return {
            "entities": len(self.entities),
            "graph_nodes": len(self.graph_nodes),
            "graph_edges": len(self.graph_edges),
            "active_tasks": len(self.active_tasks),
            "agents": len(self.agents),
            "observations": len(self.observations),
        }


def _metadata_of(event: Dict[str, Any]) -> Dict[str, Any]:
    md = event.get("metadata") or {}
    return md if isinstance(md, dict) else {}


def validate_chain(events: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Verify hash chain integrity across the event list (H2 contract).

    Returns report dict; raises ChainIntegrityError on violation.
    """
    for index, event in enumerate(events):
        md = _metadata_of(event)
        stored_hash = md.get("event_hash", "")
        stored_prev = md.get("previous_hash", "")

        content = {
            "event_type": event.get("topic", ""),
            "source": event.get("source", "system"),
            "payload": event.get("payload", {}),
            "agent_id": md.get("agent_id", ""),
            "task_id": md.get("task_id", ""),
            "confidence": float(md.get("confidence", 0.0)),
            "previous_hash": stored_prev,
        }
        recomputed = calculate_event_hash(content)

        if stored_hash and recomputed != stored_hash:
            raise ChainIntegrityError(
                f"seq {event.get('seq')} hash mismatch: stored {stored_hash[:12]} "
                f"!= recomputed {recomputed[:12]}"
            )

        if index == 0:
            if stored_prev not in ("", None):
                raise ChainIntegrityError(
                    f"seq {event.get('seq')} is first event but previous_hash={stored_prev!r}"
                )
        else:
            prev_md = _metadata_of(events[index - 1])
            if stored_prev and stored_prev != prev_md.get("event_hash", ""):
                raise ChainIntegrityError(
                    f"seq {event.get('seq')} chain break: previous_hash={stored_prev[:12]} "
                    f"!= prior event_hash={prev_md.get('event_hash', '')[:12]}"
                )

    return {
        "valid": True,
        "events_checked": len(events),
        "last_event_hash": _metadata_of(events[-1]).get("event_hash", "") if events else "",
    }


class ChainIntegrityError(RuntimeError):
    """Raised when the hash chain validation fails (STOP condition)."""


def reconstruct_state(events: List[Dict[str, Any]]) -> ReconstructedState:
    """Fold an ordered event list into the final ReconstructedState.

    Order must be seq-ascending (as delivered by EventStore.replay()).
    """
    state = ReconstructedState()
    for event in events:
        state.apply(event)
    return state


def reconstruct_from_store(event_store, cursor: int = 0, topic: Optional[str] = None) -> ReconstructedState:
    """Convenience: replay events from the store and reconstruct the state."""
    events = event_store.replay(cursor=cursor, topic=topic, limit=2**31 - 1)
    return reconstruct_state(events)
