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


def test_all_hooks_present():
    from plugin_registry import HOOKS
    expected_hooks = [
        "kernel_before", "kernel_after",
        "mkc_before", "mkc_after",
        "bridge_before", "bridge_after",
        "optimizer_before", "optimizer_after",
        "mel_before", "mel_after",
        "feedback_before", "feedback_after",
        "memory_before", "memory_after",
    ]
    assert set(HOOKS.keys()) == set(expected_hooks)


def test_run_hooks_sets_hook_name():
    from plugin_registry import HOOKS, run_hooks
    names = []
    def tracker(ctx):
        names.append(ctx["_hook_name"])
    HOOKS["kernel_before"].append(tracker)
    HOOKS["mkc_before"].append(tracker)
    ctx = {"input_text": "test", "kernel": None}
    run_hooks("kernel_before", ctx)
    run_hooks("mkc_before", ctx)
    assert names == ["kernel_before", "mkc_before"]


def test_plugins_loaded():
    from plugin_loader import load_plugins
    from plugin_registry import HOOKS, PLUGINS
    load_plugins()
    assert len(PLUGINS) >= 1
    for p in PLUGINS:
        assert hasattr(p, "name")
        assert hasattr(p, "register")
        assert callable(p.register)


def test_validate_plugin():
    import types
    from plugin_loader import validate_plugin
    safe_mod = types.ModuleType("safe")
    safe_mod.__file__ = "/tmp/safe.py"
    assert len(validate_plugin(safe_mod)) == 0


def test_hook_context_kernel_reference():
    from plugin_loader import load_plugins
    from plugin_registry import HOOKS
    from kernel import MuscalKernel
    load_plugins()
    kernel_ref_ok = [False]
    def check_kernel(ctx):
        kernel_ref_ok[0] = ctx.get("kernel") is not None and hasattr(ctx["kernel"], "run")
    HOOKS["kernel_before"].append(check_kernel)
    k = MuscalKernel(enable_graph=False)
    k.run("hello from context test")
    assert kernel_ref_ok[0]
