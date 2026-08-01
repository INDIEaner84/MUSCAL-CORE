import os
import time
from typing import Any, Dict, Optional

RUNTIME_CANONICAL_VERSION = "1.0.0"
RUNTIME_CANONICAL_STATUS = "ACTIVE"

_shared_state: Dict[str, Any] = {
    "server_ready": False,
    "start_time": time.monotonic(),
    "tool_runtime": None,
    "safety_gate": None,
    "governance": None,
    "auth_token": "",
}

_AUTH_REQUIRED_GET_PREFIXES = ("/admin", "/governance", "/snapshot", "/handoff")
_PUBLIC_PATHS = {"/health", "/state", "/live"}
_SECURITY_HEADERS = {
    "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
    "X-Frame-Options": "DENY",
    "X-Content-Type-Options": "nosniff",
    "X-XSS-Protection": "0",
    "Content-Security-Policy": "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'",
    "Referrer-Policy": "strict-origin-when-cross-origin",
}


def init_canonical_runtime(tool_runtime=None, safety_gate=None, governance=None):
    _shared_state["start_time"] = time.monotonic()
    _shared_state["tool_runtime"] = tool_runtime
    _shared_state["safety_gate"] = safety_gate
    _shared_state["governance"] = governance
    _shared_state["auth_token"] = os.environ.get("MUSCAL_API_KEY", "")
    return _shared_state


def get_auth_token() -> str:
    token = _shared_state["auth_token"]
    if not token:
        try:
            import config
            token = getattr(config, "SESSION_ID", "")
        except (ImportError, AttributeError):
            pass
    return token


def is_auth_required(path: str, method: str) -> bool:
    if method == "OPTIONS":
        return False
    stripped = path.rstrip("/")
    if stripped in _PUBLIC_PATHS:
        return False
    if method == "GET" and not stripped.startswith(_AUTH_REQUIRED_GET_PREFIXES):
        return False
    return bool(get_auth_token())


def set_server_ready(val: bool = True):
    _shared_state["server_ready"] = val


def is_server_ready() -> bool:
    return _shared_state["server_ready"]


def get_security_headers() -> Dict[str, str]:
    return dict(_SECURITY_HEADERS)


def get_shared_state() -> Dict[str, Any]:
    return dict(_shared_state)


def check_tool_via_kernel(tool_name: str, args: dict, task_type: str = "general") -> Dict[str, Any]:
    safety = _shared_state.get("safety_gate")
    if safety:
        sg_result = safety.check(tool_name, args)
        if not sg_result.allowed:
            return {"status": "blocked_by_safety", "reason": sg_result.reason}

    utr = _shared_state.get("tool_runtime")
    if not utr:
        return {"status": "no_runtime", "error": "Tool runtime not initialized"}

    result = utr.execute(tool_name, args)
    return {
        "status": "success" if result.success else "error",
        "output": result.output,
        "error": result.error,
    }
