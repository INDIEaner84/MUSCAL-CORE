import os

import pytest


@pytest.fixture(autouse=True)
def reset_state():
    from plugin_registry import PLUGINS, HOOKS
    PLUGINS.clear()
    HOOKS.clear()
    yield


class TestPluginSandboxIntegration:
    def test_plugins_load_in_sandbox_mode(self):
        os.environ["MUSCAL_PLUGIN_SANDBOX"] = "1"
        try:
            from plugin_loader import load_plugins
            load_plugins()
            from plugin_registry import PLUGINS
            assert len(PLUGINS) >= 6, f"Expected >=6 plugins, got {len(PLUGINS)}"
            names = [p.name for p in PLUGINS]
            assert "input_classifier" in names
            assert "health_monitor" in names
            assert "execution_trace" in names
        finally:
            os.environ.pop("MUSCAL_PLUGIN_SANDBOX", None)

    def test_all_hooks_registered_in_sandbox(self):
        os.environ["MUSCAL_PLUGIN_SANDBOX"] = "1"
        try:
            from plugin_loader import load_plugins
            load_plugins()
            from plugin_registry import HOOKS
            assert "mkc_before" in HOOKS
            assert "kernel_before" in HOOKS
            assert "feedback_after" in HOOKS
        finally:
            os.environ.pop("MUSCAL_PLUGIN_SANDBOX", None)

    def test_sandbox_blocks_dangerous_imports(self):
        from features.sandbox import PluginSandbox
        sandbox = PluginSandbox()
        for dangerous in ["import os", "import subprocess", "import socket"]:
            with pytest.raises(Exception, match="(?i)blocked"):
                sandbox.exec_module(f'{dangerous}\nclass Plugin: pass')

    def test_sandbox_allows_safe_imports(self):
        from features.sandbox import PluginSandbox
        sandbox = PluginSandbox()
        for safe_mod in ["json", "time", "math", "re"]:
            result = sandbox.exec_module(f'import {safe_mod}\nclass Plugin:\n    pass')
            assert "Plugin" in result
