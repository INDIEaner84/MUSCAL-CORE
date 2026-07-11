import signal
import time


class TestPluginTimeout:
    def test_timeout_handler_raises(self):
        from plugin_registry import _PluginTimeout, _timeout_handler
        try:
            _timeout_handler(None, None)
        except _PluginTimeout:
            assert True
        else:
            assert False, "Expected _PluginTimeout"

    def test_timeout_env_var_default(self):
        import os
        from plugin_registry import _PLUGIN_TIMEOUT_SECONDS, _HAS_SIGALRM
        assert isinstance(_PLUGIN_TIMEOUT_SECONDS, int)
        assert _PLUGIN_TIMEOUT_SECONDS >= 1
        assert _HAS_SIGALRM == hasattr(signal, "SIGALRM")

    def test_hanging_callback_removed(self):
        from plugin_registry import HOOKS, PLUGINS, run_hooks
        PLUGINS.clear()
        for k in list(HOOKS):
            HOOKS[k].clear()

        captured = []

        def hanging_callback(ctx):
            captured.append("called")
            time.sleep(30)

        def rescue(ctx):
            captured.append("rescue")

        HOOKS.setdefault("kernel_after", []).append(hanging_callback)
        HOOKS.setdefault("kernel_after", []).append(rescue)

        run_hooks("kernel_after", {"input_text": "timeout test"})

        assert "called" in captured
        if hasattr(signal, "SIGALRM"):
            assert len(HOOKS["kernel_after"]) == 1
            assert HOOKS["kernel_after"][0] == rescue
