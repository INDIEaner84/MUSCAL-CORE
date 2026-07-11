import logging
from concurrent.futures import Future

import config
from runtime.kernel.sanitizer import validate_no_injection
from runtime.llm.client import _ollama_call_async, _ollama_generate, _ollama_ping

log = logging.getLogger("muscal.llm.models")


def ask_smol(prompt: str, system: str = "") -> str:
    _, system = validate_no_injection(system)
    _, prompt = validate_no_injection(prompt)
    future = _ollama_call_async(_ollama_generate, config.SMOL_MODEL, prompt,
                                system=system, keep_alive=-1, timeout=10)
    return future.result(timeout=15)


def ask_qwen(prompt: str, system: str = "") -> str:
    _, system = validate_no_injection(system)
    _, prompt = validate_no_injection(prompt)
    future = _ollama_call_async(_ollama_generate, config.QWEN_MODEL, prompt,
                                system=system, keep_alive=-1, timeout=60)
    return future.result(timeout=70)


def ask_r1(prompt: str, system: str = "") -> str:
    _, system = validate_no_injection(system)
    _, prompt = validate_no_injection(prompt)
    future = _ollama_call_async(_ollama_generate, config.R1_MODEL, prompt,
                                system=system, keep_alive=config.R1_KEEP_ALIVE, timeout=120)
    return future.result(timeout=130)


def init_router() -> bool:
    log.info("Initializing Qwen router: %s", config.QWEN_MODEL)
    if not _ollama_ping():
        log.warning("Ollama not reachable \u2014 router init skipped")
        return False
    resp = _ollama_generate(config.QWEN_MODEL, "OK", keep_alive=-1, timeout=180)
    ok = bool(resp and "OLLAMA_ERROR" not in resp)
    if ok:
        log.info("Router ready")
    else:
        log.warning("Router init failed: %s", resp[:80] if resp else "no response")
    return ok


def init_smol() -> bool:
    log.info("Initializing SMOL: %s", config.SMOL_MODEL)
    if not _ollama_ping():
        log.warning("Ollama not reachable \u2014 smol init skipped")
        return False
    resp = _ollama_generate(config.SMOL_MODEL, "OK", keep_alive=-1, timeout=60)
    ok = bool(resp and "OLLAMA_ERROR" not in resp)
    if ok:
        log.info("SMOL ready")
    else:
        log.warning("SMOL init failed: %s", resp[:80] if resp else "no response")
    return ok
