"""EventStore v2 adapter (P0-1).

Implements the ``EventProducer`` interface on top of the EXISTING
infrastructure (REUSE BEFORE CREATE):

    NormalizedEvent
        → validate (validation/validator.py)
        → hash via HashService (event_hash.py, H2 contract)
        → v2 mapping (this module)
        → ConsolidatedEventWriter (existing writer → EventStore v2)
        → persist

Rules:
* NO Core writes (only additive usage of existing features/events modules)
* NO new event pipeline: writer + store + replay are the existing ones
* Idempotency: the store's UNIQUE event_id constraint is the guard;
  ``sqlite3.IntegrityError`` is translated into ``DuplicateEventError``.
"""

from __future__ import annotations

import logging
import sqlite3
import time
import uuid
from typing import Any, Dict, List, Optional

from ..contracts.observer_event_contract import NormalizedEvent
from ..event_hash import HashService
from ..event_consolidation import ConsolidatedEventWriter
from ..validation.validator import validate_event
from .exceptions import DuplicateEventError, EventHashMismatchError, PersistenceError

log = logging.getLogger(__name__)

ADAPTER_VERSION = "1.0.0"

DEFAULT_SCHEMA_VERSION = 2
DEFAULT_EVENT_VERSION = 2
DEFAULT_SOURCE = "graph"


class EventProducer:
    """Producer interface (P0-1).

    create_event() → build a NormalizedEvent (id/chain defaults applied)
    validate()    → structural + hash validation (raises on invalid)
    publish()     → hash, map to v2 and persist (returns seq or None)
    """

    def create_event(
        self,
        event_type: str,
        payload: Optional[Dict[str, Any]] = None,
        *,
        metadata: Optional[Dict[str, Any]] = None,
        correlation_id: str = "",
        timestamp: Optional[float] = None,
        event_id: Optional[str] = None,
        previous_hash: Optional[str] = None,
    ) -> NormalizedEvent:
        raise NotImplementedError

    def validate(self, event: NormalizedEvent) -> bool:
        raise NotImplementedError

    def publish(self, event: NormalizedEvent) -> Optional[int]:
        raise NotImplementedError


class EventStoreV2Adapter(EventProducer):
    """Producer adapter persisting NormalizedEvents into the EventStore v2."""

    def __init__(
        self,
        event_store=None,
        writer: Optional[ConsolidatedEventWriter] = None,
        producer: str = "eventstore_v2_adapter",
        source: str = DEFAULT_SOURCE,
        agent_id: str = "",
        task_id: str = "",
        confidence: float = 0.0,
        schema_version: int = DEFAULT_SCHEMA_VERSION,
        event_version: int = DEFAULT_EVENT_VERSION,
    ):
        self._event_store = event_store
        self._writer = writer or (
            ConsolidatedEventWriter(event_store=event_store)
            if event_store is not None
            else None
        )
        self._producer = producer
        self._source = source
        self._agent_id = agent_id
        self._task_id = task_id
        self._confidence = confidence
        self._schema_version = schema_version
        self._event_version = event_version
        self._hash_service = HashService()
        self._last_hash: str = ""

    # ── EventProducer interface ──────────────────────────────────────

    def create_event(
        self,
        event_type: str,
        payload: Optional[Dict[str, Any]] = None,
        *,
        metadata: Optional[Dict[str, Any]] = None,
        correlation_id: str = "",
        timestamp: Optional[float] = None,
        event_id: Optional[str] = None,
        previous_hash: Optional[str] = None,
    ) -> NormalizedEvent:
        md = dict(metadata or {})
        md.setdefault("source", self._source)
        md.setdefault("agent_id", self._agent_id)
        md.setdefault("task_id", self._task_id)
        md.setdefault("confidence", self._confidence)
        md.setdefault("version", self._event_version)
        md.setdefault("schema_version", self._schema_version)
        if previous_hash is not None:
            md["previous_hash"] = previous_hash
        elif not md.get("previous_hash"):
            md["previous_hash"] = self._last_hash
        return NormalizedEvent(
            event_type=event_type,
            event_id=event_id or str(uuid.uuid4()),
            producer=self._producer,
            timestamp=timestamp if timestamp is not None else time.time(),
            payload=dict(payload or {}),
            metadata=md,
            correlation_id=correlation_id or "",
        )

    def validate(self, event: NormalizedEvent) -> bool:
        return validate_event(event)

    def publish(self, event: NormalizedEvent) -> Optional[int]:
        """Hash, validate, map to v2 and persist.

        Returns the assigned store seq; None if no store is attached.
        Raises DuplicateEventError when event_id already exists.
        """
        if self._writer is None:
            log.warning("publish skipped: no EventStore attached")
            return None

        self.validate(event)
        mapping = self.to_v2_mapping(event)
        try:
            seq = self._writer.write_event(**mapping)
        except sqlite3.IntegrityError as exc:
            raise DuplicateEventError(
                f"event_id already persisted: {event.event_id!r}"
            ) from exc
        except Exception as exc:
            raise PersistenceError(
                f"persist failed for event {event.event_id!r}: {exc}"
            ) from exc

        event.metadata["event_hash"] = mapping["metadata"]["event_hash"]
        event.metadata["previous_hash"] = mapping["metadata"]["previous_hash"]
        self._last_hash = event.metadata["event_hash"]
        return seq

    # ── v2 mapping (NormalizedEvent → EventStore v2 dict) ────────────

    def to_v2_mapping(self, event: NormalizedEvent) -> Dict[str, Any]:
        """Map a NormalizedEvent to the existing writer/store contract."""
        md = dict(event.metadata or {})
        md["previous_hash"] = md.get("previous_hash", "")
        md["event_hash"] = self._hash_service.calculate_hash(event)
        return {
            "topic": event.event_type,
            "payload": event.payload,
            "source": md.get("source", event.producer),
            "priority": "NORMAL",
            "event_id": event.event_id,
            "execution_id": md.get("task_id", ""),
            "correlation_id": event.correlation_id,
            "causation_id": md.get("causation_id", ""),
            "execution_mode": "real",
            "verification_state": md.get("verification_state", "unverified"),
            "metadata": md,
            "prev_hash": md.get("previous_hash", ""),
            "schema_version": int(md.get("schema_version", DEFAULT_SCHEMA_VERSION)),
            "event_version": int(md.get("version", DEFAULT_EVENT_VERSION)),
            "agent_id": md.get("agent_id", ""),
            "task_id": md.get("task_id", ""),
            "confidence": float(md.get("confidence", 0.0)),
        }

    @classmethod
    def from_stored(cls, stored: Dict[str, Any]) -> NormalizedEvent:
        """Reconstruct a NormalizedEvent from a stored/replayed row.

        Enables replay compatibility: producer events read back through the
        existing replay reader remain valid producer contracts.
        """
        md = dict(stored.get("metadata") or {})
        md.setdefault("source", stored.get("source", DEFAULT_SOURCE))
        md.setdefault("previous_hash", stored.get("prev_hash", ""))
        md.setdefault("event_hash", md.get("event_hash", ""))
        return NormalizedEvent(
            event_type=stored.get("topic", ""),
            event_id=stored.get("id", ""),
            producer=md.get("source", stored.get("source", DEFAULT_SOURCE)),
            timestamp=float(stored.get("timestamp", 0.0)),
            payload=dict(stored.get("payload") or {}),
            metadata=md,
            correlation_id=stored.get("correlation_id", ""),
        )

    def verify_hash(self, event: NormalizedEvent, expected: Optional[str] = None) -> bool:
        """Verify the canonical hash of a NormalizedEvent (or its stored hash)."""
        expected = expected if expected is not None else (event.metadata or {}).get("event_hash", "")
        if not self._hash_service.verify_hash(event, expected):
            raise EventHashMismatchError(
                f"hash mismatch for event {event.event_id!r}"
            )
        return True

    # ── replay passthrough (existing reader) ─────────────────────────

    def replay(
        self, cursor: Optional[int] = None, topic: Optional[str] = None, limit: int = 100
    ) -> List[Dict[str, Any]]:
        if self._writer is None:
            return []
        return self._writer.replay(cursor=cursor, topic=topic, limit=limit)

    def count(self, topic: Optional[str] = None) -> int:
        if self._writer is None:
            return 0
        return self._writer.count(topic=topic)

    def reset_chain(self) -> None:
        """Reset the hash chain (next published event becomes a genesis)."""
        self._last_hash = ""
