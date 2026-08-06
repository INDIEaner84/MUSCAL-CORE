"""Observer Event Contract tests (P0-2)."""

import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", ".."))

from features.events.contracts.observer_event_contract import (  # noqa: E402
    ALL_OBSERVER_EVENT_TYPES,
    OBS_NODE_CREATED,
    OBS_NODE_UPDATED,
    ObserverEvent,
)


class TestObserverEventContract:
    def test_to_dict_from_dict_roundtrip(self):
        ev = ObserverEvent(
            event_type=OBS_NODE_CREATED,
            payload={"node_id": "n1"},
            source="graph",
            agent_id="a1",
            task_id="t1",
            confidence=0.9,
            previous_hash="abc",
            event_hash="def",
            timestamp=123.0,
        )
        restored = ObserverEvent.from_dict(ev.to_dict())
        assert restored == ev
        assert restored.payload == {"node_id": "n1"}

    def test_invalid_event_type_rejected(self):
        with pytest.raises(ValueError):
            ObserverEvent(event_type="not.an.event")

    def test_hash_content_excludes_timestamp(self):
        a = ObserverEvent(
            event_type=OBS_NODE_UPDATED,
            payload={"k": "v"},
            timestamp=111.0,
        )
        b = ObserverEvent(
            event_type=OBS_NODE_UPDATED,
            payload={"k": "v"},
            timestamp=222.0,
        )
        assert a.hash_content() == b.hash_content()
        assert a.hash_content()["event_type"] == OBS_NODE_UPDATED

    def test_contract_contains_e10_set(self):
        assert len(ALL_OBSERVER_EVENT_TYPES) == 13
        assert OBS_NODE_CREATED in ALL_OBSERVER_EVENT_TYPES
