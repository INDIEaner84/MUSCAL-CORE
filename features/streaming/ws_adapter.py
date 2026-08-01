import asyncio
import json
import logging
import threading
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set

import websockets
from websockets.server import WebSocketServer

from event_bus import EventBus, EventMessage
from features.projection.graph_os_projection import GraphOSProjection
from runtime.event_store import EventStore

logger = logging.getLogger(__name__)

ADAPTER_VERSION = "2.0.0"

DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8765
MAX_QUEUE_SIZE = 1000
HEARTBEAT_INTERVAL = 5.0
HEARTBEAT_TIMEOUT = 15.0
RECONCILIATION_INTERVAL = 30.0
MAX_RECONCILIATION_EVENTS = 2000
SNAPSHOT_GAP_THRESHOLD = 1000
STALE_DISCONNECT_SECONDS = 60.0
SNAPSHOT_SCHEMA_VERSION = 1


@dataclass
class ClientSession:
    websocket: Any
    client_id: str
    last_seq: int = 0
    subscribed_types: Optional[Set[str]] = None
    queue: asyncio.Queue = field(default_factory=lambda: asyncio.Queue(maxsize=MAX_QUEUE_SIZE))
    connected_at: float = 0.0
    last_heartbeat: float = 0.0
    last_reconciliation: float = 0.0
    bytes_sent: int = 0
    messages_sent: int = 0


class WebSocketAdapter:
    def __init__(
        self,
        event_bus: EventBus,
        event_store: EventStore,
        projection: GraphOSProjection,
        host: str = DEFAULT_HOST,
        port: int = DEFAULT_PORT,
    ):
        self.event_bus = event_bus
        self.event_store = event_store
        self.projection = projection
        self.host = host
        self.port = port

        self._clients: Dict[str, ClientSession] = {}
        self._lock = threading.Lock()
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        self._thread: Optional[threading.Thread] = None
        self._server: Optional[WebSocketServer] = None
        self._running = False

    def start(self) -> None:
        if self._running:
            logger.warning("WebSocketAdapter already running")
            return
        self._running = True
        self._thread = threading.Thread(target=self._run_loop, name="ws-adapter", daemon=True)
        self._thread.start()
        logger.info("WebSocketAdapter starting on ws://%s:%s", self.host, self.port)

    def _run_loop(self) -> None:
        self._loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self._loop)
        try:
            self._loop.run_until_complete(self._serve())
        except Exception as e:
            logger.error("WebSocketAdapter event loop failed: %s", e)
        finally:
            self._loop.close()

    async def _serve(self) -> None:
        self._server = await websockets.serve(
            self._handle_client,
            self.host,
            self.port,
            ping_interval=None,
            ping_timeout=None,
        )
        logger.info("WebSocketAdapter server listening on %s:%s", self.host, self.port)
        try:
            await self._maintenance_loop()
        finally:
            if self._server:
                self._server.close()
                await self._server.wait_closed()
            logger.info("WebSocketAdapter server stopped")

    async def _maintenance_loop(self) -> None:
        while self._running:
            await asyncio.sleep(1.0)
            now = time.time()
            stale_ids: List[str] = []
            reconciliation_ids: List[str] = []
            with self._lock:
                for cid, session in list(self._clients.items()):
                    if now - session.last_heartbeat > HEARTBEAT_TIMEOUT:
                        stale_ids.append(cid)
                    elif now - session.last_reconciliation > RECONCILIATION_INTERVAL:
                        reconciliation_ids.append(cid)
            for cid in stale_ids:
                await self._disconnect_client(cid, "heartbeat timeout")
            for cid in reconciliation_ids:
                await self._send_reconciliation(cid)

    async def _handle_client(self, websocket) -> None:
        client_id = str(int(time.time() * 1_000_000)) + f"_{id(websocket)}"
        session = ClientSession(
            websocket=websocket,
            client_id=client_id,
            connected_at=time.time(),
            last_heartbeat=time.time(),
            last_reconciliation=time.time(),
        )
        with self._lock:
            self._clients[client_id] = session
        logger.info("Client connected: %s (total: %d)", client_id, len(self._clients))

        try:
            sender_task = asyncio.create_task(self._sender_loop(session))
            receiver_task = asyncio.create_task(self._receiver_loop(session))
            done, pending = await asyncio.wait(
                [sender_task, receiver_task],
                return_when=asyncio.FIRST_COMPLETED,
            )
            for task in pending:
                task.cancel()
                try:
                    await task
                except (asyncio.CancelledError, Exception):
                    pass
        except Exception as e:
            logger.debug("Client %s handler error: %s", client_id, e)
        finally:
            with self._lock:
                self._clients.pop(client_id, None)
            logger.info("Client disconnected: %s (total: %d)", client_id, len(self._clients))

    async def _sender_loop(self, session: ClientSession) -> None:
        ws = session.websocket
        while self._running:
            try:
                message = await asyncio.wait_for(session.queue.get(), timeout=1.0)
                data = json.dumps(message, ensure_ascii=False)
                await ws.send(data)
                session.bytes_sent += len(data)
                session.messages_sent += 1
            except asyncio.TimeoutError:
                continue
            except websockets.exceptions.ConnectionClosed:
                break
            except Exception as e:
                logger.debug("Send error for %s: %s", session.client_id, e)
                break

    async def _receiver_loop(self, session: ClientSession) -> None:
        ws = session.websocket
        try:
            async for raw in ws:
                try:
                    msg = json.loads(raw)
                except json.JSONDecodeError:
                    await self._enqueue(session, {"type": "error", "code": "INVALID_JSON", "message": "payload must be valid JSON"})
                    continue
                await self._handle_client_message(session, msg)
        except websockets.exceptions.ConnectionClosed:
            pass
        except Exception as e:
            logger.debug("Receive error for %s: %s", session.client_id, e)

    async def _handle_client_message(self, session: ClientSession, msg: Dict[str, Any]) -> None:
        msg_type = msg.get("type", "")
        if msg_type == "ping":
            session.last_heartbeat = time.time()
            await self._enqueue(session, {"type": "pong"})
        elif msg_type == "subscribe":
            session.last_seq = msg.get("last_seq", 0)
            raw_types = msg.get("filters", {}).get("event_types", [])
            session.subscribed_types = set(raw_types) if raw_types else None
            await self._deliver_snapshot_or_delta(session)
            session.last_reconciliation = time.time()
        elif msg_type == "unsubscribe":
            session.subscribed_types = None
            await self._enqueue(session, {"type": "unsubscribed"})

    async def _deliver_snapshot_or_delta(self, session: ClientSession) -> None:
        current_seq = self._get_current_seq()
        gap = current_seq - session.last_seq
        if session.last_seq == 0 or gap > SNAPSHOT_GAP_THRESHOLD:
            await self._deliver_snapshot(session, current_seq)
        else:
            await self._deliver_delta(session, current_seq)

    async def _deliver_snapshot(self, session: ClientSession, current_seq: int) -> None:
        nodes = await self._build_snapshot_nodes()
        edges = await self._build_snapshot_edges()
        snapshot = {
            "type": "snapshot",
            "seq": current_seq,
            "schema_version": SNAPSHOT_SCHEMA_VERSION,
            "nodes": nodes,
            "edges": edges,
        }
        await self._enqueue(session, snapshot)
        session.last_seq = current_seq
        logger.debug("Snapshot delivered to %s (seq=%d, nodes=%d, edges=%d)",
                     session.client_id, current_seq, len(nodes), len(edges))

    async def _deliver_delta(self, session: ClientSession, current_seq: int) -> None:
        try:
            events = self.event_store.replay(cursor=session.last_seq, limit=SNAPSHOT_GAP_THRESHOLD)
        except Exception as e:
            logger.warning("Delta replay failed for %s: %s", session.client_id, e)
            await self._deliver_snapshot(session, current_seq)
            return

        count = 0
        for row in events:
            seq = row.get("seq", 0)
            if seq <= session.last_seq:
                continue
            projected = self._project_row(row)
            if projected is not None:
                await self._enqueue(session, projected)
                count += 1
            session.last_seq = seq

        logger.debug("Delta delivered to %s (from seq=%d, events=%d)", session.client_id, session.last_seq, count)

    def _get_current_seq(self) -> int:
        try:
            return self.event_store.get_cursor()
        except Exception:
            return 0

    async def _build_snapshot_nodes(self) -> List[Dict[str, Any]]:
        try:
            events = self.event_store.replay(cursor=0, limit=100_000)
        except Exception:
            return []
        nodes: Dict[str, Dict[str, Any]] = {}
        for row in events:
            projected = self._project_row(row)
            if projected is None:
                continue
            payload = projected.get("payload", {})
            node_id = payload.get("node_id") or payload.get("id") or projected.get("event_id")
            event_type = projected.get("event_type", "")
            if event_type == "NODE_CREATED" and node_id:
                nodes[node_id] = {
                    "id": node_id,
                    "type": payload.get("node_type", "unknown"),
                    "status": payload.get("status", "created"),
                    "execution_mode": projected.get("execution_mode", "real"),
                    "execution_state": projected.get("execution_state", "running"),
                    "verification_state": projected.get("verification_state", "unverified"),
                    "execution_id": projected.get("execution_id", ""),
                    "correlation_id": projected.get("correlation_id"),
                    "causation_id": projected.get("causation_id"),
                    "timestamp": projected.get("timestamp", ""),
                }
            elif event_type == "NODE_UPDATED" and node_id and node_id in nodes:
                nodes[node_id].update({
                    "status": payload.get("status", nodes[node_id].get("status", "created")),
                    "execution_state": projected.get("execution_state", nodes[node_id].get("execution_state", "running")),
                    "verification_state": projected.get("verification_state", nodes[node_id].get("verification_state", "unverified")),
                })
            elif event_type == "NODE_ARCHIVED" and node_id and node_id in nodes:
                del nodes[node_id]
        return list(nodes.values())

    async def _build_snapshot_edges(self) -> List[Dict[str, Any]]:
        try:
            events = self.event_store.replay(cursor=0, limit=100_000)
        except Exception:
            return []
        edges: List[Dict[str, Any]] = []
        seen: Set[str] = set()
        for row in events:
            projected = self._project_row(row)
            if projected is None:
                continue
            payload = projected.get("payload", {})
            event_type = projected.get("event_type", "")
            if event_type == "EDGE_CREATED":
                edge_id = payload.get("edge_id") or f"{payload.get('source_id')}->{payload.get('target_id')}"
                if edge_id not in seen:
                    seen.add(edge_id)
                    edges.append({
                        "source_id": payload.get("source_id", ""),
                        "target_id": payload.get("target_id", ""),
                        "edge_type": payload.get("edge_type", "default"),
                        "execution_id": projected.get("execution_id", ""),
                        "execution_mode": projected.get("execution_mode", "real"),
                        "verification_state": projected.get("verification_state", "unverified"),
                    })
            elif event_type == "EDGE_REMOVED":
                edge_id = payload.get("edge_id") or f"{payload.get('source_id')}->{payload.get('target_id')}"
                edges = [e for e in edges if not (
                    e.get("source_id") == payload.get("source_id") and
                    e.get("target_id") == payload.get("target_id")
                )]
        return edges

    def _project_row(self, row: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        seq = row.get("seq", 0)
        msg = EventMessage(
            topic=row.get("topic", "system"),
            payload=row.get("payload", {}),
            source=row.get("source", ""),
            priority=row.get("priority", "NORMAL"),
            timestamp=row.get("timestamp", time.time()),
            id=row.get("id", ""),
        )
        return self.projection.project(msg)

    async def _send_reconciliation(self, client_id: str) -> None:
        session = self._clients.get(client_id)
        if not session:
            return
        current_seq = self._get_current_seq()
        msg = {"type": "reconciliation", "seq": current_seq, "checksum": await self._compute_checksum(session)}
        await self._enqueue(session, msg)
        session.last_reconciliation = time.time()

    async def _compute_checksum(self, session: ClientSession) -> str:
        import hashlib
        with self._lock:
            node_ids = sorted(
                n["id"] for n in await self._build_snapshot_nodes()
            )
        return hashlib.sha256(",".join(node_ids).encode()).hexdigest()[:16]

    async def _disconnect_client(self, client_id: str, reason: str) -> None:
        session = self._clients.pop(client_id, None)
        if session:
            try:
                await session.websocket.close(1000, reason)
            except Exception:
                pass
            logger.info("Client %s disconnected: %s", client_id, reason)

    async def _enqueue(self, session: ClientSession, message: Dict[str, Any]) -> None:
        try:
            session.queue.put_nowait(message)
        except asyncio.QueueFull:
            try:
                session.queue.get_nowait()
                session.queue.put_nowait(message)
            except asyncio.QueueEmpty:
                pass

    def on_event(self, event: EventMessage) -> None:
        if not self._running or not self._loop:
            return
        projected = self.projection.project(event)
        if projected is None:
            return
        seq = projected.get("sequence_number", 0)
        with self._lock:
            for session in list(self._clients.values()):
                if session.subscribed_types and projected.get("event_type") not in session.subscribed_types:
                    continue
                if seq > 0:
                    session.last_seq = seq
                try:
                    session.queue.put_nowait(projected)
                except asyncio.QueueFull:
                    try:
                        session.queue.get_nowait()
                        session.queue.put_nowait(projected)
                    except asyncio.QueueEmpty:
                        pass

    def stop(self) -> None:
        self._running = False
        if self._loop and self._loop.is_running() and self._server is not None:
            self._loop.call_soon_threadsafe(self._server.close)  # type: ignore
        if self._thread:
            self._thread.join(timeout=5.0)
        logger.info("WebSocketAdapter stopped")

    def get_stats(self) -> Dict[str, Any]:
        with self._lock:
            return {
                "version": ADAPTER_VERSION,
                "running": self._running,
                "clients": len(self._clients),
                "host": self.host,
                "port": self.port,
                "client_details": [
                    {
                        "id": cid,
                        "connected_at": s.connected_at,
                        "last_heartbeat": s.last_heartbeat,
                        "last_seq": s.last_seq,
                        "bytes_sent": s.bytes_sent,
                        "messages_sent": s.messages_sent,
                        "queue_size": s.queue.qsize(),
                        "subscribed_types": list(s.subscribed_types) if s.subscribed_types else None,
                    }
                    for cid, s in self._clients.items()
                ],
            }
