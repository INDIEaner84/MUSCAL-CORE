import re

BLOCKED_TOOLS = {"shell.exec", "subprocess.run", "os.system", "exec", "eval", "__import__"}
BLOCKED_KEYWORDS = ["import os", "import subprocess", "os.system", "subprocess.run", "eval(", "exec("]

HIGH_RISK_TOOLS = {
    "browser.open", "browser.click", "browser.type",
    "browser.extract_text", "browser.screenshot", "browser.scroll",
    "opencode.run",
    "desktop.screenshot", "desktop.type", "desktop.click",
    "desktop.open_app", "desktop.move", "desktop.keypress",
}

MEDIUM_RISK_TOOLS = {"filesystem.write", "file.write"}

LOW_RISK_TOOLS = {"console.print", "math.add"}

RISK_CLASSIFICATION = {}
for t in LOW_RISK_TOOLS:
    RISK_CLASSIFICATION[t] = "low"
for t in MEDIUM_RISK_TOOLS:
    RISK_CLASSIFICATION[t] = "medium"
for t in HIGH_RISK_TOOLS:
    RISK_CLASSIFICATION[t] = "high"

DEFAULT_ALLOWED_TOOLS = set(LOW_RISK_TOOLS | MEDIUM_RISK_TOOLS)
DEFAULT_HIGH_RISK_ALLOWED = set()


class SafetyResult:
    __slots__ = ("allowed", "reason", "risk", "tool", "details")

    def __init__(self, allowed=True, reason="", risk="low", tool="", details=None):
        self.allowed = allowed
        self.reason = reason
        self.risk = risk
        self.tool = tool
        self.details = details or {}

    def to_dict(self):
        return {
            "allowed": self.allowed,
            "reason": self.reason,
            "risk": self.risk,
            "tool": self.tool,
            "details": self.details,
        }


class SafetyGate:
    def __init__(self, allowed_tools=None, high_risk_allowed=None, user_policy=None):
        self._allowed_tools = set(allowed_tools) if allowed_tools else set(DEFAULT_ALLOWED_TOOLS)
        self._high_risk_allowed = set(high_risk_allowed) if high_risk_allowed else set(DEFAULT_HIGH_RISK_ALLOWED)
        self._user_policy = user_policy or {"allow_high_risk": False}

    def check(self, tool_name, args=None):
        args = args or {}

        if tool_name in BLOCKED_TOOLS:
            return SafetyResult(
                allowed=False, reason=f"BLOCKED_TOOL: {tool_name}",
                risk="critical", tool=tool_name,
            )

        text = str(args)
        for kw in BLOCKED_KEYWORDS:
            if kw in text:
                return SafetyResult(
                    allowed=False, reason=f"HIDDEN_COMMAND: {kw}",
                    risk="critical", tool=tool_name,
                )

        if tool_name not in RISK_CLASSIFICATION:
            return SafetyResult(
                allowed=False, reason=f"UNKNOWN_TOOL: '{tool_name}' is not classified",
                risk="unknown", tool=tool_name,
            )

        risk = RISK_CLASSIFICATION[tool_name]

        if risk == "high":
            if tool_name not in self._high_risk_allowed:
                return SafetyResult(
                    allowed=False, reason=f"HIGH_RISK_BLOCKED: '{tool_name}' requires explicit permit() and allow_high_risk=True",
                    risk="high", tool=tool_name,
                )
            if not self._user_policy.get("allow_high_risk", False):
                return SafetyResult(
                    allowed=False, reason=f"HIGH_RISK_BLOCKED: '{tool_name}' requires allow_high_risk=True",
                    risk="high", tool=tool_name,
                )
        elif tool_name not in self._allowed_tools:
            return SafetyResult(
                allowed=False, reason=f"TOOL_NOT_ALLOWED: '{tool_name}' (risk={risk})",
                risk=risk, tool=tool_name,
            )

        if tool_name in ("filesystem.write", "file.write"):
            path = args.get("path", "")
            if ".." in path.split(os.sep):
                return SafetyResult(
                    allowed=False, reason=f"PATH_TRAVERSAL: '{path}'",
                    risk="high", tool=tool_name,
                    details={"path": path},
                )
            if re.search(r'[;&|`$(){}\n\r]', path):
                return SafetyResult(
                    allowed=False, reason=f"SHELL_METACHARACTERS_IN_PATH: '{path}'",
                    risk="high", tool=tool_name,
                    details={"path": path},
                )

        if tool_name.startswith("browser."):
            url = args.get("url", "")
            if tool_name == "browser.open" and url:
                if not url.startswith(("http://", "https://")):
                    return SafetyResult(
                        allowed=False, reason=f"INVALID_URL: '{url}' must start with http:// or https://",
                        risk="medium", tool=tool_name,
                        details={"url": url},
                    )

        if isinstance(args, dict):
            for k, v in args.items():
                if isinstance(v, str):
                    if re.search(r'[;&|`$(){}\n\r]', v):
                        return SafetyResult(
                            allowed=False, reason=f"SHELL_METACHARACTERS in args['{k}']",
                            risk="high", tool=tool_name,
                            details={"key": k, "value": v[:100]},
                        )

        return SafetyResult(allowed=True, risk=risk, tool=tool_name)

    def permit(self, tool_name):
        risk = RISK_CLASSIFICATION.get(tool_name, "unknown")
        self._allowed_tools.add(tool_name)
        if risk == "high":
            self._high_risk_allowed.add(tool_name)

    def deny(self, tool_name):
        self._allowed_tools.discard(tool_name)
        self._high_risk_allowed.discard(tool_name)

    def risk_of(self, tool_name):
        return RISK_CLASSIFICATION.get(tool_name, "unknown")

    def is_allowed(self, tool_name):
        if tool_name in BLOCKED_TOOLS:
            return False
        risk = RISK_CLASSIFICATION.get(tool_name, "unknown")
        if tool_name not in self._allowed_tools:
            if risk == "high" and self._user_policy.get("allow_high_risk"):
                return tool_name in self._high_risk_allowed
            return False
        if risk == "high" and not self._user_policy.get("allow_high_risk"):
            return False
        return True


import os

DEFAULT_SAFETY_GATE = SafetyGate()
