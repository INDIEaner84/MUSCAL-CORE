from __future__ import annotations

from pathlib import Path

import pytest

from features.bridge.bridge_event_writer import BridgeEventWriter, BRIDGE_EXECUTION_TOPIC


class TestBridgeEventWriter:

    def test_writer_requires_store_or_path(self):
        writer = BridgeEventWriter()
        assert not writer.is_connected

    def test_writer_connects_with_db_path(self, tmp_path: Path):
        db = tmp_path / "test_bridge.db"
        writer = BridgeEventWriter(db_path=db)
        assert writer.is_connected

    def test_write_execution_event_returns_seq(self, tmp_path: Path):
        db = tmp_path / "test_events.db"
        writer = BridgeEventWriter(db_path=db)
        seq = writer.write_execution_event(
            task_id="task-001",
            project_id="/test/project",
            execution_id="exec-001",
            opencode_session="ses_123",
            status="completed",
        )
        assert seq is not None
        assert isinstance(seq, int)
        assert seq > 0

    def test_write_execution_event_fails_without_store(self):
        writer = BridgeEventWriter()
        seq = writer.write_execution_event(
            task_id="task-002",
            project_id="/test/project",
            execution_id="exec-002",
            opencode_session=None,
            status="failed",
        )
        assert seq is None

    def test_written_event_can_be_replayed(self, tmp_path: Path):
        db = tmp_path / "test_replay.db"
        writer = BridgeEventWriter(db_path=db)
        writer.write_execution_event(
            task_id="task-replay",
            project_id="/test",
            execution_id="exec-replay",
            opencode_session="ses_replay",
            status="completed",
        )
        from runtime.event_store import EventStore
        store = EventStore(db)
        events = store.replay(topic=BRIDGE_EXECUTION_TOPIC, limit=10)
        assert len(events) >= 1
        assert events[0]["topic"] == BRIDGE_EXECUTION_TOPIC

    def test_writer_with_correlation_id(self, tmp_path: Path):
        db = tmp_path / "test_corr.db"
        writer = BridgeEventWriter(db_path=db)
        seq = writer.write_execution_event(
            task_id="task-corr",
            project_id="/test",
            execution_id="exec-corr",
            opencode_session="ses_corr",
            status="completed",
            correlation_id="corr-001",
        )
        assert seq is not None
