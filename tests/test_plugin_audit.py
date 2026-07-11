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


def test_plugin_audit():
    audit_path = "storage/audit.jsonl"
    if os.path.exists(audit_path):
        os.remove(audit_path)

    from plugin_loader import load_plugins
    load_plugins()

    from kernel import MuscalKernel
    k = MuscalKernel(enable_graph=True)
    for i in range(3):
        k.run(f"print hello from audit test {i}")

    assert os.path.exists(audit_path)

    with open(audit_path) as f:
        lines = [l.strip() for l in f if l.strip()]
    assert len(lines) == 7 * 3

    for i, line in enumerate(lines):
        entry = json.loads(line)
        assert "hook" in entry
        assert "timestamp" in entry
        assert "duration_ms" in entry
        assert entry["duration_ms"] >= 0

    hook_names = set()
    for line in lines:
        entry = json.loads(line)
        hook_names.add(entry["hook"])
    expected = {"kernel_after", "mkc_after", "bridge_after", "optimizer_after",
                "mel_after", "feedback_after", "memory_after"}
    assert hook_names == expected
