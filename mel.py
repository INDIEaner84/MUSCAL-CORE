import threading
import warnings

from tools import TOOL_REGISTRY

_runtime = None
_lock = threading.RLock()

_utr = None
_utr_lock = threading.RLock()


def _register_tools_to_utr(utr):
    from features.tool_runtime.tool_runtime import BrowserAgent
    ba = BrowserAgent(headless=False)
    for name, fn in TOOL_REGISTRY.items():
        def make_wrapper(f):
            return lambda args: f(**args)
        utr.register_tool(name, make_wrapper(fn))


def _get_utr():
    global _utr
    with _utr_lock:
        if _utr is None:
            from features.safety.safety_gate import SafetyGate
            sg = SafetyGate(user_policy={"allow_high_risk": True})
            from features.tool_runtime.tool_runtime import create_default_utr
            _utr, _ba = create_default_utr(safety_gate=sg)
            _register_tools_to_utr(_utr)
        return _utr


def _get_runtime():
    global _runtime
    with _lock:
        if _runtime is None:
            from system_runtime import SystemAgentRuntime
            _runtime = SystemAgentRuntime()
        return _runtime


def _execute_step(step: dict) -> dict:
    tool_name = step["tool"]
    if tool_name == "UNMAPPED":
        return {
            "tool": "UNMAPPED",
            "original_task": step.get("original_task", ""),
            "reason": step.get("reason", ""),
            "status": "skipped",
        }
    utr = _get_utr()
    args = step.get("args", {})
    result = utr.execute(tool_name, args)
    if result.success:
        base = result.output if isinstance(result.output, dict) else {"output": result.output}
        base.setdefault("tool", tool_name)
        base.setdefault("status", "success")
        return base
    if result.error and "Unknown tool" in result.error:
        if tool_name.startswith("browser.") or tool_name.startswith("desktop."):
            return _get_runtime().execute(step)
        raise Exception(f"Unknown tool: {tool_name}")
    return {"tool": tool_name, "status": "error", "error": result.error}


def execute(plan):
    results = []

    if hasattr(plan, "layers"):
        for layer_nodes in plan.layers:
            for step in layer_nodes:
                result = _execute_step(step)
                results.append(result)
    elif hasattr(plan, "steps"):
        for step in plan.steps:
            result = _execute_step(step)
            results.append(result)
    else:
        for step in plan:
            result = _execute_step(step)
            results.append(result)

    return results
