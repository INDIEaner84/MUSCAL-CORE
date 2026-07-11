import threading

from tools import TOOL_REGISTRY

_runtime = None
_lock = threading.RLock()


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
    if tool_name.startswith("browser.") or tool_name.startswith("desktop."):
        return _get_runtime().execute(step)
    if tool_name not in TOOL_REGISTRY:
        raise Exception(f"Unknown tool: {tool_name}")
    args = step["args"]
    return TOOL_REGISTRY[tool_name](**args)


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
