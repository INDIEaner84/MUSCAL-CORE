import asyncio
import json
import logging
import uuid
from typing import Any, Callable, Coroutine, Dict, List, Optional

from config import (
    MUSCAL_IPC_TIMEOUT,
    MUSCAL_SOCKET_PATH,
    MUSCAL_TCP_HOST,
    MUSCAL_TCP_PORT,
)

logger = logging.getLogger(__name__)


class IPCClient:
    def __init__(
        self,
        socket_path: Optional[str] = None,
        tcp_host: str = "127.0.0.1",
        tcp_port: int = 5000,
        use_unix: bool = True,
        auto_reconnect: bool = True,
        reconnect_delay: float = 2.0,
    ) -> None:
        self.socket_path = socket_path or str(MUSCAL_SOCKET_PATH)
        self.tcp_host = tcp_host
        self.tcp_port = tcp_port
        self.use_unix = use_unix
        self.auto_reconnect = auto_reconnect
        self.reconnect_delay = reconnect_delay
        self._reader: Optional[asyncio.StreamReader] = None
        self._writer: Optional[asyncio.StreamWriter] = None
        self._connected = False
        self._event_handlers: Dict[str, List[Callable]] = {}
        self._listen_task: Optional[asyncio.Task] = None
        self._response_queue: asyncio.Queue[Dict[str, Any]] = asyncio.Queue()

    async def connect(self) -> None:
        try:
            if self.use_unix:
                self._reader, self._writer = await asyncio.open_unix_connection(
                    self.socket_path
                )
            else:
                self._reader, self._writer = await asyncio.open_connection(
                    self.tcp_host, self.tcp_port
                )

            self._connected = True
            logger.info("IPC Client connected")
            self._listen_task = asyncio.create_task(self._listen())

        except (ConnectionRefusedError, FileNotFoundError, OSError) as e:
            self._connected = False
            raise ConnectionError(f"IPC connection failed: {e}") from e

    async def disconnect(self) -> None:
        self._connected = False
        if self._listen_task:
            self._listen_task.cancel()
            try:
                await self._listen_task
            except asyncio.CancelledError:
                pass
        if self._writer:
            try:
                self._writer.close()
                await self._writer.wait_closed()
            except Exception:
                pass
        logger.info("IPC Client disconnected")

    async def send(
        self, message: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        if not self._connected:
            if self.auto_reconnect:
                try:
                    await self.connect()
                except ConnectionError:
                    return {"ok": False, "error": "Reconnect failed"}
            else:
                return {"ok": False, "error": "Not connected"}

        line = json.dumps(message, ensure_ascii=False) + "\n"
        try:
            self._writer.write(line.encode("utf-8"))
            await self._writer.drain()
        except (ConnectionResetError, BrokenPipeError, OSError) as e:
            if self.auto_reconnect:
                logger.warning("Connection lost, reconnecting...")
                try:
                    await self.connect()
                    self._writer.write(line.encode("utf-8"))
                    await self._writer.drain()
                except (ConnectionError, OSError):
                    return {"ok": False, "error": "Reconnect failed"}
            else:
                return {"ok": False, "error": str(e)}

        try:
            response = await asyncio.wait_for(
                self._response_queue.get(), timeout=float(MUSCAL_IPC_TIMEOUT)
            )
            return response
        except asyncio.TimeoutError:
            return {"ok": False, "error": f"Response timeout ({MUSCAL_IPC_TIMEOUT}s)"}

    async def register(
        self,
        agent_id: str,
        agent_type: str,
        subscribed_events: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        return await self.send({
            "type": "agent.register",
            "agent_id": agent_id,
            "agent_type": agent_type,
            "subscribed_events": subscribed_events or [],
        })

    async def emit_event(
        self,
        event_type: str,
        payload: Optional[Dict[str, Any]] = None,
        source: str = "",
    ) -> Dict[str, Any]:
        return await self.send({
            "type": "event.emit",
            "event_type": event_type,
            "payload": payload or {},
            "source": source,
        })

    async def submit_task(
        self,
        agent_id: str,
        payload: Dict[str, Any],
        priority: str = "normal",
        timeout: float = 30.0,
    ) -> Dict[str, Any]:
        return await self.send({
            "type": "task.submit",
            "agent_id": agent_id,
            "payload": payload,
            "priority": priority,
            "timeout": timeout,
        })

    async def heartbeat(self, agent_id: str) -> Dict[str, Any]:
        return await self.send({
            "type": "heartbeat",
            "agent_id": agent_id,
        })

    def on_event(self, event_type: str, handler: Callable) -> None:
        if event_type not in self._event_handlers:
            self._event_handlers[event_type] = []
        self._event_handlers[event_type].append(handler)

    @property
    def is_connected(self) -> bool:
        return self._connected

    async def _listen(self) -> None:
        try:
            while self._connected and self._reader:
                line = await self._reader.readline()
                if not line:
                    break

                line_str = line.decode("utf-8").strip()
                if not line_str:
                    continue

                try:
                    data = json.loads(line_str)
                except json.JSONDecodeError:
                    continue

                msg_type = data.get("type", "")
                if msg_type.startswith("event."):
                    await self._handle_event_push(data)
                else:
                    await self._response_queue.put(data)

        except asyncio.CancelledError:
            pass
        except (ConnectionResetError, OSError):
            self._connected = False
            logger.warning("IPC listen: connection lost")

    async def _handle_event_push(self, data: Dict[str, Any]) -> None:
        event_type = data.get("event_type", data.get("type", ""))
        for pattern, handlers in self._event_handlers.items():
            if self._matches(pattern, event_type):
                for handler in handlers:
                    try:
                        if asyncio.iscoroutinefunction(handler):
                            await handler(data)
                        else:
                            handler(data)
                    except Exception as e:
                        logger.error(f"Event handler error: {e}")

    @staticmethod
    def _matches(pattern: str, event_type: str) -> bool:
        if pattern == "*":
            return True
        if "*" not in pattern:
            return pattern == event_type
        prefix = pattern.replace("*", "")
        return event_type.startswith(prefix)
