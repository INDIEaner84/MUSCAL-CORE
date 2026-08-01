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
        self._utr = None

    def _get_utr(self):
        if self._utr is None:
            from features.tool_runtime.tool_runtime import create_default_utr
            from features.safety.safety_gate import SafetyGate
            sg = SafetyGate()
            sg.permit("console.print")
            sg.permit("filesystem.write")
            sg.permit("file.write")
            sg.permit("math.add")
            sg.permit("browser.open")
            sg.permit("browser.click")
            sg.permit("browser.type")
            sg.permit("opencode.run")
            self._utr, _ = create_default_utr(safety_gate=sg)
        return self._utr

    def run(self, tool_name, args):
        utr = self._get_utr()
        result = utr.execute(tool_name, args)
        if result.success:
            base = result.output if isinstance(result.output, dict) else {"output": result.output}
            base.setdefault("tool", tool_name)
            base.setdefault("status", "executed")
            return base
        return {"tool": tool_name, "status": "error", "error": result.error}


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
