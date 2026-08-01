from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory

from runtime.event_store import EventStore

from features.runtime.coordinator import RuntimeCoordinator
from features.runtime.models import RuntimeConfig


class TestCoordinatorEventStoreIntegration:

    def test_coordinator_with_event_store(self):
        tmpdir = TemporaryDirectory()
        store_path = Path(tmpdir.name) / "test_coord.db"
        store = EventStore(store_path)
        config = RuntimeConfig(event_store_path=str(store_path))
        coord = RuntimeCoordinator(config=config, event_store=store)
        output = coord.execute("--help")
        assert output.session_id is not None
        started = store.replay(topic="runtime.execution.started")
        assert len(started) >= 1
        store.close()
        tmpdir.cleanup()

    def test_coordinator_events_written(self):
        tmpdir = TemporaryDirectory()
        store_path = Path(tmpdir.name) / "test_events.db"
        store = EventStore(store_path)
        config = RuntimeConfig(event_store_path=str(store_path))
        coord = RuntimeCoordinator(config=config, event_store=store)
        output = coord.execute("--help")
        runtime_events = store.replay(topic=None)
        topics = {e["topic"] for e in runtime_events}
        assert "runtime.session.created" in topics
        assert "runtime.execution.started" in topics
        store.close()
        tmpdir.cleanup()
