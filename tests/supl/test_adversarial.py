from __future__ import annotations
import json
import threading
import time
import uuid
import pytest
from unittest.mock import MagicMock


class TestSafetyGateAdversarial:
    """Adversarial tests for SafetyGate enforcement in SUPL API."""

    def test_high_risk_tool_rejected(self, safety_gate):
        result = safety_gate.check("shell.exec", {"command": "rm -rf /"})
        assert result.risk in ("high", "critical")
        assert not result.allowed

    def test_shell_metacharacters_flagged(self, safety_gate):
        result = safety_gate.check("shell.exec", {"command": "ls; rm -rf /"})
        assert not result.allowed

    def test_shell_metacharacters_via_url_flagged(self, safety_gate):
        result = safety_gate.check("filesystem.write", {"path": "x; rm -rf /"})
        assert not result.allowed

    def test_path_traversal_flagged(self, safety_gate):
        result = safety_gate.check("filesystem.write", {"path": "../../../etc/passwd"})
        assert not result.allowed

    def test_blocked_tool_rejected(self, safety_gate):
        result = safety_gate.check("os.system", {"command": "ls"})
        assert not result.allowed
        assert result.risk == "critical"

    def test_unknown_tool_rejected(self, safety_gate):
        result = safety_gate.check("nonexistent.tool", {})
        assert not result.allowed

    def test_shell_metacharacters_in_args(self, safety_gate):
        result = safety_gate.check("filesystem.write", {"path": "/tmp/test", "content": "x; rm -rf /"})
        assert not result.allowed


class TestURTAdversarial:
    """Adversarial tests for UnifiedToolRuntime integration with SUPL."""

    def test_nonexistent_tool_returns_error(self, utr):
        result = utr.execute("nonexistent.tool", {"x": 1})
        assert not result.success
        assert result.error is not None

    def test_missing_keys_in_args(self, utr):
        result = utr.execute("math.add", {})
        assert result.success
        assert result.output.get("result") == 0

    def test_none_parameters(self, utr):
        result = utr.execute("math.add", None)
        assert result.success
        assert result.output.get("result") == 0

    def test_large_string_in_args(self, utr):
        result = utr.execute("math.add", {"a": 1, "b": 2, "data": "x" * 10000})
        assert result.success

    def test_concurrent_executions(self, utr):
        errors = []
        lock = threading.Lock()

        def worker():
            for _ in range(10):
                try:
                    r = utr.execute("math.add", {"a": 1, "b": 2})
                    if not r.success:
                        with lock:
                            errors.append(r.error)
                except Exception:
                    with lock:
                        errors.append("exception")

        threads = [threading.Thread(target=worker) for _ in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        assert len(errors) == 0, f"Concurrent errors: {errors}"


class TestEventBusAdversarial:
    """Adversarial tests for event bus integration."""

    def test_very_large_payload(self, event_bus):
        received = []
        event_bus.subscribe("supl.test", lambda m: received.append(m))
        large = {"data": "x" * 50000}
        event_bus.publish("supl.test", large, source="test")
        assert len(received) == 1

    def test_unicode_payload(self, event_bus):
        received = []
        event_bus.subscribe("supl.test", lambda m: received.append(m))
        event_bus.publish("supl.test", {"msg": "\ud83d\ude00\u00e9\u00f1"}, source="test")
        assert len(received) == 1

    def test_rapid_publish_subscribe(self, event_bus):
        received = []
        event_bus.subscribe("supl.rapid", lambda m: received.append(m))
        for i in range(100):
            event_bus.publish("supl.rapid", {"i": i}, source="test")
        assert len(received) == 100

    def test_unsubscribe_during_publish(self, event_bus):
        calls = []

        def cb(m):
            calls.append(1)
            if len(calls) == 1:
                event_bus.unsubscribe("supl.unsub", cb)

        event_bus.subscribe("supl.unsub", cb)
        event_bus.publish("supl.unsub", {"x": 1}, source="test")
        event_bus.publish("supl.unsub", {"x": 2}, source="test")
        assert len(calls) == 1

    def test_wildcard_stress(self, event_bus):
        received = []
        event_bus.subscribe("*", lambda m: received.append(m))
        topics = [f"supl.stress.{i}" for i in range(50)]
        for t in topics:
            event_bus.publish(t, {"idx": int(t.split(".")[-1])}, source="test")
        assert len(received) == 50


class TestProvenanceAdversarial:
    """Adversarial tests for provenance chain integrity."""

    def test_linker_inconsistent_chain(self, linker):
        interaction = pytest.importorskip("features.supl.provenance").UIInteraction.create(
            application_id="test", action_id="add"
        )
        mock_receipt = MagicMock()
        mock_receipt.receipt_id = "receipt-abc"
        mock_receipt.execution_id = "exec-abc"
        linker.link(interaction, mock_receipt)
        assert linker.validate_consistency(interaction.interaction_id, "exec-abc", "receipt-abc") is True
        assert linker.validate_consistency(interaction.interaction_id, "wrong-exec", "receipt-abc") is False

    def test_linker_missing_interaction(self, linker):
        assert linker.get_chain("nonexistent") is None
        assert linker.validate_consistency("nonexistent", "e1", "r1") is False

    def test_link_without_receipt(self, linker):
        interaction = pytest.importorskip("features.supl.provenance").UIInteraction.create(
            application_id="test", action_id="add"
        )
        linker.link(interaction)
        chain = linker.get_chain(interaction.interaction_id)
        assert chain is not None

    def test_link_multiple_interactions(self, linker):
        receipts = []
        for i in range(10):
            interaction = pytest.importorskip("features.supl.provenance").UIInteraction.create(
                application_id=f"app{i}", action_id="add"
            )
            mock_r = MagicMock()
            mock_r.receipt_id = f"receipt-{i}"
            mock_r.execution_id = f"exec-{i}"
            linker.link(interaction, mock_r)
            receipts.append(interaction)
        for i, interaction in enumerate(receipts):
            chain = linker.get_chain(interaction.interaction_id)
            assert chain["execution_id"] == f"exec-{i}"
            assert chain["receipt_id"] == f"receipt-{i}"


class TestProjectionAdversarial:
    """Adversarial tests for projection engine edge cases."""

    def test_projection_nonexistent_app(self, projection_engine):
        ctx = pytest.importorskip("features.supl.projection_engine").ProjectionContext()
        ui_mode = pytest.importorskip("features.supl.projection_engine").UIMode.OVERLAY
        proj = projection_engine.project("nonexistent", ctx, ui_mode)
        assert proj.projection_state.value == "error"

    def test_projection_with_empty_context(self, projection_engine, registry):
        ctx = pytest.importorskip("features.supl.projection_engine").ProjectionContext()
        ui_mode = pytest.importorskip("features.supl.projection_engine").UIMode.OVERLAY
        proj = projection_engine.project("test_calc", ctx, ui_mode)
        assert proj.projection_state.value in ("fresh", "synced")

    def test_projection_all_three_modes(self, projection_engine, registry):
        ctx = pytest.importorskip("features.supl.projection_engine").ProjectionContext()
        modes = [
            pytest.importorskip("features.supl.projection_engine").UIMode.NATIVE,
            pytest.importorskip("features.supl.projection_engine").UIMode.OVERLAY,
            pytest.importorskip("features.supl.projection_engine").UIMode.GRAPH_NATIVE,
        ]
        for mode in modes:
            proj = projection_engine.project("test_calc", ctx, mode)
            assert proj.projection_state.value in ("fresh", "synced")
