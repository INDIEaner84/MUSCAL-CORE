ALLOWED_TOOLS = {
    "console.print": {"risk": "low"},
    "file.read": {"risk": "low"},
    "file.write": {"risk": "medium"},
    "browser.open": {"risk": "high"},
    "browser.click": {"risk": "high"},
    "browser.type": {"risk": "high"},
    "opencode.run": {"risk": "high"},
}


class PermissionEngine:
    def __init__(self, user_policy=None):
        self.user_policy = user_policy or {"allow_high_risk": False}

    def check(self, tool_name, mcxf_context=None):
        if tool_name not in ALLOWED_TOOLS:
            return False, "UNKNOWN_TOOL"
        risk = ALLOWED_TOOLS[tool_name]["risk"]
        if risk == "high" and not self.user_policy["allow_high_risk"]:
            return False, "HIGH_RISK_BLOCKED"
        return True, "OK"


class ToolExecutor:
    def __init__(self):
        from muscal_loop import EXECUTORS
        self._executors = EXECUTORS

    def run(self, tool_name, args):
        fn = self._executors.get(tool_name)
        if fn is None:
            return {"status": "error", "tool": tool_name, "error": "unknown_tool"}
        try:
            result = fn(args)
            if isinstance(result, dict):
                result.setdefault("status", "executed")
            result["tool"] = tool_name
            return result
        except Exception as e:
            return {"tool": tool_name, "status": "error", "error": str(e)}


class ExecutionFirewall:
    def __init__(self, permission_engine, tool_executor):
        self.perm = permission_engine
        self.exec = tool_executor

    def run(self, tool_name, args, context=None):
        allowed, reason = self.perm.check(tool_name, context)
        if not allowed:
            return {"status": "BLOCKED", "tool": tool_name, "reason": reason}
        return self.exec.run(tool_name, args)


_perm = PermissionEngine()
_executor = ToolExecutor()
_firewall = ExecutionFirewall(_perm, _executor)


def mel_execute(task):
    return _firewall.run(task.get("tool", ""), task.get("args", {}), context=task)


def run_muscal(mcxf_tasks):
    from execution_governor import ExecutionGovernor
    from loop_controller import LoopController
    loop = LoopController(max_iterations=5)
    governor = ExecutionGovernor(mel_execute, loop)
    return governor.run(mcxf_tasks)
