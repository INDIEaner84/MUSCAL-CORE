"""Event hash pipeline (P0-2, Phase 4).

Implements ``calculate_event_hash()`` per the H2 hash contract:

* SHA-256
* canonical JSON serialization, ``sort_keys=True``
* wall-clock fields (timestamp) excluded → same input ⇒ same hash
* changed payload ⇒ different hash

Accepts either a mapping (dict) or an ``ObserverEvent``. For dicts, only the
canonical hash fields are used; unknown keys are ignored (hash stability).
"""

from __future__ import annotations

import hashlib
import json
from typing import Any, Dict, Mapping, Optional

HASH_ALGORITHM = "sha256"
HASH_VERSION = "1.0.0"

HASH_CONTENT_FIELDS = (
    "event_type",
    "source",
    "payload",
    "agent_id",
    "task_id",
    "confidence",
    "previous_hash",
)


def _canonical_content(event: Mapping[str, Any]) -> Dict[str, Any]:
    try:
        from .contracts.observer_event_contract import NormalizedEvent, ObserverEvent

        if isinstance(event, ObserverEvent):
            return event.hash_content()
        if isinstance(event, NormalizedEvent):
            return event.hash_content()
    except ImportError:  # pragma: no cover - defensive
        pass

    content: Dict[str, Any] = {}
    for field in HASH_CONTENT_FIELDS:
        value = event.get(field)
        if isinstance(value, dict):
            value = dict(value)
        content[field] = value
    return content


def canonical_json(content: Mapping[str, Any]) -> str:
    """Canonical JSON serialization (sort_keys, compact separators)."""
    return json.dumps(
        content,
        sort_keys=True,
        ensure_ascii=False,
        separators=(",", ":"),
    )


def calculate_event_hash(event: Mapping[str, Any] | Any) -> str:
    """SHA-256 hexdigest over the canonical hash content of the event."""
    content = _canonical_content(event)
    blob = canonical_json(content).encode("utf-8")
    return hashlib.sha256(blob).hexdigest()


def validate_hash(event: Mapping[str, Any] | Any, expected: str) -> bool:
    """Compare an event's hash against ``expected`` (None/'' allowed)."""
    if not expected:
        return True
    return calculate_event_hash(event) == expected


class HashService:
    """Thin wrapper (P0-1) over the existing H2 hash pipeline.

    Deliberately NOT a new hash implementation: it reuses
    ``calculate_event_hash``/``validate_hash`` (single source of truth).
    Keeps the hash responsibility cleanly separated from the producer
    adapter while keeping determinism (same input ⇒ same hash).
    """

    def __init__(self, algorithm: str = HASH_ALGORITHM) -> None:
        if algorithm not in ("sha256",):
            raise ValueError(f"unsupported algorithm: {algorithm!r}")
        self.algorithm = algorithm

    def calculate_hash(self, event: Mapping[str, Any] | Any) -> str:
        """Compute the canonical SHA-256 digest for an event."""
        return calculate_event_hash(event)

    def verify_hash(self, event: Mapping[str, Any] | Any, expected: str) -> bool:
        """Return True if the recomputed hash equals ``expected``."""
        return validate_hash(event, expected)
