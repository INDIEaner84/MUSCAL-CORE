"""End-to-end integration test for MUSCAL Phase 1A runtime.

Full lifecycle: start Daemon -> connect IPC client -> send messages
-> verify handler execution -> graceful shutdown.
"""

import asyncio
import json
import os

import pytest

from runtime.daemon import MUSCALDaemon
from runtime.ipc_client import IPCClient


@pytest.mark.asyncio
async def test_full_runtime_lifecycle(tmp_socket_path):
    """Start Daemon, connect client, exchange messages, verify clean shutdown."""
    daemon = MUSCALDaemon(socket_path=tmp_socket_path)

    # --- Start ---
    await daemon.start()
    assert await daemon.is_running() is True

    # IPC server is active — socket file created
    assert os.path.exists(tmp_socket_path), "Socket file should exist"

    # --- Connect IPC client ---
    client = IPCClient(socket_path=tmp_socket_path)
    await client.connect()
    assert client.is_connected is True

    # --- Send status request ---
    response = await client.send({"type": "daemon.status"})

    # Verify response format
    assert response["ok"] is True
    assert "data" in response
    data = response["data"]

    # Verify daemon section
    assert "daemon" in data
    assert data["daemon"]["running"] is True
    assert data["daemon"]["pid"] == os.getpid()
    assert data["daemon"]["uptime"] > 0

    # Verify process manager section
    assert "process_manager" in data
    assert data["process_manager"]["count"] == 0
    assert data["process_manager"]["running"] == 0

    # Verify IPC section
    assert "ipc" in data
    assert data["ipc"]["running"] is True
    assert data["ipc"]["connected_clients"] >= 1

    # --- Spawn an agent via daemon handler ---
    spawn_response = await client.send({
        "type": "daemon.spawn",
        "agent_id": "integration-test-agent",
        "command": ["echo", "hello"],
    })

    assert spawn_response["ok"] is True
    assert spawn_response["data"]["agent_id"] == "integration-test-agent"
    assert spawn_response["data"]["pid"] > 0

    # Verify agent appears in status
    status = await client.send({"type": "daemon.status"})
    assert status["data"]["process_manager"]["count"] == 1

    # --- Send heartbeat ---
    hb_response = await client.send({
        "type": "heartbeat",
        "agent_id": "integration-test-agent",
    })
    assert hb_response["ok"] is True

    # --- Kill the agent ---
    kill_response = await client.send({
        "type": "daemon.kill",
        "agent_id": "integration-test-agent",
    })
    assert kill_response["ok"] is True

    # --- Disconnect client ---
    await client.disconnect()
    assert client.is_connected is False

    # Yield to let server process disconnection
    await asyncio.sleep(0.05)

    # --- Verify IPC connection count drops ---
    assert daemon.ipc.connected_clients == 0

    # --- Stop daemon ---
    await daemon.stop()
    assert await daemon.is_running() is False

    # --- Verify cleanup ---
    assert not os.path.exists(tmp_socket_path), "Socket should be removed on stop"


@pytest.mark.asyncio
async def test_runtime_response_format(tmp_socket_path):
    """Verify response format for all daemon handlers."""
    daemon = MUSCALDaemon(socket_path=tmp_socket_path)
    await daemon.start()

    client = IPCClient(socket_path=tmp_socket_path)
    await client.connect()

    test_cases = [
        ("daemon.status", {}, True),
        ("daemon.spawn", {"agent_id": "a", "command": ["echo", "x"]}, True),
        ("heartbeat", {"agent_id": "a"}, True),
        ("daemon.kill", {"agent_id": "a"}, True),
        ("nonexistent", {}, False),
    ]

    for msg_type, payload, expect_ok in test_cases:
        msg = {"type": msg_type, **payload}
        response = await client.send(msg)
        assert "ok" in response, f"{msg_type}: missing 'ok' field"
        assert response["ok"] is expect_ok, (
            f"{msg_type}: expected ok={expect_ok}, got {response['ok']}"
        )
        if expect_ok:
            assert "data" in response, f"{msg_type}: missing 'data' field"

    await client.disconnect()
    await daemon.stop()


@pytest.mark.asyncio
async def test_runtime_concurrent_clients(tmp_socket_path):
    """Multiple clients connecting simultaneously to the daemon."""
    daemon = MUSCALDaemon(socket_path=tmp_socket_path)
    await daemon.start()

    async def client_session(client_id: int) -> dict:
        c = IPCClient(socket_path=tmp_socket_path)
        await c.connect()
        resp = await c.send({"type": "daemon.status"})
        await c.disconnect()
        return {"client_id": client_id, "ok": resp["ok"]}

    results = await asyncio.gather(*[client_session(i) for i in range(5)])
    assert all(r["ok"] for r in results)
    assert len(results) == 5

    await daemon.stop()


@pytest.mark.asyncio
async def test_runtime_start_stop_idempotent(tmp_socket_path):
    """Start/stop multiple times — no resource leaks."""
    for i in range(3):
        d = MUSCALDaemon(socket_path=tmp_socket_path)
        await d.start()
        assert await d.is_running() is True
        await asyncio.sleep(0.05)
        await d.stop()
        assert await d.is_running() is False
