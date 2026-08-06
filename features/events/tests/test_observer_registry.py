"""Observer registry tests (P0-2)."""

import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", ".."))

from features.events.contracts.observer_event_contract import (  # noqa: E402
    OBS_NODE_CREATED,
)
from features.events import observer_registry  # noqa: E402


@pytest.fixture(autouse=True)
def _clean_registry():
    observer_registry.clear()
    yield
    observer_registry.clear()


class TestObserverRegistry:
    def test_register_emit_list(self):
        received = []
        observer_registry.register(lambda ev: received.append(ev))
        observer_registry.emit(
            {"event_type": OBS_NODE_CREATED, "payload": {"node_id": "x"}}
        )
        assert len(received) == 1
        assert received[0].event_type == OBS_NODE_CREATED
        assert received[0].payload == {"node_id": "x"}
        assert len(observer_registry.list_observers()) == 1

    def test_unregister_stops_dispatch(self):
        received = []

        def obs(ev):
            received.append(ev)

        observer_registry.register(obs)
        assert observer_registry.unregister(obs) is True
        observer_registry.emit(
            {"event_type": OBS_NODE_CREATED, "payload": {}}
        )
        assert received == []
        assert observer_registry.unregister(obs) is False

    def test_emit_rejects_non_event(self):
        with pytest.raises(TypeError):
            observer_registry.emit("not an event")

    def test_failing_observer_isolated(self):
        received = []

        def bad(ev):
            raise RuntimeError("boom")

        def good(ev):
            received.append(ev)

        observer_registry.register(bad)
        observer_registry.register(good)
        observer_registry.emit(
            {"event_type": OBS_NODE_CREATED, "payload": {}}
        )
        assert len(received) == 1
