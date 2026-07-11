import json
import logging
import time
import urllib.error
import urllib.request
from concurrent.futures import Future, ThreadPoolExecutor
from typing import Optional

import config

log = logging.getLogger("muscal.llm")

_ollama_available: Optional[bool] = None
_ollama_last_fail: float = 0.0
_ollama_retry_delay: float = 30.0
_ollama_executor: Optional[ThreadPoolExecutor] = None


def _get_executor() -> ThreadPoolExecutor:
    global _ollama_executor
    if _ollama_executor is None:
        _ollama_executor = ThreadPoolExecutor(max_workers=2, thread_name_prefix="ollama")
    return _ollama_executor


def _ollama_generate(model: str, prompt: str, system: str = "",
                     timeout: int = 60, keep_alive: int = -1) -> str:
    payload = {
        "model": model, "prompt": prompt, "stream": False,
        "keep_alive": keep_alive,
    }
    if system:
        payload["system"] = system
    data = json.dumps(payload).encode()
    req = urllib.request.Request(
        f"{config.OLLAMA_BASE}/api/generate",
        data=data, method="POST",
        headers={"Content-Type": "application/json"}
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            result = json.loads(resp.read())
            return result.get("response", "")
    except Exception as e:
        log.warning("Ollama error [%s]: %s", model, e)
        return f"[OLLAMA_ERROR: {e}]"


def _ollama_call_async(fn, *args, **kwargs) -> Future:
    return _get_executor().submit(fn, *args, **kwargs)


def _ollama_ping(timeout: int = 3) -> bool:
    global _ollama_available, _ollama_last_fail
    if _ollama_available is False:
        if time.monotonic() - _ollama_last_fail < _ollama_retry_delay:
            return False
    try:
        with urllib.request.urlopen(f"{config.OLLAMA_BASE}/api/tags", timeout=timeout):
            _ollama_available = True
            return True
    except Exception:
        _ollama_available = False
        _ollama_last_fail = time.monotonic()
        return False


def ollama_keepalive(model: str) -> None:
    try:
        payload = json.dumps({
            "model": model, "prompt": "OK", "stream": False,
            "keep_alive": -1,
        }).encode()
        req = urllib.request.Request(
            f"{config.OLLAMA_BASE}/api/generate", data=payload,
            method="POST", headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=5):
            pass
    except Exception:
        pass
