"""Event producer factory (P0-1).

Factory helpers to build EventProducer instances while reusing the existing
writer pipeline (ConsolidatedEventWriter) and the observer adapter wiring.
"""

from __future__ import annotations

from typing import Any, Callable, Dict, Optional

from ..contracts.observer_event_contract import NormalizedEvent, ObserverEvent
from .adapter import EventProducer, EventStoreV2Adapter

FACTORY_VERSION = "1.0.0"

PRODUCER_TYPES = ("eventstore_v2",)


def create_producer(
    event_store=None,
    *,
    producer_type: str = "eventstore_v2",
    **options: Any,
) -> EventProducer:
    """Build a producer instance (default: EventStoreV2Adapter).

    ``options`` are forwarded to the adapter constructor (source, agent_id,
    task_id, confidence, schema_version, event_version, ...).
    """
    if producer_type not in PRODUCER_TYPES:
        raise ValueError(
            f"unknown producer_type {producer_type!r} (allowed: {PRODUCER_TYPES})"
        )
    if producer_type == "eventstore_v2":
        return EventStoreV2Adapter(event_store=event_store, **options)
    raise AssertionError("unreachable")


def create_v2_adapter(event_store=None, **options: Any) -> EventStoreV2Adapter:
    """Convenience: typed adapter (normalized events, v2 persistence)."""
    adapter = create_producer(event_store, producer_type="eventstore_v2", **options)
    assert isinstance(adapter, EventStoreV2Adapter)
    return adapter


def observer_producer_factory(
    adapter: EventProducer,
) -> Callable[[ObserverEvent], Optional[int]]:
    """Wrap an EventProducer so it accepts ObserverEvents (P0-2 wiring).

    Reuses the existing GraphObserverAdapter → producer callable contract:
    an ObserverEvent is normalized (source/agent/task/chain fields travel
    through metadata) and published through the adapter.
    """

    def _produce(event: ObserverEvent) -> Optional[int]:
        normalized = NormalizedEvent(
            event_type=event.event_type,
            producer=getattr(adapter, "_producer", "observer_bridge"),
            timestamp=event.timestamp,
            payload=dict(event.payload),
            metadata={
                "source": event.source,
                "agent_id": event.agent_id,
                "task_id": event.task_id,
                "confidence": event.confidence,
                "previous_hash": event.previous_hash,
                "event_hash": event.event_hash,
                "version": 2,
                "schema_version": 2,
            },
            correlation_id="",
        )
        return adapter.publish(normalized)

    return _produce
