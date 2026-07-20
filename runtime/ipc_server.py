import asyncio
import json
import logging
import os
from typing import Any, Callable, Coroutine, Dict, Optional

from config import MUSCAL_SOCKET_PATH, MUSCAL_TCP_HOST, MUSCAL_TCP_PORT

logger = logging.getLogger(__name__)

MessageHandler = Callable[
    [Dict[str, Any]], Coroutine[Any, Any, Dict[str, Any]]
]


class IPCServer:
    def __init__(
        self,
        socket_path: Optional[str] = None,
        tcp_host: str = "127.0.0.1",
        tcp_port: int = 5000,
        use_unix: bool = True,
    ) -> None:
        self.socket_path = socket_path or str(MUSCAL_SOCKET_PATH)
        self.tcp_host = tcp_host
        self.tcp_port = tcp_port
        self.use_unix = use_unix
        self._server: Optional[asyncio.AbstractServer] = None
        self._handlers: Dict[str, MessageHandler] = {}
        self._running = False
        self._connections: set[asyncio.StreamWriter] = set()

    def register_handler(
        self, message_type: str, handler: MessageHandler
    ) -> None:
        self._handlers[message_type] = handler
        logger.debug(f"IPC handler registered: {message_type}")

    async def start(self) -> None:
        if self.use_unix:
            await self._start_unix()
        else:
            await self._start_tcp()

        self._running = True
        transport = "Unix" if self.use_unix else "TCP"
        addr = (
            self.socket_path
            if self.use_unix
            else f"{self.tcp_host}:{self.tcp_port}"
        )
        logger.info(f"IPC Server started ({transport}): {addr}")

    async def _start_unix(self) -> None:
        if os.path.exists(self.socket_path):
            os.unlink(self.socket_path)
        os.makedirs(
            os.path.dirname(self.socket_path) or ".", exist_ok=True
        )
        self._server = await asyncio.start_unix_server(
            self._handle_client,
            path=self.socket_path,
        )

    async def _start_tcp(self) -> None:
        self._server = await asyncio.start_server(
            self._handle_client,
            host=self.tcp_host,
            port=self.tcp_port,
        )

    async def stop(self) -> None:
        self._running = False
        for writer in list(self._connections):
            try:
                writer.close()
                await writer.wait_closed()
            except Exception:
                pass
        self._connections.clear()
        if self._server:
            self._server.close()
            await self._server.wait_closed()
        if self.use_unix and os.path.exists(self.socket_path):
            os.unlink(self.socket_path)
        logger.info("IPC Server stopped")

    async def broadcast(self, message: Dict[str, Any]) -> None:
        for writer in list(self._connections):
            try:
                await self._send(writer, message)
            except Exception:
                self._connections.discard(writer)

    def is_running(self) -> bool:
        return self._running

    @property
    def connected_clients(self) -> int:
        return len(self._connections)

    async def _handle_client(
        self,
        reader: asyncio.StreamReader,
        writer: asyncio.StreamWriter,
    ) -> None:
        addr = writer.get_extra_info("peername") or "unix"
        self._connections.add(writer)
        logger.debug(f"Client connected: {addr}")

        try:
            while self._running:
                line = await reader.readline()
                if not line:
                    break

                line_str = line.decode("utf-8").strip()
                if not line_str:
                    continue

                try:
                    request = json.loads(line_str)
                except json.JSONDecodeError:
                    response = {"ok": False, "error": "Invalid JSON"}
                    await self._send(writer, response)
                    continue

                response = await self._dispatch(request)
                await self._send(writer, response)

        except asyncio.CancelledError:
            pass
        except ConnectionResetError:
            logger.debug(f"Client disconnected: {addr}")
        except Exception as e:
            logger.error(f"Client error ({addr}): {e}")
        finally:
            self._connections.discard(writer)
            try:
                writer.close()
                await writer.wait_closed()
            except Exception:
                pass
            logger.debug(f"Client disconnected: {addr}")

    async def _dispatch(
        self, request: Dict[str, Any]
    ) -> Dict[str, Any]:
        msg_type = request.get("type", "")

        if not msg_type:
            return {"ok": False, "error": "Missing 'type' field"}

        handler = self._handlers.get(msg_type)
        if not handler:
            return {"ok": False, "error": f"Unknown message type: {msg_type}"}

        try:
            result = await handler(request)
            return {"ok": True, "data": result}
        except Exception as e:
            logger.error(f"Handler error for '{msg_type}': {e}")
            return {"ok": False, "error": str(e)}

    @staticmethod
    async def _send(
        writer: asyncio.StreamWriter, data: Dict[str, Any]
    ) -> None:
        line = json.dumps(data, ensure_ascii=False) + "\n"
        writer.write(line.encode("utf-8"))
        await writer.drain()
