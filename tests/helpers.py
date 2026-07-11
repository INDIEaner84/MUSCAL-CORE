"""Plugin-Test-Helper: shared fixtures for plugin tests."""

from plugin_registry import HOOKS, PLUGINS
from plugin_loader import load_plugins

_HOOK_BASE = {
    "kernel_before": [], "kernel_after": [],
    "mkc_before": [], "mkc_after": [],
    "bridge_before": [], "bridge_after": [],
    "optimizer_before": [], "optimizer_after": [],
    "mel_before": [], "mel_after": [],
    "feedback_before": [], "feedback_after": [],
    "memory_before": [], "memory_after": [],
}


def reset_plugins():
    PLUGINS.clear()
    HOOKS.clear()
    HOOKS.update(_HOOK_BASE)


def reload_plugins():
    reset_plugins()
    load_plugins()


def count_hooks(hook_name: str = None) -> int:
    if hook_name:
        return len(HOOKS.get(hook_name, []))
    return sum(len(v) for v in HOOKS.values())


def assert_ctx_has(ctx: dict, keys: list[str]) -> list[str]:
    missing = [k for k in keys if k not in ctx]
    return missing


def run_pipeline_with_plugins(input_text: str = "print hello") -> dict:
    from kernel import MuscalKernel
    k = MuscalKernel(enable_graph=False)
    result = k.run(input_text)
    return {"result": result, "kernel": k}
