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
