import asyncio
import json

import pytest

from runtime.ipc_client import IPCClient
from runtime.ipc_server import IPCServer


@pytest.mark.asyncio
async def test_server_start_stop_unix(tmp_socket_path):
    server = IPCServer(socket_path=tmp_socket_path)
    await server.start()
    assert server.is_running() is True
    assert server.connected_clients == 0
    await server.stop()
    assert server.is_running() is False


@pytest.mark.asyncio
async def test_handler_registration(tmp_socket_path):
    server = IPCServer(socket_path=tmp_socket_path)

    async def handler(msg):
        return {"echo": msg.get("data", {})}

    server.register_handler("echo", handler)
    assert "echo" in server._handlers

    await server.stop()


@pytest.mark.asyncio
async def test_dispatch_valid_message(tmp_socket_path):
    server = IPCServer(socket_path=tmp_socket_path)
    await server.start()

    async def echo_handler(msg):
        return {"echo": msg.get("data", {})}

    server.register_handler("echo", echo_handler)

    client = IPCClient(socket_path=tmp_socket_path)
    await client.connect()

    response = await client.send({
        "type": "echo",
        "data": {"hello": "world"},
    })

    assert response["ok"] is True
    assert response["data"]["echo"]["hello"] == "world"

    await client.disconnect()
    await server.stop()


@pytest.mark.asyncio
async def test_dispatch_missing_type(tmp_socket_path):
    server = IPCServer(socket_path=tmp_socket_path)
    await server.start()

    client = IPCClient(socket_path=tmp_socket_path)
    await client.connect()

    response = await client.send({"data": {}})

    assert response["ok"] is False
    assert "Missing 'type' field" in response["error"]

    await client.disconnect()
    await server.stop()


@pytest.mark.asyncio
async def test_dispatch_unknown_type(tmp_socket_path):
    server = IPCServer(socket_path=tmp_socket_path)
    await server.start()

    client = IPCClient(socket_path=tmp_socket_path)
    await client.connect()

    response = await client.send({"type": "nonexistent"})

    assert response["ok"] is False
    assert "Unknown message type" in response["error"]

    await client.disconnect()
    await server.stop()


@pytest.mark.asyncio
async def test_dispatch_handler_exception(tmp_socket_path):
    server = IPCServer(socket_path=tmp_socket_path)
    await server.start()

    async def failing_handler(msg):
        raise RuntimeError("handler crashed")

    server.register_handler("fail", failing_handler)

    client = IPCClient(socket_path=tmp_socket_path)
    await client.connect()

    response = await client.send({"type": "fail"})

    assert response["ok"] is False
    assert response["error"] == "handler crashed"

    await client.disconnect()
    await server.stop()


@pytest.mark.asyncio
async def test_client_connect_disconnect(tmp_socket_path):
    server = IPCServer(socket_path=tmp_socket_path)
    await server.start()

    client = IPCClient(socket_path=tmp_socket_path)
    await client.connect()
    assert client.is_connected is True

    await client.disconnect()
    assert client.is_connected is False

    await server.stop()


@pytest.mark.asyncio
async def test_client_send_without_connect(tmp_socket_path):
    server = IPCServer(socket_path=tmp_socket_path)
    await server.start()

    client = IPCClient(socket_path=tmp_socket_path, auto_reconnect=False)

    response = await client.send({"type": "echo", "data": {}})
    assert response["ok"] is False
    assert "Not connected" in response["error"]

    await server.stop()


@pytest.mark.asyncio
async def test_broadcast(tmp_socket_path):
    server = IPCServer(socket_path=tmp_socket_path)
    await server.start()

    received = []

    async def collect_handler(msg):
        received.append(msg)
        return {"ok": True}

    server.register_handler("broadcast_test", collect_handler)

    client1 = IPCClient(socket_path=tmp_socket_path)
    client2 = IPCClient(socket_path=tmp_socket_path)
    await client1.connect()
    await client2.connect()

    await client1.send({"type": "broadcast_test", "data": "hello"})
    await client2.send({"type": "broadcast_test", "data": "world"})

    await asyncio.sleep(0.1)
    assert len(received) == 2

    await client1.disconnect()
    await client2.disconnect()
    await server.stop()


@pytest.mark.asyncio
async def test_concurrent_clients(tmp_socket_path):
    server = IPCServer(socket_path=tmp_socket_path)
    await server.start()

    async def echo_handler(msg):
        return {"echo": msg.get("data", {})}

    server.register_handler("echo", echo_handler)

    async def client_task(client_id):
        client = IPCClient(socket_path=tmp_socket_path)
        await client.connect()
        response = await client.send({
            "type": "echo",
            "data": {"client": client_id},
        })
        await client.disconnect()
        return response

    results = await asyncio.gather(
        client_task(1), client_task(2), client_task(3)
    )

    for r in results:
        assert r["ok"] is True

    await server.stop()


@pytest.mark.asyncio
async def test_server_rejects_invalid_json(tmp_socket_path):
    server = IPCServer(socket_path=tmp_socket_path)
    await server.start()

    reader, writer = await asyncio.open_unix_connection(tmp_socket_path)
    writer.write(b"not json\n")
    await writer.drain()

    response_line = await reader.readline()
    response = json.loads(response_line.decode("utf-8").strip())
    assert response["ok"] is False
    assert response["error"] == "Invalid JSON"

    writer.close()
    await server.stop()


@pytest.mark.asyncio
async def test_tcp_server_start_stop():
    server = IPCServer(use_unix=False, tcp_port=0)
    await server.start()
    assert server.is_running() is True
    await server.stop()
    assert server.is_running() is False
