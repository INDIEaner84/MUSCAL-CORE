"""NormalizedEvent validation (P0-1).

Validates the producer-facing event contract:

* required fields present with correct types
* event_type is a known GECS observer type (reuses contract whitelist)
* hash consistency via the EXISTING hash pipeline (event_hash.py)
  — manipulated events are rejected.

Reuses: ALL_OBSERVER_EVENT_TYPES (contract), validate_hash (event_hash).
"""

from __future__ import annotations

from typing import List

from ..contracts.observer_event_contract import (
    ALL_OBSERVER_EVENT_TYPES,
    NormalizedEvent,
)
from ..event_hash import validate_hash
from ..producer.exceptions import EventHashMismatchError, EventValidationError

VALIDATOR_VERSION = "1.0.0"

REQUIRED_STRING_FIELDS = ("event_id", "event_type", "producer")
REQUIRED_DICT_FIELDS = ("payload", "metadata")
REQUIRED_FLOAT_FIELDS = ("timestamp",)


def collect_errors(event: NormalizedEvent) -> List[str]:
    """Return all structural validation errors (no raises)."""
    errors: List[str] = []
    if not isinstance(event, NormalizedEvent):
        return ["not a NormalizedEvent"]

    if not isinstance(event.event_id, str) or not event.event_id:
        errors.append("event_id: required non-empty string")
    if not isinstance(event.event_type, str) or not event.event_type:
        errors.append("event_type: required non-empty string")
    elif event.event_type not in ALL_OBSERVER_EVENT_TYPES:
        errors.append(f"event_type: unknown {event.event_type!r}")
    if not isinstance(event.producer, str) or not event.producer:
        errors.append("producer: required non-empty string")
    if not isinstance(event.payload, dict):
        errors.append("payload: required dict")
    if not isinstance(event.metadata, dict):
        errors.append("metadata: required dict")
    if not isinstance(event.timestamp, (int, float)):
        errors.append("timestamp: required number")
    if not isinstance(event.correlation_id, str):
        errors.append("correlation_id: required string")
    return errors


def verify_hash_consistency(event: NormalizedEvent) -> bool:
    """Verify the canonical hash against the expected hash.

    Uses the EXISTING H2 pipeline (``event_hash.validate_hash``). Rejects
    manipulated events (changed payload/metadata ⇒ hash mismatch).
    """
    expected = (event.metadata or {}).get("event_hash", "")
    if not expected:
        return True
    return validate_hash(event, expected)


def validate_event(
    event: NormalizedEvent,
    *,
    check_hash: bool = True,
    raise_on_error: bool = True,
) -> bool:
    """Validate a NormalizedEvent (structure + optional hash consistency).

    Returns True when valid. With ``raise_on_error`` (default) raises
    EventValidationError / EventHashMismatchError instead of returning
    False.
    """
    errors = collect_errors(event)
    if errors:
        if raise_on_error:
            raise EventValidationError("; ".join(errors))
        return False
    if check_hash and not verify_hash_consistency(event):
        if raise_on_error:
            raise EventHashMismatchError(
                f"hash mismatch for event {event.event_id!r}"
            )
        return False
    return True
