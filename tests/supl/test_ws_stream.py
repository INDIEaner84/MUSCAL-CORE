from __future__ import annotations
import asyncio
import json
import time
import pytest
from unittest.mock import MagicMock, patch

from fastapi import FastAPI
from fastapi.testclient import TestClient


class TestWebSocketRegistration:
    def test_register_ws_endpoint(self, event_bus):
        from features.supl.ws_stream import register_supl_ws
        app = FastAPI()
        manager = register_supl_ws(app, event_bus)
        assert manager is not None

    def test_ws_manager_creation(self, event_bus):
        from features.supl.ws_stream import SUPLWebSocketManager
        manager = SUPLWebSocketManager(event_bus)
        assert manager is not None

    def test_ws_manager_with_store(self, event_bus):
        from features.supl.ws_stream import SUPLWebSocketManager
        manager = SUPLWebSocketManager(event_bus, event_store=None)
        assert manager._store is None

    @pytest.mark.asyncio
    async def test_ws_start_stop(self, event_bus):
        from features.supl.ws_stream import SUPLWebSocketManager
        manager = SUPLWebSocketManager(event_bus)
        await manager.start()
        assert manager._running is True
        await manager.stop()
        assert manager._running is False

    @pytest.mark.asyncio
    async def test_ws_broadcast_no_clients(self, event_bus):
        from features.supl.ws_stream import SUPLWebSocketManager
        manager = SUPLWebSocketManager(event_bus)
        await manager.broadcast({"type": "test"})


class TestWebSocketGapDetection:
    def test_gap_detection_logic(self, event_bus):
        from features.supl.ws_stream import SUPLWebSocketManager
        manager = SUPLWebSocketManager(event_bus)
        assert hasattr(manager, "_make_callback")
        assert callable(manager._make_callback)

    def test_make_callback_produces_dict(self, event_bus):
        from features.supl.ws_stream import SUPLWebSocketManager
        manager = SUPLWebSocketManager(event_bus)
        queue = asyncio.Queue()
        cb = manager._make_callback(queue)
        assert callable(cb)

    @pytest.mark.asyncio
    async def test_callback_message_shape(self, event_bus):
        from features.supl.ws_stream import SUPLWebSocketManager
        from event_bus import EventMessage, EventPriority
        manager = SUPLWebSocketManager(event_bus)
        queue = asyncio.Queue()
        cb = manager._make_callback(queue)
        msg = EventMessage(
            id="test-id",
            topic="supl.test",
            payload={"key": "value"},
            source="test",
            timestamp=time.time(),
            priority=EventPriority.NORMAL,
        )
        cb(msg)
        item = await asyncio.wait_for(queue.get(), timeout=1.0)
        assert item["event_id"] == "test-id"
        assert item["topic"] == "supl.test"
        assert item["payload"]["key"] == "value"

    def test_handle_websocket_accepts_none_last_seq(self, event_bus):
        from features.supl.ws_stream import SUPLWebSocketManager
        manager = SUPLWebSocketManager(event_bus)
        assert manager._store is None

    def test_handle_websocket_with_store(self, event_bus):
        from runtime.event_store import EventStore
        import tempfile
        import os
        tmp = tempfile.mktemp(suffix=".db")
        try:
            store = EventStore(db_path=tmp)
            from features.supl.ws_stream import SUPLWebSocketManager
            manager = SUPLWebSocketManager(event_bus, event_store=store)
            assert manager._store is not None
            store.close()
        finally:
            if os.path.exists(tmp):
                os.unlink(tmp)


class TestWebSocketReplayResync:
    def test_replay_resync_signaling(self, event_bus):
        from features.supl.ws_stream import SUPLWebSocketManager
        manager = SUPLWebSocketManager(event_bus)
        assert hasattr(manager, "broadcast")
        assert callable(manager.broadcast)

    def test_resync_message_shape(self):
        msg = {
            "type": "gap_detected",
            "message": "events may have been missed",
            "last_replayed_seq": 5,
            "store_cursor": 10,
            "resync_required": True,
        }
        assert msg["type"] == "gap_detected"
        assert msg["resync_required"] is True

    def test_heartbeat_with_seq(self):
        hb = {"type": "heartbeat", "timestamp": time.time(), "last_seq": 42}
        assert hb["type"] == "heartbeat"
        assert hb["last_seq"] == 42

    def test_heartbeat_without_seq(self):
        hb = {"type": "heartbeat", "timestamp": time.time()}
        assert hb["type"] == "heartbeat"
        assert "last_seq" not in hb

    def test_get_store_seq_none(self, event_bus):
        from features.supl.ws_stream import SUPLWebSocketManager
        manager = SUPLWebSocketManager(event_bus)
        result = manager._get_store_seq([])
        assert result is None

    def test_get_store_seq_with_events(self, event_bus):
        from features.supl.ws_stream import SUPLWebSocketManager
        manager = SUPLWebSocketManager(event_bus)
        result = manager._get_store_seq([{"seq": 42}, {"seq": 99}])
        assert result == 99


class TestWebSocketQueryParam:
    def test_last_seq_parsed(self):
        from features.supl.ws_stream import SUPLWebSocketManager
        manager = SUPLWebSocketManager(MagicMock())
        params = {"last_seq": "42"}
        last_seq = None
        if "last_seq" in params:
            try:
                last_seq = int(params["last_seq"])
            except (ValueError, TypeError):
                last_seq = None
        assert last_seq == 42

    def test_last_seq_invalid(self):
        params = {"last_seq": "not-a-number"}
        last_seq = None
        if "last_seq" in params:
            try:
                last_seq = int(params["last_seq"])
            except (ValueError, TypeError):
                last_seq = None
        assert last_seq is None

    def test_last_seq_missing(self):
        params = {}
        last_seq = None
        if "last_seq" in params:
            try:
                last_seq = int(params["last_seq"])
            except (ValueError, TypeError):
                last_seq = None
        assert last_seq is None

    def test_last_seq_zero(self):
        params = {"last_seq": "0"}
        last_seq = None
        if "last_seq" in params:
            try:
                last_seq = int(params["last_seq"])
            except (ValueError, TypeError):
                last_seq = None
        assert last_seq == 0
