"""Event Producer exceptions (P0-1).

Typed, controlled errors raised by the producer layer. No Core changes.
"""

from __future__ import annotations


class ProducerError(RuntimeError):
    """Base class for all EventProducer errors."""


class EventValidationError(ProducerError):
    """Raised when a NormalizedEvent is structurally invalid."""


class EventHashMismatchError(ProducerError):
    """Raised when a hash verification fails (manipulated event)."""


class DuplicateEventError(ProducerError):
    """Raised when an event_id is published twice (idempotency guard)."""


class PersistenceError(ProducerError):
    """Raised when persisting a NormalizedEvent into the EventStore fails."""