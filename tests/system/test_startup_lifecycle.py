import os
import tempfile

import pytest


@pytest.fixture(autouse=True)
def reset_state():
    from plugin_registry import PLUGINS, HOOKS
    PLUGINS.clear()
    HOOKS.clear()
    HOOKS.update({
        "kernel_before": [], "kernel_after": [],
        "mkc_before": [], "mkc_after": [],
        "bridge_before": [], "bridge_after": [],
        "optimizer_before": [], "optimizer_after": [],
        "mel_before": [], "mel_after": [],
        "feedback_before": [], "feedback_after": [],
        "memory_before": [], "memory_after": [],
    })
    yield


class TestStartupLifecycle:
    def test_muscal_os_creates_storage(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            original = os.getcwd()
            os.chdir(tmpdir)
            try:
                os.environ["MUSCAL_MODE"] = "development"
                from muscal_os import MuscalOS
                os_ = MuscalOS()
                os_.start()
                assert os.path.isdir("storage")
            finally:
                os.chdir(original)

    def test_boot_fires_events_in_order(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            original = os.getcwd()
            os.chdir(tmpdir)
            try:
                os.environ["MUSCAL_MODE"] = "development"
                from muscal_os import MuscalOS
                from schema import (
                    EVENT_BOOT_INIT, EVENT_KERNEL_INITIALIZED,
                    EVENT_PLUGINS_INITIALIZED, EVENT_RUNTIME_INITIALIZED,
                )
                os_ = MuscalOS()
                fired = []
                os_.events.subscribe(EVENT_BOOT_INIT, lambda m: fired.append("boot"))
                os_.events.subscribe(EVENT_KERNEL_INITIALIZED, lambda m: fired.append("kernel"))
                os_.events.subscribe(EVENT_PLUGINS_INITIALIZED, lambda m: fired.append("plugins"))
                os_.events.subscribe(EVENT_RUNTIME_INITIALIZED, lambda m: fired.append("runtime"))
                os_.start()
                assert fired == ["boot", "kernel", "plugins", "runtime"], f"Got: {fired}"
            finally:
                os.chdir(original)

    def test_boot_report_contains_all_steps(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            original = os.getcwd()
            os.chdir(tmpdir)
            try:
                os.environ["MUSCAL_MODE"] = "development"
                from muscal_os import MuscalOS
                os_ = MuscalOS()
                report = os_.start()
                step_names = [s.step_name for s in report.steps]
                expected = [
                    "create_storage", "init_event_bus", "validate_config",
                    "resolve_paths", "init_kernel", "init_plugins",
                    "init_system_runtime", "wire_event_bus",
                ]
                for name in expected:
                    assert name in step_names, f"Missing step: {name}"
                assert report.success is True
            finally:
                os.chdir(original)

    def test_eventbus_bridge_to_graph(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            original = os.getcwd()
            os.chdir(tmpdir)
            try:
                os.environ["MUSCAL_MODE"] = "development"
                from muscal_os import MuscalOS
                from schema import EVENT_BOOT_INIT
                os_ = MuscalOS()
                os_.start()
                assert os_.kernel is not None
                assert os_.kernel.graph is not None
                graph_events = []
                os_.kernel.graph.on(EVENT_BOOT_INIT, lambda e: graph_events.append(e))
                os_.events.publish(EVENT_BOOT_INIT, {"test": True}, source="test")
                assert len(graph_events) >= 1
                event = graph_events[0]
                assert event["type"] == EVENT_BOOT_INIT
                assert event["payload"]["test"] is True
                assert event["payload"]["_source"] == "test"
            finally:
                os.chdir(original)

    def test_boot_idempotent(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            original = os.getcwd()
            os.chdir(tmpdir)
            try:
                os.environ["MUSCAL_MODE"] = "development"
                from muscal_os import MuscalOS
                os_ = MuscalOS()
                r1 = os_.start()
                r2 = os_.start()
                assert r1.success == r2.success
            finally:
                os.chdir(original)

    def test_status_reflects_boot(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            original = os.getcwd()
            os.chdir(tmpdir)
            try:
                os.environ["MUSCAL_MODE"] = "development"
                from muscal_os import MuscalOS
                os_ = MuscalOS()
                status_before = os_.get_status()
                assert status_before["running"] is False
                os_.start()
                status_after = os_.get_status()
                assert status_after["running"] is True
                assert status_after["kernel_ready"] is True
                assert status_after["boot"] is not None
                assert "[OK]" in str(status_after["boot"])
            finally:
                os.chdir(original)
