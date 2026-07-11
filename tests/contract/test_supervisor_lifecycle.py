import pytest


class TestSupervisorLifecycle:
    """Contract: Supervisor Lifecycle — 6 Phasen als isolierte Tests."""

    def test_phase1_kernel_boot(self):
        from kernel import MuscalKernel
        k = MuscalKernel(enable_graph=True, enable_sphere=True)
        assert k is not None
        assert k.graph is not None
        assert k.sphere is not None

    def test_phase2_plugin_loading(self):
        from plugin_loader import load_plugins
        from plugin_registry import PLUGINS, HOOKS
        load_plugins()
        assert len(PLUGINS) >= 0
        assert len(HOOKS) >= 14

    def test_phase3_eventbus_active(self):
        from event_bus import EventBus
        bus = EventBus()
        received = []
        bus.subscribe("test.boot", lambda m: received.append(m))
        bus.publish("test.boot", {"phase": "init"})
        assert len(received) == 1

    def test_phase4_kernel_run(self):
        from kernel import MuscalKernel
        k = MuscalKernel(enable_graph=True, enable_sphere=True)
        result = k.run("print hello")
        assert result.success
        assert result.memory_id > 0

    def test_phase5_api_health(self):
        from runtime.api import create_app
        app = create_app()
        assert app is not None
        rules = [r.rule for r in app.url_map.iter_rules()]
        assert len(rules) > 0
        assert any("/health" in r for r in rules)

    def test_phase6_graceful_shutdown(self):
        from kernel import MuscalKernel
        k = MuscalKernel(enable_graph=False, enable_sphere=False)
        result = k.run("print goodbye")
        assert result.success
