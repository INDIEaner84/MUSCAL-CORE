import os
import json


_HOOK_BASE = {
    "kernel_before": [], "kernel_after": [],
    "mkc_before": [], "mkc_after": [],
    "bridge_before": [], "bridge_after": [],
    "optimizer_before": [], "optimizer_after": [],
    "mel_before": [], "mel_after": [],
    "feedback_before": [], "feedback_after": [],
    "memory_before": [], "memory_after": [],
}


import pytest


@pytest.fixture(autouse=True)
def _setup():
    from plugin_registry import HOOKS, PLUGINS
    PLUGINS.clear()
    HOOKS.clear()
    HOOKS.update(_HOOK_BASE)


def test_plugin_health():
    health_path = "storage/health.jsonl"
    if os.path.exists(health_path):
        os.remove(health_path)

    from plugin_registry import HOOKS, run_hooks
    from plugin_loader import load_plugins
    load_plugins()

    crash_count = [0]
    def crashy(ctx):
        crash_count[0] += 1
        raise RuntimeError("intentional test crash")

    HOOKS["kernel_before"].append(crashy)

    ctx = {"input_text": "test", "kernel": None}
    for i in range(5):
        run_hooks("kernel_before", ctx)

    assert crash_count[0] == 1
    assert len(HOOKS["kernel_before"]) >= 1
    assert os.path.exists(health_path)

    lines = [l.strip() for l in open(health_path) if l.strip()]
    assert len(lines) >= 1

    for line in lines:
        entry = json.loads(line)
        assert "hook" in entry
        assert "plugin" in entry
        assert "failures_in_window" in entry
        assert "timestamp" in entry
