"""Event Producer layer (P0-1).

Implements the producer adapter on top of the EXISTING EventStore v2
infrastructure (REUSE BEFORE CREATE). No Core writes, no new pipeline.
"""

from .adapter import EventProducer, EventStoreV2Adapter
from .exceptions import (
    DuplicateEventError,
    EventHashMismatchError,
    EventValidationError,
    PersistenceError,
    ProducerError,
)
from .factory import create_producer, observer_producer_factory

__all__ = [
    "EventProducer",
    "EventStoreV2Adapter",
    "create_producer",
    "observer_producer_factory",
    "ProducerError",
    "EventValidationError",
    "EventHashMismatchError",
    "DuplicateEventError",
    "PersistenceError",
]
