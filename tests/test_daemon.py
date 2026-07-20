import asyncio
import os

import pytest

from runtime.daemon import MUSCALDaemon
from runtime.ipc_client import IPCClient


@pytest.mark.asyncio
async def test_daemon_init(tmp_socket_path):
    daemon = MUSCALDaemon(socket_path=tmp_socket_path)
    assert daemon._running is False
    assert daemon.get_uptime() == 0.0


@pytest.mark.asyncio
async def test_daemon_start_stop(tmp_socket_path):
    daemon = MUSCALDaemon(socket_path=tmp_socket_path)
    await daemon.start()
    assert await daemon.is_running() is True
    assert daemon.get_uptime() >= 0

    await daemon.stop()
    assert await daemon.is_running() is False


@pytest.mark.asyncio
async def test_daemon_start_idempotent(tmp_socket_path):
    daemon = MUSCALDaemon(socket_path=tmp_socket_path)
    await daemon.start()
    await daemon.start()
    assert await daemon.is_running() is True
    await daemon.stop()


@pytest.mark.asyncio
async def test_daemon_stop_idempotent(tmp_socket_path):
    daemon = MUSCALDaemon(socket_path=tmp_socket_path)
    await daemon.start()
    await daemon.stop()
    await daemon.stop()
    assert await daemon.is_running() is False


@pytest.mark.asyncio
async def test_daemon_uptime(tmp_socket_path):
    daemon = MUSCALDaemon(socket_path=tmp_socket_path)
    assert daemon.get_uptime() == 0.0
    await daemon.start()
    uptime = daemon.get_uptime()
    assert uptime > 0
    await asyncio.sleep(0.1)
    assert daemon.get_uptime() > uptime
    await daemon.stop()


@pytest.mark.asyncio
async def test_daemon_pid_file(tmp_socket_path):
    pid_file = tmp_socket_path.with_suffix(".pid")
    daemon = MUSCALDaemon(socket_path=tmp_socket_path, pid_file=str(pid_file))
    await daemon.start()
    assert pid_file.exists()
    pid = int(pid_file.read_text())
    assert pid == os.getpid()
    await daemon.stop()
    assert not pid_file.exists()


@pytest.mark.asyncio
async def test_daemon_shutdown_request(tmp_socket_path):
    daemon = MUSCALDaemon(socket_path=tmp_socket_path)
    await daemon.start()
    assert await daemon.is_running() is True

    daemon.request_shutdown()
    await daemon.stop()
    assert await daemon.is_running() is False


@pytest.mark.asyncio
async def test_daemon_ipc_status_handler(tmp_socket_path):
    daemon = MUSCALDaemon(socket_path=tmp_socket_path)
    await daemon.start()

    client = IPCClient(socket_path=tmp_socket_path)
    await client.connect()

    response = await client.send({"type": "daemon.status"})
    assert response["ok"] is True
    assert "daemon" in response["data"]
    assert response["data"]["daemon"]["running"] is True
    assert response["data"]["daemon"]["pid"] == os.getpid()

    await client.disconnect()
    await daemon.stop()


@pytest.mark.asyncio
async def test_daemon_ipc_spawn_handler(tmp_socket_path):
    daemon = MUSCALDaemon(socket_path=tmp_socket_path)
    await daemon.start()

    client = IPCClient(socket_path=tmp_socket_path)
    await client.connect()

    response = await client.send({
        "type": "daemon.spawn",
        "agent_id": "test-agent",
        "command": ["echo", "hello"],
    })

    assert response["ok"] is True
    assert response["data"]["agent_id"] == "test-agent"
    assert response["data"]["pid"] > 0

    await client.disconnect()
    await daemon.stop()


@pytest.mark.asyncio
async def test_daemon_ipc_heartbeat_handler(tmp_socket_path):
    daemon = MUSCALDaemon(socket_path=tmp_socket_path)
    await daemon.start()

    client = IPCClient(socket_path=tmp_socket_path)
    await client.connect()

    response = await client.send({
        "type": "heartbeat",
        "agent_id": "test-agent",
    })

    assert response["ok"] is True

    await client.disconnect()
    await daemon.stop()


@pytest.mark.asyncio
async def test_daemon_ipc_kill_handler(tmp_socket_path):
    daemon = MUSCALDaemon(socket_path=tmp_socket_path)
    await daemon.start()

    client = IPCClient(socket_path=tmp_socket_path)
    await client.connect()

    await client.send({
        "type": "daemon.spawn",
        "agent_id": "test-agent",
        "command": ["echo", "hello"],
    })

    response = await client.send({
        "type": "daemon.kill",
        "agent_id": "test-agent",
    })

    assert response["ok"] is True

    await client.disconnect()
    await daemon.stop()
