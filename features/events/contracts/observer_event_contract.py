"""Observer Event Contract (P0-2).

The official, versioned event representation produced by the Graph Observer
Layer. Built on top of the EventStore v2 migration (P0-1) and the hash rules
of H2_HASH_CONTRACT_ADDENDUM:

* SHA-256 over canonical JSON (sort_keys=True)
* wall-clock ``timestamp`` is part of the *transport* envelope but EXCLUDED
  from the hash content (determinism: same input ⇒ same hash)
* ``previous_hash``/``event_hash`` follow chain rules R1/R2/B3-B6
  (genesis event: previous_hash = "")

No graph.py rewrite, no EventStore change, no core architecture change.
"""

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field, asdict
from typing import Any, Dict, Optional

CONTRACT_VERSION = "1.0.0"

# ── Observer event types (GECS E1–E10, topics aus GRAPH_EVENT_COVERAGE_SPECIFICATION) ──

OBS_NODE_CREATED = "graph.node_created"          # E1
OBS_NODE_UPDATED = "graph.node_updated"          # E2
OBS_NODE_REMOVED = "graph.node_removed"          # E3 (neu, fehlt heute)
OBS_EDGE_CREATED = "graph.edge_created"          # E4
OBS_EDGE_REMOVED = "graph.edge_removed"          # E5 (neu, fehlt heute)
OBS_GRAPH_PRUNED = "graph.pruned"                # E6 (neu, fehlt heute)
OBS_FOCUS_CHANGED = "graph.focus_changed"        # E7 (neu, fehlt heute)
OBS_STATE_RESTORED = "graph.state_restored"      # E8 (neu, fehlt heute)
OBS_SNAPSHOT_CREATED = "graph.snapshot_created"  # E9 (neu, fehlt heute)
OBS_REBUILD_COMPLETED = "graph.rebuild_completed"  # E10 (neu, fehlt heute)
OBS_EXECUTION_STARTED = "graph.execution_started"  # existiert (kernel pipeline)
OBS_EXECUTION_FINISHED = "graph.execution_finished"  # existiert (kernel pipeline)
OBS_OBSERVATION_CREATED = "graph.observation_created"  # P0-2/3 Integration (Testevent)

ALL_OBSERVER_EVENT_TYPES = frozenset(
    [
        OBS_NODE_CREATED,
        OBS_NODE_UPDATED,
        OBS_NODE_REMOVED,
        OBS_EDGE_CREATED,
        OBS_EDGE_REMOVED,
        OBS_GRAPH_PRUNED,
        OBS_FOCUS_CHANGED,
        OBS_STATE_RESTORED,
        OBS_SNAPSHOT_CREATED,
        OBS_REBUILD_COMPLETED,
        OBS_EXECUTION_STARTED,
        OBS_EXECUTION_FINISHED,
        OBS_OBSERVATION_CREATED,
    ]
)

# Fields that participate in the canonical hash (H2 contract: no wall-clock).
HASH_CONTENT_FIELDS = (
    "event_type",
    "source",
    "payload",
    "agent_id",
    "task_id",
    "confidence",
    "previous_hash",
)


@dataclass
class ObserverEvent:
    """Canonical observer event (P0-2 contract).

    ``timestamp`` is transport metadata (wall-clock, excluded from hash).
    ``previous_hash``/``event_hash`` are set by the hash pipeline / producer.
    """

    event_type: str
    payload: Dict[str, Any] = field(default_factory=dict)
    source: str = "system"
    timestamp: float = field(default_factory=time.time)
    agent_id: str = ""
    task_id: str = ""
    confidence: float = 0.0
    previous_hash: str = ""
    event_hash: str = ""

    def __post_init__(self) -> None:
        if self.event_type not in ALL_OBSERVER_EVENT_TYPES:
            raise ValueError(
                f"unknown observer event type: {self.event_type!r} "
                f"(allowed: {sorted(ALL_OBSERVER_EVENT_TYPES)})"
            )

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ObserverEvent":
        return cls(
            event_type=data["event_type"],
            payload=dict(data.get("payload") or {}),
            source=data.get("source", "system"),
            timestamp=float(data.get("timestamp", time.time())),
            agent_id=data.get("agent_id", ""),
            task_id=data.get("task_id", ""),
            confidence=float(data.get("confidence", 0.0)),
            previous_hash=data.get("previous_hash", ""),
            event_hash=data.get("event_hash", ""),
        )

    def hash_content(self) -> Dict[str, Any]:
        """Canonical content for hashing (timestamp excluded)."""
        return {
            "event_type": self.event_type,
            "source": self.source,
            "payload": self.payload,
            "agent_id": self.agent_id,
            "task_id": self.task_id,
            "confidence": self.confidence,
            "previous_hash": self.previous_hash,
        }


@dataclass
class NormalizedEvent:
    """Producer-facing normalized event (P0-1).

    Canonical, transport-independent representation produced by the
    EventProducer. ``event_hash`` is NOT a manual field: it is always
    derived from the canonical representation (``hash_content()``) via the
    existing H2 hash pipeline (``features/events/event_hash.py``).

    Fields:
    * event_id        – unique id (default: uuid4); store UNIQUE constraint
                        doubles as idempotency guard
    * event_type      – one of the GECS observer types (E1–E10 + extras)
    * producer        – logical producer id (e.g. "eventstore_v2_adapter")
    * timestamp       – wall-clock transport metadata (EXCLUDED from hash)
    * payload         – business payload (dict)
    * metadata        – transport/chain metadata: source, actor, trace_id,
                        version, schema_version, agent_id, task_id,
                        confidence, previous_hash
    * correlation_id  – correlation identifier (not hashed, H2 contract)

    No Core changes; reuses the observer contract types for validation.
    """

    event_type: str
    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    producer: str = "eventstore_v2_adapter"
    timestamp: float = field(default_factory=time.time)
    payload: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    correlation_id: str = ""

    def __post_init__(self) -> None:
        if self.event_type not in ALL_OBSERVER_EVENT_TYPES:
            raise ValueError(
                f"unknown event type: {self.event_type!r} "
                f"(allowed: {sorted(ALL_OBSERVER_EVENT_TYPES)})"
            )
        if not isinstance(self.payload, dict):
            raise TypeError(f"payload must be a dict, got {type(self.payload).__name__}")
        if not isinstance(self.metadata, dict):
            raise TypeError(
                f"metadata must be a dict, got {type(self.metadata).__name__}"
            )

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "NormalizedEvent":
        return cls(
            event_type=data["event_type"],
            event_id=data.get("event_id", "") or str(uuid.uuid4()),
            producer=data.get("producer", "eventstore_v2_adapter"),
            timestamp=float(data.get("timestamp", time.time())),
            payload=dict(data.get("payload") or {}),
            metadata=dict(data.get("metadata") or {}),
            correlation_id=data.get("correlation_id", ""),
        )

    def hash_content(self) -> Dict[str, Any]:
        """Canonical content for hashing (H2 contract, timestamp excluded).

        Mirrors the field set used by ``state_model.validate_chain`` so that
        stored producer events are replay-verifiable by the existing P0-3
        validation (same input ⇒ same hash).
        """
        md = self.metadata or {}
        return {
            "event_type": self.event_type,
            "source": md.get("source", self.producer),
            "payload": self.payload,
            "agent_id": md.get("agent_id", ""),
            "task_id": md.get("task_id", ""),
            "confidence": float(md.get("confidence", 0.0)),
            "previous_hash": md.get("previous_hash", ""),
        }
