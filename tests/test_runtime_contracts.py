"""Runtime protocol compliance tests.

Verifies that Batch B implementation classes meet Batch A protocol contracts
and expose required public API methods.
"""

import inspect
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from interfaces import (
    DaemonProvider,
    IPCClientProvider,
    IPCServerProvider,
    ProcessManagerProvider,
)
from runtime.daemon import MUSCALDaemon
from runtime.ipc_client import IPCClient
from runtime.ipc_server import IPCServer
from runtime.process_manager import (
    AgentState,
    ManagedAgent,
    ProcessManager,
)


def _get_protocol_attrs(protocol: type) -> set[str]:
    return {
        name
        for name in protocol.__dict__
        if not name.startswith("_") and name != "__abstractmethods__"
    }


# ---------------------------------------------------------------------------
# ProcessManagerProvider compliance
# ---------------------------------------------------------------------------


class TestProcessManagerContract:
    def test_implements_protocol_methods(self):
        required = _get_protocol_attrs(ProcessManagerProvider)
        for name in required:
            assert hasattr(ProcessManager, name), (
                f"ProcessManager missing protocol method: {name}"
            )

    def test_spawn_agent_is_async(self):
        assert inspect.iscoroutinefunction(ProcessManager.spawn_agent)

    def test_shutdown_agent_is_async(self):
        assert inspect.iscoroutinefunction(ProcessManager.shutdown_agent)

    def test_shutdown_all_is_async(self):
        assert inspect.iscoroutinefunction(ProcessManager.shutdown_all)

    def test_get_agent_pid_is_sync(self):
        assert not inspect.iscoroutinefunction(ProcessManager.get_agent_pid)

    def test_list_agents_is_sync(self):
        assert not inspect.iscoroutinefunction(ProcessManager.list_agents)

    def test_get_status_is_sync(self):
        assert not inspect.iscoroutinefunction(ProcessManager.get_status)

    def test_public_api(self):
        """Additional public methods beyond the protocol."""
        for name in ("get_agent", "get_all_agents", "to_dict", "restart_agent",
                      "start_monitor", "stop_monitor", "update_heartbeat"):
            assert hasattr(ProcessManager, name), f"Missing public method: {name}"

    def test_instantiation(self):
        pm = ProcessManager()
        assert isinstance(pm, ProcessManager)


# ---------------------------------------------------------------------------
# IPCServerProvider compliance
# ---------------------------------------------------------------------------


class TestIPCServerContract:
    def test_implements_protocol_methods(self):
        required = _get_protocol_attrs(IPCServerProvider)
        for name in required:
            assert hasattr(IPCServer, name), (
                f"IPCServer missing protocol method: {name}"
            )

    def test_start_is_async(self):
        assert inspect.iscoroutinefunction(IPCServer.start)

    def test_stop_is_async(self):
        assert inspect.iscoroutinefunction(IPCServer.stop)

    def test_broadcast_is_async(self):
        assert inspect.iscoroutinefunction(IPCServer.broadcast)

    def test_is_running_is_sync(self):
        assert not inspect.iscoroutinefunction(IPCServer.is_running)

    def test_connected_clients_is_property(self):
        prop = IPCServer.__dict__.get("connected_clients")
        assert isinstance(prop, property)

    def test_instantiation(self):
        server = IPCServer()
        assert isinstance(server, IPCServer)


# ---------------------------------------------------------------------------
# IPCClientProvider compliance
# ---------------------------------------------------------------------------


class TestIPCClientContract:
    def test_implements_protocol_methods(self):
        required = _get_protocol_attrs(IPCClientProvider)
        for name in required:
            assert hasattr(IPCClient, name), (
                f"IPCClient missing protocol method: {name}"
            )

    def test_connect_is_async(self):
        assert inspect.iscoroutinefunction(IPCClient.connect)

    def test_disconnect_is_async(self):
        assert inspect.iscoroutinefunction(IPCClient.disconnect)

    def test_send_is_async(self):
        assert inspect.iscoroutinefunction(IPCClient.send)

    def test_is_connected_is_property(self):
        assert "is_connected" in dir(IPCClient)

    def test_instantiation(self):
        client = IPCClient()
        assert isinstance(client, IPCClient)

    def test_additional_methods(self):
        for name in ("register", "emit_event", "submit_task", "heartbeat",
                      "on_event"):
            assert hasattr(IPCClient, name), f"Missing method: {name}"


# ---------------------------------------------------------------------------
# DaemonProvider compliance
# ---------------------------------------------------------------------------


class TestDaemonContract:
    def test_implements_protocol_methods(self):
        required = _get_protocol_attrs(DaemonProvider)
        for name in required:
            assert hasattr(MUSCALDaemon, name), (
                f"MUSCALDaemon missing protocol method: {name}"
            )

    def test_start_is_async(self):
        assert inspect.iscoroutinefunction(MUSCALDaemon.start)

    def test_stop_is_async(self):
        assert inspect.iscoroutinefunction(MUSCALDaemon.stop)

    def test_is_running_is_async(self):
        assert inspect.iscoroutinefunction(MUSCALDaemon.is_running)

    def test_get_uptime_is_sync(self):
        assert not inspect.iscoroutinefunction(MUSCALDaemon.get_uptime)

    def test_instantiation(self):
        daemon = MUSCALDaemon()
        assert isinstance(daemon, MUSCALDaemon)

    def test_additional_methods(self):
        for name in ("request_shutdown", "wait_for_shutdown"):
            assert hasattr(MUSCALDaemon, name), f"Missing method: {name}"


# ---------------------------------------------------------------------------
# ManagedAgent contract
# ---------------------------------------------------------------------------


class TestManagedAgentContract:
    def test_dataclass_fields(self):
        expected = {"agent_id", "command", "process", "state", "pid",
                     "created_at", "started_at", "stopped_at",
                     "restart_count", "last_heartbeat", "metadata"}
        actual = {f.name for f in ManagedAgent.__dataclass_fields__.values()}
        missing = expected - actual
        assert not missing, f"ManagedAgent missing fields: {missing}"

    def test_agent_state_enum(self):
        assert AgentState.STARTING.value == "starting"
        assert AgentState.RUNNING.value == "running"
        assert AgentState.STOPPING.value == "stopping"
        assert AgentState.STOPPED.value == "stopped"
        assert AgentState.CRASHED.value == "crashed"
