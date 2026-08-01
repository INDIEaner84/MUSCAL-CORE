import os as _os
import signal as _signal
import traceback as _traceback


_PLUGIN_TIMEOUT_SECONDS = int(_os.environ.get("MUSCAL_PLUGIN_TIMEOUT", "10"))
_HAS_SIGALRM = hasattr(_signal, "SIGALRM")

PLUGINS = []

HOOKS = {
    "kernel_before": [],
    "kernel_after": [],
    "mkc_before": [],
    "mkc_after": [],
    "bridge_before": [],
    "bridge_after": [],
    "optimizer_before": [],
    "optimizer_after": [],
    "mel_before": [],
    "mel_after": [],
    "feedback_before": [],
    "feedback_after": [],
    "memory_before": [],
    "memory_after": [],
}

PLUGIN_CAPABILITIES: dict[int, set] = {}

CAPABILITY_MAP = {
    "kernel_before": {"ctx_read", "input_read", "kernel_access"},
    "kernel_after": {"ctx_read", "result_read", "kernel_access"},
    "mkc_before": {"input_read", "ctx_read", "kernel_access"},
    "mkc_after": {"ctx_read", "kernel_access"},
    "bridge_before": {"input_read", "ctx_read", "kernel_access"},
    "bridge_after": {"ctx_read", "kernel_access"},
    "optimizer_before": {"plan_read", "ctx_read"},
    "optimizer_after": {"ctx_read"},
    "mel_before": {"plan_read", "ctx_read"},
    "mel_after": {"result_read", "ctx_read"},
    "feedback_before": {"result_read", "ctx_read"},
    "feedback_after": {"ctx_read"},
    "memory_before": {"result_read", "ctx_read"},
    "memory_after": {"ctx_read"},
}

_reg_index = 0

STAGES: dict[str, dict] = {}


def register_stage(stage, before: str = "", after: str = ""):
    """Register a pipeline stage with optional ordering hints.

    Args:
        stage: A PipelineStage-compatible object with .name, .order, .process(context).
        before: Name of existing stage this should run before.
        after: Name of existing stage this should run after.
    """
    global _reg_index
    if not hasattr(stage, "name") or not stage.name:
        raise ValueError("Stage must have a non-empty 'name' attribute")
    if before and after:
        raise ValueError("Use either 'before' or 'after', not both")

    if before and before in STAGES:
        existing = STAGES[before]
        stage.order = existing["stage"].order - 1
    elif after and after in STAGES:
        existing = STAGES[after]
        stage.order = existing["stage"].order + 1

    stage._reg_index = _reg_index
    _reg_index += 1
    STAGES[stage.name] = {"stage": stage, "before": before, "after": after}


def build_pipeline(stage_names=None):
    """Build an ordered list of PipelineStage instances from registered stages.

    Args:
        stage_names: Optional list of stage names to include. If None, all stages.

    Returns:
        List of PipelineStage instances sorted by .order, then registration order.
    """
    names = stage_names if stage_names is not None else list(STAGES.keys())
    result = []
    for name in names:
        if name in STAGES:
            result.append(STAGES[name]["stage"])
    return sorted(result, key=lambda s: (s.order, s._reg_index))


_health_listeners = []


def add_health_listener(fn):
    _health_listeners.append(fn)


def _sorted_callables(name: str) -> list:
    items = [(getattr(fn, "hook_priority", 100), i, fn)
             for i, fn in enumerate(HOOKS[name])]
    items.sort(key=lambda x: (x[0], x[1]))
    return [fn for _, _, fn in items]


def register_plugin_capability(fn, capabilities: set):
    PLUGIN_CAPABILITIES[id(fn)] = capabilities


def _restrict_ctx_for_plugin(fn, ctx: dict, hook_name: str) -> dict:
    if id(fn) in PLUGIN_CAPABILITIES:
        caps = PLUGIN_CAPABILITIES[id(fn)]
    else:
        caps = CAPABILITY_MAP.get(hook_name, set())
    scoped = {}
    for k, v in ctx.items():
        if k.startswith("_"):
            scoped[k] = v
        elif k == "input_text" and "input_read" in caps:
            scoped[k] = v
        elif k == "kernel" and "kernel_access" in caps:
            scoped[k] = v
        elif k in ("mcxf", "mel_result", "feedback", "execution_plan") and "result_read" in caps:
            scoped[k] = v
        elif k in ("execution_plan", "optimized_plan") and "plan_read" in caps:
            scoped[k] = v
        elif k == "mem_id" and "result_read" in caps:
            scoped[k] = v
        elif k not in ("kernel", "input_text", "mcxf", "mel_result", "feedback", "execution_plan", "optimized_plan", "mem_id"):
            scoped[k] = v
    scoped["_capability_scope"] = caps
    return scoped


class _PluginTimeout(Exception):
    pass


def _timeout_handler(signum, frame):
    raise _PluginTimeout("Plugin callback timed out")


def run_hooks(name: str, ctx: dict):
    ctx["_hook_name"] = name
    ordered = _sorted_callables(name)
    for fn in ordered:
        try:
            if _HAS_SIGALRM:
                _signal.signal(_signal.SIGALRM, _timeout_handler)
                _signal.alarm(_PLUGIN_TIMEOUT_SECONDS)
            scoped_ctx = _restrict_ctx_for_plugin(fn, ctx, name)
            fn(scoped_ctx)
        except _PluginTimeout:
            _traceback.print_exc()
            if fn in HOOKS[name]:
                HOOKS[name].remove(fn)
            for listener in _health_listeners:
                try:
                    listener({"hook": name, "plugin": str(fn), "timeout": True})
                except Exception:
                    pass
        except Exception:
            _traceback.print_exc()
            if fn in HOOKS[name]:
                HOOKS[name].remove(fn)
            for listener in _health_listeners:
                try:
                    listener({"hook": name, "plugin": str(fn)})
                except Exception:
                    pass
        finally:
            if _HAS_SIGALRM:
                _signal.alarm(0)
