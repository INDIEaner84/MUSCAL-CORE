"""Browser Intelligence - LLM resolution.

Returns a browser-use BaseChatModel instance or None. Resolution order
(default):

1. Local Ollama (native ChatOllama) if reachable
2. OPENAI_API_KEY -> ChatOpenAI
3. BROWSER_USE_API_KEY -> ChatBrowserUse
4. None (deterministic extraction mode)

Explicit override via BROWSER_INTEL_LLM=ollama|openai|browseruse|none.
"""

from __future__ import annotations

import os

from .config import get_config


def _ollama_reachable(base_url: str) -> bool:
    try:
        import httpx

        r = httpx.get(base_url.rstrip("/") + "/api/tags", timeout=2.0)
        return r.status_code == 200
    except Exception:
        return False


def _build_ollama():
    from browser_use.llm.ollama.chat import ChatOllama

    cfg = get_config()
    return ChatOllama(
        model=cfg.ollama_model,
        host=cfg.ollama_base,
        ollama_options={
            "num_ctx": 8192,
            "num_predict": 2048,
            "temperature": 0.0,
        },
        timeout=480,
    )


def _build_openai():
    from browser_use.llm.models import ChatOpenAI

    cfg = get_config()
    return ChatOpenAI(model=cfg.openai_model)


def _build_browseruse():
    from browser_use import ChatBrowserUse

    cfg = get_config()
    return ChatBrowserUse(model=cfg.cloud_model)


def resolve_chat_llm():
    """Return a chat model or None. Lazy imports only, safe offline."""
    cfg = get_config()
    override = cfg.llm_provider or os.environ.get("BROWSER_INTEL_LLM", "").lower()

    if override == "none":
        return None
    if override == "ollama":
        return _build_ollama()
    if override == "openai":
        if os.environ.get("OPENAI_API_KEY"):
            return _build_openai()
        return None
    if override == "browseruse":
        if os.environ.get("BROWSER_USE_API_KEY"):
            return _build_browseruse()
        return None

    if _ollama_reachable(cfg.ollama_base):
        try:
            return _build_ollama()
        except Exception:
            pass
    if os.environ.get("OPENAI_API_KEY"):
        try:
            return _build_openai()
        except Exception:
            pass
    if os.environ.get("BROWSER_USE_API_KEY"):
        try:
            return _build_browseruse()
        except Exception:
            pass
    return None


def resolve_synthesis_llm():
    """Return a synthesis-tuned chat model, or None for non-Ollama providers.

    The default chat model requests up to 2048 tokens and a long read budget,
    which is wasteful for the short structured synthesis call and prone to
    timeouts on slow CPU-only Ollama. Synthesis hence uses a bounded model:
    fewer tokens and a shorter timeout, so a slow box degrades to the raw
    extraction instead of blocking.
    """
    cfg = get_config()
    override = cfg.llm_provider or os.environ.get("BROWSER_INTEL_LLM", "").lower()
    if override in ("openai", "browseruse", "none"):
        return None
    wanted = override == "ollama" or _ollama_reachable(cfg.ollama_base)
    if not wanted:
        return None
    try:
        from browser_use.llm.ollama.chat import ChatOllama

        return ChatOllama(
            model=cfg.ollama_model,
            host=cfg.ollama_base,
            ollama_options={
                "num_ctx": 8192,
                "num_predict": cfg.synthesis_max_tokens,
                "temperature": 0.0,
            },
            timeout=cfg.synthesis_timeout_seconds,
        )
    except Exception:
        return None
