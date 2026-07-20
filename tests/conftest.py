import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

_HOOK_BASE = {
    "kernel_before": [], "kernel_after": [],
    "mkc_before": [], "mkc_after": [],
    "bridge_before": [], "bridge_after": [],
    "optimizer_before": [], "optimizer_after": [],
    "mel_before": [], "mel_after": [],
    "feedback_before": [], "feedback_after": [],
    "memory_before": [], "memory_after": [],
}


@pytest.fixture
def reset_plugins():
    from plugin_registry import HOOKS, PLUGINS
    PLUGINS.clear()
    HOOKS.clear()
    HOOKS.update(_HOOK_BASE)


@pytest.fixture
def reset_memory():
    import memory
    memory._conn = None
    memory.init()


@pytest.fixture
def tmp_kernel():
    from kernel import MuscalKernel
    k = MuscalKernel(enable_graph=False, enable_sphere=False)
    return k


import pytest_asyncio
import tempfile
from pathlib import Path

from config import BASE_DIR


@pytest_asyncio.fixture
async def tmp_socket_path():
    path = BASE_DIR / "runtime.sock"
    yield path
    try:
        path.unlink(missing_ok=True)
    except Exception:
        pass


@pytest_asyncio.fixture
async def tmp_data_dir():
    path = BASE_DIR / "tmp_data"
    path.mkdir(exist_ok=True)
    yield path
    try:
        import shutil
        shutil.rmtree(path, ignore_errors=True)
    except Exception:
        pass


@pytest_asyncio.fixture
async def async_process_manager(tmp_socket_path, tmp_data_dir):
    from runtime.process_manager import ProcessManager
    pm = ProcessManager(socket_path=tmp_socket_path)
    yield pm
    try:
        await pm.shutdown_all()
    except Exception:
        pass


@pytest_asyncio.fixture
async def async_ipc_server(tmp_socket_path):
    from runtime.ipc_server import IPCServer
    server = IPCServer(socket_path=tmp_socket_path)
    yield server
    try:
        await server.stop()
    except Exception:
        pass
