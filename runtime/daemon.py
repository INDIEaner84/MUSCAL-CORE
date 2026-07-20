import asyncio
import logging
import os
import signal
import time
from typing import Any, Dict, Optional

from config import MUSCAL_SOCKET_PATH

from runtime.ipc_server import IPCServer
from runtime.process_manager import ProcessManager

logger = logging.getLogger(__name__)

PID_FILE = "/tmp/muscal_daemon.pid"


class MUSCALDaemon:
    def __init__(
        self,
        socket_path: Optional[str] = None,
        pid_file: str = PID_FILE,
    ) -> None:
        self.socket_path = socket_path or str(MUSCAL_SOCKET_PATH)
        self.pid_file = pid_file

        self.ipc = IPCServer(socket_path=self.socket_path)
        self.process_manager = ProcessManager(socket_path=self.socket_path)

        self._running = False
        self._start_time: float = 0.0
        self._shutdown_event = asyncio.Event()

    async def start(self) -> None:
        if self._running:
            return

        self._write_pid()
        self._register_ipc_handlers()
        await self.ipc.start()
        await self.process_manager.start_monitor()

        self._running = True
        self._start_time = time.time()
        logger.info(f"MUSCAL Daemon started (PID {os.getpid()})")

        try:
            self._setup_signals()
        except RuntimeError:
            pass

    async def stop(self) -> None:
        if not self._running:
            return
        self._running = False
        self._shutdown_event.set()
        logger.info("Stopping MUSCAL Daemon...")
        await self.process_manager.shutdown_all()
        await self.process_manager.stop_monitor()
        await self.ipc.stop()
        self._remove_pid()
        logger.info("MUSCAL Daemon stopped")

    async def wait_for_shutdown(self) -> None:
        await self._shutdown_event.wait()
        await self.stop()

    def request_shutdown(self) -> None:
        self._shutdown_event.set()

    async def is_running(self) -> bool:
        return self._running

    def get_uptime(self) -> float:
        if self._start_time == 0.0:
            return 0.0
        return time.time() - self._start_time

    def _register_ipc_handlers(self) -> None:
        self.ipc.register_handler("daemon.spawn", self._handle_spawn)
        self.ipc.register_handler("daemon.kill", self._handle_kill)
        self.ipc.register_handler("heartbeat", self._handle_heartbeat)
        self.ipc.register_handler("daemon.status", self._handle_status)

    def _setup_signals(self) -> None:
        loop = asyncio.get_running_loop()
        for sig in (signal.SIGTERM, signal.SIGINT):
            loop.add_signal_handler(sig, self.request_shutdown)

    def _write_pid(self) -> None:
        try:
            os.makedirs(os.path.dirname(self.pid_file) or ".", exist_ok=True)
            with open(self.pid_file, "w") as f:
                f.write(str(os.getpid()))
            logger.debug(f"PID file written: {self.pid_file}")
        except OSError as e:
            logger.warning(f"Could not write PID file: {e}")

    def _remove_pid(self) -> None:
        try:
            if os.path.exists(self.pid_file):
                os.unlink(self.pid_file)
                logger.debug(f"PID file removed: {self.pid_file}")
        except OSError as e:
            logger.warning(f"Could not remove PID file: {e}")

    async def _handle_spawn(
        self, msg: Dict[str, Any]
    ) -> Dict[str, Any]:
        agent_id = msg.get("agent_id", "")
        command = msg.get("command", [])
        if not agent_id or not command:
            return {"ok": False, "error": "Missing agent_id or command"}
        try:
            pid = await self.process_manager.spawn_agent(
                agent_id=agent_id,
                command=command,
                env=msg.get("env"),
                cwd=msg.get("cwd"),
            )
            return {"ok": True, "agent_id": agent_id, "pid": pid}
        except Exception as e:
            logger.error(f"Spawn failed: {e}")
            return {"ok": False, "error": str(e)}

    async def _handle_kill(
        self, msg: Dict[str, Any]
    ) -> Dict[str, Any]:
        agent_id = msg.get("agent_id", "")
        if not agent_id:
            return {"ok": False, "error": "Missing agent_id"}
        success = await self.process_manager.shutdown_agent(agent_id)
        return {"ok": success, "agent_id": agent_id}

    async def _handle_heartbeat(
        self, msg: Dict[str, Any]
    ) -> Dict[str, Any]:
        agent_id = msg.get("agent_id", "")
        if agent_id:
            self.process_manager.update_heartbeat(agent_id)
        return {"ok": True, "agent_id": agent_id}

    async def _handle_status(
        self, msg: Dict[str, Any]
    ) -> Dict[str, Any]:
        return {
            "daemon": {
                "pid": os.getpid(),
                "uptime": self.get_uptime(),
                "running": self._running,
            },
            "process_manager": self.process_manager.to_dict(),
            "ipc": {
                "connected_clients": self.ipc.connected_clients,
                "running": self.ipc.is_running(),
            },
        }
