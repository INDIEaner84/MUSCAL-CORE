from __future__ import annotations
import asyncio
import json
import time
from typing import Any, Dict, List, Optional, Set

from fastapi import FastAPI, WebSocket

from event_bus import EventBus, EventMessage
from runtime.event_store import EventStore


class SUPLWebSocketManager:
    def __init__(self, event_bus: EventBus, event_store: Optional[EventStore] = None, max_queue: int = 500):
        self._bus = event_bus
        self._store = event_store
        self._max_queue = max_queue
        self._clients: Set[WebSocket] = set()
        self._lock = asyncio.Lock()
        self._running = False

    async def start(self) -> None:
        self._running = True

    async def stop(self) -> None:
        self._running = False

    async def handle_websocket(self, ws: WebSocket, last_seq: Optional[int] = None) -> None:
        await ws.accept()
        async with self._lock:
            self._clients.add(ws)

        try:
            last_known_seq = last_seq
            store_cursor = None
            if self._store is not None:
                store_cursor = self._store.get_cursor()

            if last_seq is not None and self._store is not None:
                events = self._store.replay(cursor=last_seq, limit=500)
                for ev in events:
                    await ws.send_json(ev)
                    last_known_seq = ev.get("seq", last_known_seq)

                if store_cursor is not None and last_known_seq is not None:
                    gap = store_cursor - last_known_seq
                    if gap > 0:
                        remaining = self._store.replay(cursor=last_known_seq, limit=500)
                        for ev in remaining:
                            await ws.send_json(ev)
                            last_known_seq = ev.get("seq", last_known_seq)

                if store_cursor is not None and last_known_seq is not None and store_cursor > last_known_seq:
                    await ws.send_json({
                        "type": "gap_detected",
                        "message": "events may have been missed between replay and live transition",
                        "last_replayed_seq": last_known_seq,
                        "store_cursor": store_cursor,
                        "resync_required": True,
                    })

            queue: asyncio.Queue = asyncio.Queue(maxsize=self._max_queue)
            bus_callback = self._make_callback(queue, last_known_seq)

            self._bus.subscribe("*", bus_callback)
            try:
                while True:
                    try:
                        msg = await asyncio.wait_for(queue.get(), timeout=30.0)
                        await ws.send_json(msg)
                    except asyncio.TimeoutError:
                        try:
                            heartbeat = {"type": "heartbeat", "timestamp": time.time()}
                            if last_known_seq is not None:
                                heartbeat["last_seq"] = last_known_seq
                            await ws.send_json(heartbeat)
                        except Exception:
                            break
            except Exception:
                pass
            finally:
                self._bus.unsubscribe("*", bus_callback)
        except Exception:
            pass
        finally:
            async with self._lock:
                self._clients.discard(ws)
            try:
                await ws.close()
            except Exception:
                pass

    def _make_callback(self, queue: asyncio.Queue, last_known_seq: Optional[int] = None):
        def callback(msg: EventMessage) -> None:
            try:
                payload = {
                    "seq": 0,
                    "event_id": msg.id,
                    "topic": msg.topic,
                    "payload": msg.payload,
                    "timestamp": msg.timestamp,
                    "source": msg.source,
                }
                try:
                    loop = asyncio.get_event_loop()
                    if loop.is_running():
                        loop.call_soon_threadsafe(lambda: queue.put_nowait(payload))
                except Exception:
                    pass
            except Exception:
                pass
        return callback

    async def broadcast(self, message: Dict[str, Any]) -> None:
        async with self._lock:
            stale = set()
            for ws in self._clients:
                try:
                    await ws.send_json(message)
                except Exception:
                    stale.add(ws)
            self._clients -= stale

    def _get_store_seq(self, store_events: List[Dict[str, Any]]) -> Optional[int]:
        if not store_events:
            return None
        return store_events[-1].get("seq")


def register_supl_ws(
    app: FastAPI,
    event_bus: EventBus,
    event_store: Optional[EventStore] = None,
) -> SUPLWebSocketManager:
    manager = SUPLWebSocketManager(event_bus, event_store)

    @app.websocket("/api/supl/stream")
    async def supl_stream(ws: WebSocket):
        last_seq_param = ws.query_params.get("last_seq")
        last_seq = None
        if last_seq_param is not None:
            try:
                last_seq = int(last_seq_param)
            except (ValueError, TypeError):
                last_seq = None
        await manager.handle_websocket(ws, last_seq)

    return manager
