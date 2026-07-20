import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from runtime.process_manager import (
    AgentState,
    ManagedAgent,
    ProcessManager,
)


@pytest.fixture
def pm():
    return ProcessManager(max_restarts=3)


@pytest.fixture
def mock_process():
    proc = MagicMock()
    proc.pid = 42
    proc.stdout = None
    proc.returncode = None
    proc.terminate = MagicMock()
    proc.kill = MagicMock()
    proc.wait = AsyncMock(return_value=0)
    return proc


@pytest.mark.asyncio
async def test_spawn_agent(pm, mock_process):
    with patch(
        "asyncio.create_subprocess_exec", AsyncMock(return_value=mock_process)
    ):
        pid = await pm.spawn_agent(
            agent_id="test-agent", command=["echo", "hello"]
        )

    assert pid == 42
    assert pm.get_agent_pid("test-agent") == 42
    assert pm.get_status("test-agent") == AgentState.RUNNING.value


@pytest.mark.asyncio
async def test_spawn_duplicate_raises(pm, mock_process):
    with patch(
        "asyncio.create_subprocess_exec", AsyncMock(return_value=mock_process)
    ):
        await pm.spawn_agent("test-agent", ["echo", "hello"])
        with pytest.raises(ValueError, match="already running"):
            await pm.spawn_agent("test-agent", ["echo", "hello"])


@pytest.mark.asyncio
async def test_shutdown_agent(pm, mock_process):
    with patch(
        "asyncio.create_subprocess_exec", AsyncMock(return_value=mock_process)
    ):
        await pm.spawn_agent("test-agent", ["echo", "hello"])

    result = await pm.shutdown_agent("test-agent")
    assert result is True
    assert pm.get_status("test-agent") == AgentState.STOPPED.value


@pytest.mark.asyncio
async def test_shutdown_nonexistent_agent(pm):
    result = await pm.shutdown_agent("nonexistent")
    assert result is False


@pytest.mark.asyncio
async def test_shutdown_all(pm, mock_process):
    with patch(
        "asyncio.create_subprocess_exec", AsyncMock(return_value=mock_process)
    ):
        await pm.spawn_agent("agent-1", ["echo", "a"])
        await pm.spawn_agent("agent-2", ["echo", "b"])

    await pm.shutdown_all()
    assert pm.get_status("agent-1") is None
    assert pm.get_status("agent-2") is None
    assert len(pm.list_agents()) == 0


@pytest.mark.asyncio
async def test_get_agent_pid(pm, mock_process):
    with patch(
        "asyncio.create_subprocess_exec", AsyncMock(return_value=mock_process)
    ):
        await pm.spawn_agent("test-agent", ["echo", "hello"])

    assert pm.get_agent_pid("test-agent") == 42
    assert pm.get_agent_pid("nonexistent") is None


@pytest.mark.asyncio
async def test_get_status(pm, mock_process):
    with patch(
        "asyncio.create_subprocess_exec", AsyncMock(return_value=mock_process)
    ):
        await pm.spawn_agent("test-agent", ["echo", "hello"])

    assert pm.get_status("test-agent") == "running"
    assert pm.get_status("nonexistent") is None


@pytest.mark.asyncio
async def test_restart_agent(pm):
    mock1 = MagicMock()
    mock1.pid = 42
    mock1.stdout = None
    mock1.returncode = None
    mock1.terminate = MagicMock()
    mock1.kill = MagicMock()
    mock1.wait = AsyncMock(return_value=0)

    mock2 = MagicMock()
    mock2.pid = 99
    mock2.stdout = None
    mock2.returncode = None
    mock2.terminate = MagicMock()
    mock2.kill = MagicMock()
    mock2.wait = AsyncMock(return_value=0)

    with patch(
        "asyncio.create_subprocess_exec",
        AsyncMock(side_effect=[mock1, mock2]),
    ):
        pid1 = await pm.spawn_agent("test-agent", ["echo", "hello"])
        assert pid1 == 42

        pid2 = await pm.restart_agent("test-agent")
        assert pid2 == 99


@pytest.mark.asyncio
async def test_restart_max_restarts(pm, mock_process):
    with patch(
        "asyncio.create_subprocess_exec", AsyncMock(return_value=mock_process)
    ):
        await pm.spawn_agent("test-agent", ["echo", "hello"])

    agent = pm._agents["test-agent"]
    agent.restart_count = 3

    result = await pm.restart_agent("test-agent")
    assert result is None
    assert pm.get_status("test-agent") == AgentState.CRASHED.value


@pytest.mark.asyncio
async def test_restart_nonexistent(pm):
    result = await pm.restart_agent("nonexistent")
    assert result is None


@pytest.mark.asyncio
async def test_heartbeat_update(pm, mock_process):
    with patch(
        "asyncio.create_subprocess_exec", AsyncMock(return_value=mock_process)
    ):
        await pm.spawn_agent("test-agent", ["echo", "hello"])

    old_hb = pm._agents["test-agent"].last_heartbeat
    pm.update_heartbeat("test-agent")
    new_hb = pm._agents["test-agent"].last_heartbeat
    assert new_hb != old_hb


@pytest.mark.asyncio
async def test_heartbeat_nonexistent(pm):
    pm.update_heartbeat("nonexistent")


@pytest.mark.asyncio
async def test_list_agents(pm, mock_process):
    with patch(
        "asyncio.create_subprocess_exec", AsyncMock(return_value=mock_process)
    ):
        await pm.spawn_agent("agent-1", ["echo", "a"])

    agents = pm.list_agents()
    assert len(agents) == 1
    assert agents[0]["agent_id"] == "agent-1"
    assert agents[0]["state"] == "running"


@pytest.mark.asyncio
async def test_get_all_agents(pm, mock_process):
    with patch(
        "asyncio.create_subprocess_exec", AsyncMock(return_value=mock_process)
    ):
        await pm.spawn_agent("test-agent", ["echo", "hello"])

    agents = pm.get_all_agents()
    assert len(agents) == 1
    assert isinstance(agents[0], ManagedAgent)
    assert agents[0].agent_id == "test-agent"


@pytest.mark.asyncio
async def test_to_dict(pm, mock_process):
    with patch(
        "asyncio.create_subprocess_exec", AsyncMock(return_value=mock_process)
    ):
        await pm.spawn_agent("test-agent", ["echo", "hello"])

    d = pm.to_dict()
    assert d["count"] == 1
    assert d["running"] == 1
    assert "test-agent" in d["agents"]


@pytest.mark.asyncio
async def test_monitor_start_stop(pm):
    await pm.start_monitor()
    assert pm._running is True
    assert pm._monitor_task is not None
    await pm.stop_monitor()
    assert pm._running is False


@pytest.mark.asyncio
async def test_process_manager_init_with_defaults():
    pm = ProcessManager()
    assert pm.max_restarts == 3
    assert pm.heartbeat_timeout == 30.0
    assert pm.socket_path is not None


@pytest.mark.asyncio
async def test_shutdown_agent_process_lookup_error(pm, mock_process):
    with patch(
        "asyncio.create_subprocess_exec", AsyncMock(return_value=mock_process)
    ):
        await pm.spawn_agent("test-agent", ["echo", "hello"])

    mock_process.wait.side_effect = ProcessLookupError()
    result = await pm.shutdown_agent("test-agent")
    assert result is True
    assert pm.get_status("test-agent") == AgentState.STOPPED.value
