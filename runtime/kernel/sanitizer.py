import json
import logging
from typing import Any

log = logging.getLogger(__name__)

_MASKED_KEYS = frozenset({
    "api_key", "token", "password", "secret", "credential",
    "auth", "authorization", "bearer", "private_key",
    "session_id", "model_id", "idempotency_key",
    "actor", "worker_id",
})

_INJECTION_PATTERNS = [
    "[SYSTEM", "ignore previous", "forget instructions",
    "```python", "```bash", "```sh",
    "import os", "subprocess", "__import__",
    "eval(", "exec(", "open(",
]

_MAX_STRING_LEN = 2048
_MAX_LIST_ITEMS = 50
_MAX_PAYLOAD_BYTES = 8192


def sanitize_payload(obj: Any, depth: int = 0) -> Any:
    if depth > 6:
        return "[MAX_DEPTH]"
    if isinstance(obj, dict):
        return {
            k: "[MASKED]" if k.lower() in _MASKED_KEYS else sanitize_payload(v, depth + 1)
            for k, v in obj.items()
        }
    if isinstance(obj, list):
        return [sanitize_payload(x, depth + 1) for x in obj[:_MAX_LIST_ITEMS]]
    if isinstance(obj, str):
        for pattern in _INJECTION_PATTERNS:
            if pattern.lower() in obj.lower():
                return "[SANITIZED: suspicious content removed]"
        return obj[:_MAX_STRING_LEN] if len(obj) > _MAX_STRING_LEN else obj
    return obj


def build_llm_context(events: list[dict], max_tokens: int = 1500) -> str:
    safe_events = []
    budget = max_tokens * 4

    for ev in reversed(events):
        safe_ev = dict(ev)
        if "payload" in safe_ev:
            try:
                payload = json.loads(safe_ev["payload"]) if isinstance(safe_ev["payload"], str) else safe_ev["payload"]
                safe_ev["payload"] = sanitize_payload(payload)
            except (json.JSONDecodeError, TypeError):
                safe_ev["payload"] = "[PARSE_ERROR]"

        if safe_ev.get("stream") == "reasoning":
            safe_ev["_note"] = "[REASONING STREAM \u2014 nicht Ground Truth]"

        serialized = json.dumps(safe_ev, ensure_ascii=False)
        if len(serialized) > budget:
            break
        safe_events.insert(0, safe_ev)
        budget -= len(serialized)

    result = json.dumps(safe_events, ensure_ascii=False, indent=2)
    if len(result) > _MAX_PAYLOAD_BYTES * 4:
        result = result[:_MAX_PAYLOAD_BYTES * 4] + "\n...[TRUNCATED]"
    return result


def validate_no_injection(text: str) -> tuple[bool, str]:
    if not isinstance(text, str):
        return True, str(text)
    for pattern in _INJECTION_PATTERNS:
        if pattern.lower() in text.lower():
            log.warning("validate_no_injection: pattern '%s' found", pattern)
            return False, f"[SANITIZED: pattern '{pattern}' removed]"
    return True, text
