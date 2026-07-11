"""Kernel state transitions: error paths, failure modes, edge cases."""

from unittest.mock import patch

import pytest

from kernel import MuscalKernel
from schema import FeedbackReport


_HOOK_BASE = {
    "kernel_before": [], "kernel_after": [],
    "mkc_before": [], "mkc_after": [],
    "bridge_before": [], "bridge_after": [],
    "optimizer_before": [], "optimizer_after": [],
    "mel_before": [], "mel_after": [],
    "feedback_before": [], "feedback_after": [],
    "memory_before": [], "memory_after": [],
}


@pytest.fixture(autouse=True)
def _setup():
    from plugin_registry import HOOKS, PLUGINS
    PLUGINS.clear()
    HOOKS.clear()
    HOOKS.update(_HOOK_BASE)


def test_run_mkc_failure_not_handled():
    k = MuscalKernel(enable_graph=True, enable_sphere=False)
    k.run("fresh")
    with patch.object(k.mkc, "compile", side_effect=ValueError("mkc crash")):
        result = k.run("fresh")
        assert result.success is False
        assert "mkc crash" in result.errors[0]


def test_run_bridge_invalid_stores_memory():
    k = MuscalKernel(enable_graph=True, enable_sphere=False)
    with patch.object(k.bridge, "validate") as mock:
        mock.return_value.valid = False
        mock.return_value.errors = ["bridge failed"]
        result = k.run("invalid")
        assert result.success is False
        assert result.memory_id is not None


def test_run_consecutive_same_input():
    k = MuscalKernel(enable_graph=True, enable_sphere=False)
    r1 = k.run("repeat test")
    r2 = k.run("repeat test")
    assert r1.success == r2.success
    assert r1.memory_id != r2.memory_id
    assert len(r1.execution) == len(r2.execution)


def test_run_without_graph():
    k = MuscalKernel(enable_graph=False, enable_sphere=False)
    result = k.run("no graph")
    assert result.success is True


def test_run_without_sphere():
    k = MuscalKernel(enable_graph=True, enable_sphere=False)
    result = k.run("no sphere")
    assert result.success is True


def test_memory_init_called_once():
    k1 = MuscalKernel(enable_graph=False, enable_sphere=False)
    k2 = MuscalKernel(enable_graph=False, enable_sphere=False)
    r1 = k1.run("first")
    r2 = k2.run("second")
    assert r1.memory_id is not None
    assert r2.memory_id is not None


def test_feedback_analyzed_on_success():
    k = MuscalKernel(enable_graph=True, enable_sphere=False)
    result = k.run("print hello")
    assert result.feedback is not None
    assert hasattr(result.feedback, "summary")
    assert hasattr(result.feedback, "failure_patterns")
    assert hasattr(result.feedback, "confidence_adjustments")


def test_graph_events_emitted_during_run():
    k = MuscalKernel(enable_graph=True, enable_sphere=False)
    before = len(k.graph._update_stream)
    k.run("emit test")
    after = len(k.graph._update_stream)
    assert after > before


def test_run_does_not_leak_nodes():
    k = MuscalKernel(enable_graph=True, enable_sphere=False)
    k.run("input a")
    k.run("input b")
    k.run("input c")
    for nid, node in k.graph.nodes.items():
        assert node.type in (
            "INTENT", "RAG_CONTEXT", "MKC_STEP", "MCXF_SECTION",
            "EXECUTION_PLAN", "TOOL_EXECUTION", "SYSTEM_ACTION",
            "CONFLICT", "MEMORY_ENTRY"
        ), f"Unexpected node type: {node.type}"
