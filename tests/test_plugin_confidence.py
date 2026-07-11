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


def test_plugin_confidence():
    conf_path = "storage/confidence.jsonl"
    if os.path.exists(conf_path):
        os.remove(conf_path)

    from plugin_loader import load_plugins
    load_plugins()

    from kernel import MuscalKernel
    k = MuscalKernel(enable_graph=True)
    for i in range(5):
        k.run(f"print hello world {i}")

    assert os.path.exists(conf_path)

    lines = [l.strip() for l in open(conf_path) if l.strip()]
    assert len(lines) >= 1

    mkc_entries = 0
    feedback_entries = 0
    for i, line in enumerate(lines):
        entry = json.loads(line)
        assert "timestamp" in entry
        assert "source" in entry
        assert "input" in entry
        if entry["source"] == "mkc":
            mkc_entries += 1
            assert "avg_confidence" in entry
            assert "min_confidence" in entry
            assert "max_confidence" in entry
        elif entry["source"] == "feedback":
            feedback_entries += 1
            assert "adjustments" in entry

    assert mkc_entries >= 1
