"""Event hash pipeline tests (P0-2, Phase 4).

Contract: same input ⇒ same hash; changed payload ⇒ different hash.
"""

import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", ".."))

from features.events.contracts.observer_event_contract import (  # noqa: E402
    OBS_NODE_CREATED,
    OBS_NODE_UPDATED,
    ObserverEvent,
)
from features.events.event_hash import (  # noqa: E402
    calculate_event_hash,
    canonical_json,
    validate_hash,
)


class TestEventHash:
    def test_same_input_same_hash(self):
        ev_a = ObserverEvent(
            event_type=OBS_NODE_CREATED,
            payload={"node_id": "n1", "type": "INTENT"},
        )
        ev_b = ObserverEvent(
            event_type=OBS_NODE_CREATED,
            payload={"node_id": "n1", "type": "INTENT"},
        )
        assert calculate_event_hash(ev_a) == calculate_event_hash(ev_b)

    def test_changed_payload_different_hash(self):
        base = ObserverEvent(
            event_type=OBS_NODE_CREATED,
            payload={"node_id": "n1"},
        )
        changed = ObserverEvent(
            event_type=OBS_NODE_CREATED,
            payload={"node_id": "n1", "extra": True},
        )
        assert calculate_event_hash(base) != calculate_event_hash(changed)

    def test_changed_field_different_hash(self):
        a = ObserverEvent(
            event_type=OBS_NODE_UPDATED,
            payload={"status": "planned"},
        )
        b = ObserverEvent(
            event_type=OBS_NODE_UPDATED,
            payload={"status": "running"},
        )
        assert calculate_event_hash(a) != calculate_event_hash(b)

    def test_canonical_json_sort_keys(self):
        content_a = {"b": 1, "a": {"z": 2, "y": 1}}
        content_b = {"a": {"y": 1, "z": 2}, "b": 1}
        assert canonical_json(content_a) == canonical_json(content_b)

    def test_sha256_hex_64(self):
        ev = ObserverEvent(event_type=OBS_NODE_CREATED, payload={})
        digest = calculate_event_hash(ev)
        assert len(digest) == 64
        assert all(c in "0123456789abcdef" for c in digest)

    def test_validate_hash(self):
        ev = ObserverEvent(event_type=OBS_NODE_CREATED, payload={"n": 1})
        digest = calculate_event_hash(ev)
        assert validate_hash(ev, digest) is True
        assert validate_hash(ev, "x" * 64) is False
