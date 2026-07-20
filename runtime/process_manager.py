import asyncio
import logging
import os
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

from config import MUSCAL_MAX_AGENT_RESTARTS

logger = logging.getLogger(__name__)


class AgentState(str, Enum):
    STARTING = "starting"
    RUNNING = "running"
    STOPPING = "stopping"
    STOPPED = "stopped"
    CRASHED = "crashed"


@dataclass
class ManagedAgent:
    agent_id: str
    command: List[str]
    process: Optional[asyncio.subprocess.Process] = None
    state: AgentState = AgentState.STARTING
    pid: int = 0
    created_at: str = ""
    started_at: str = ""
    stopped_at: str = ""
    restart_count: int = 0
    last_heartbeat: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)


class ProcessManager:
    def __init__(
        self,
        socket_path: Optional[str] = None,
        heartbeat_timeout: float = 30.0,
        max_restarts: Optional[int] = None,
    ) -> None:
        from config import MUSCAL_SOCKET_PATH

        self.socket_path = socket_path or str(MUSCAL_SOCKET_PATH)
        self.heartbeat_timeout = heartbeat_timeout
        self.max_restarts = max_restarts if max_restarts is not None else int(MUSCAL_MAX_AGENT_RESTARTS)
        self._agents: Dict[str, ManagedAgent] = {}
        self._monitor_task: Optional[asyncio.Task] = None
        self._running = False
        self._lock = asyncio.Lock()
        self._start_time: float = 0.0

    async def start_monitor(self) -> None:
        self._running = True
        self._start_time = time.time()
        self._monitor_task = asyncio.create_task(self._monitor_loop())
        logger.info("Process Manager monitor started")

    async def stop_monitor(self) -> None:
        self._running = False
        if self._monitor_task:
            self._monitor_task.cancel()
            try:
                await self._monitor_task
            except asyncio.CancelledError:
                pass
        logger.info("Process Manager monitor stopped")

    async def spawn_agent(
        self,
        agent_id: str,
        command: List[str],
        env: Optional[Dict[str, str]] = None,
        cwd: Optional[str] = None,
    ) -> int:
        async with self._lock:
            if agent_id in self._agents:
                existing = self._agents[agent_id]
                if existing.state == AgentState.RUNNING:
                    raise ValueError(f"Agent '{agent_id}' is already running")

            process_env = os.environ.copy()
            if env:
                process_env.update(env)

            process = await asyncio.create_subprocess_exec(
                *command,
                env=process_env,
                cwd=cwd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            now = datetime.now(timezone.utc).isoformat()
            old_restart_count = (
                self._agents[agent_id].restart_count
                if agent_id in self._agents
                else 0
            )

            managed = ManagedAgent(
                agent_id=agent_id,
                command=command,
                process=process,
                state=AgentState.RUNNING,
                pid=process.pid,
                created_at=now,
                started_at=now,
                restart_count=old_restart_count,
                last_heartbeat=now,
            )
            self._agents[agent_id] = managed

        logger.info(f"Agent spawned: {agent_id} (PID {process.pid})")
        asyncio.create_task(self._read_output(managed))
        return process.pid

    async def shutdown_agent(self, agent_id: str, timeout: float = 5.0) -> bool:
        managed = self._agents.get(agent_id)
        if not managed or managed.process is None:
            return False

        managed.state = AgentState.STOPPING
        try:
            managed.process.terminate()
            try:
                await asyncio.wait_for(managed.process.wait(), timeout=timeout)
            except asyncio.TimeoutError:
                managed.process.kill()
                await managed.process.wait()
            managed.state = AgentState.STOPPED
            managed.stopped_at = datetime.now(timezone.utc).isoformat()
            logger.info(f"Agent stopped: {agent_id}")
            return True
        except ProcessLookupError:
            managed.state = AgentState.STOPPED
            managed.stopped_at = datetime.now(timezone.utc).isoformat()
            return True

    async def shutdown_all(self) -> None:
        logger.info("Shutting down all agents...")
        for agent_id in list(self._agents.keys()):
            await self.shutdown_agent(agent_id)
        async with self._lock:
            self._agents.clear()
        logger.info("All agents stopped")

    async def restart_agent(self, agent_id: str) -> Optional[int]:
        managed = self._agents.get(agent_id)
        if not managed:
            return None

        if managed.restart_count >= self.max_restarts:
            logger.error(
                f"Agent '{agent_id}' exceeded max restarts ({self.max_restarts})"
            )
            managed.state = AgentState.CRASHED
            return None

        await self.shutdown_agent(agent_id)
        managed.restart_count += 1
        return await self.spawn_agent(
            agent_id=agent_id,
            command=managed.command,
        )

    def get_agent_pid(self, agent_id: str) -> Optional[int]:
        managed = self._agents.get(agent_id)
        if managed and managed.process:
            return managed.process.pid
        if managed and managed.pid:
            return managed.pid
        return None

    def get_status(self, agent_id: str) -> Optional[str]:
        managed = self._agents.get(agent_id)
        return managed.state.value if managed else None

    def list_agents(self) -> List[Dict[str, Any]]:
        return [
            {
                "agent_id": a.agent_id,
                "state": a.state.value,
                "pid": a.pid,
                "restart_count": a.restart_count,
                "last_heartbeat": a.last_heartbeat,
                "created_at": a.created_at,
                "started_at": a.started_at,
                "stopped_at": a.stopped_at,
            }
            for a in self._agents.values()
        ]

    def get_agent(self, agent_id: str) -> Optional[ManagedAgent]:
        return self._agents.get(agent_id)

    def get_all_agents(self) -> List[ManagedAgent]:
        return list(self._agents.values())

    def update_heartbeat(self, agent_id: str) -> None:
        managed = self._agents.get(agent_id)
        if managed:
            managed.last_heartbeat = datetime.now(timezone.utc).isoformat()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "agents": {
                aid: {
                    "agent_id": a.agent_id,
                    "state": a.state.value,
                    "pid": a.pid,
                    "restart_count": a.restart_count,
                    "last_heartbeat": a.last_heartbeat,
                    "started_at": a.started_at,
                }
                for aid, a in self._agents.items()
            },
            "count": len(self._agents),
            "running": sum(
                1 for a in self._agents.values() if a.state == AgentState.RUNNING
            ),
        }

    async def _monitor_loop(self) -> None:
        while self._running:
            try:
                now = datetime.now(timezone.utc)
                for agent_id, managed in list(self._agents.items()):
                    if managed.state != AgentState.RUNNING:
                        continue
                    if managed.process is None:
                        continue
                    if managed.process.returncode is not None:
                        managed.state = AgentState.CRASHED
                        logger.warning(
                            f"Agent '{agent_id}' crashed "
                            f"(exit code: {managed.process.returncode})"
                        )
                        asyncio.create_task(self._handle_crash(agent_id))
                        continue
                    if managed.last_heartbeat:
                        try:
                            last_hb = datetime.fromisoformat(managed.last_heartbeat)
                            elapsed = (now - last_hb).total_seconds()
                            if elapsed > self.heartbeat_timeout:
                                logger.warning(
                                    f"Agent '{agent_id}' heartbeat timeout "
                                    f"({elapsed:.1f}s)"
                                )
                                asyncio.create_task(
                                    self._handle_crash(agent_id)
                                )
                        except ValueError:
                            pass
            except Exception as e:
                logger.error(f"Monitor error: {e}")
            await asyncio.sleep(5)

    async def _handle_crash(self, agent_id: str) -> None:
        try:
            await self.restart_agent(agent_id)
        except Exception as e:
            logger.error(f"Crash handler error for '{agent_id}': {e}")

    async def _read_output(self, managed: ManagedAgent) -> None:
        agent_id = managed.agent_id
        try:
            if managed.process and managed.process.stdout:
                while True:
                    line = await managed.process.stdout.readline()
                    if not line:
                        break
                    text = line.decode("utf-8").rstrip()
                    if text:
                        logger.info(f"[{agent_id}] {text}")
        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.debug(f"Output reader for {agent_id}: {e}")
