"""Research Memory - research pipeline abstraction (future-proofing).

Research Memory itself NEVER browses. To compute a fresh answer it relies on an
external "pipeline" (today Browser Intelligence, tomorrow web_search, Knowledge
Foundation, ...). Defining the contract here keeps Research Memory decoupled
from any concrete provider (no import of browser_intelligence anywhere).

A pipeline is anything providing ``research(query, context="", **opts)`` that
returns a mapping shaped like a ResearchRecord payload (facts/analysis/... or
FACTS/ANALYSIS/... uppercased - both are accepted).
"""

from __future__ import annotations

import asyncio


class ResearchPipeline:
    """Interface for computing fresh research results."""

    name = "abstract"

    def research(self, query: str, context: str = "", **opts) -> dict:
        raise NotImplementedError

    async def research_async(self, query: str, context: str = "", **opts) -> dict:
        return await asyncio.to_thread(self.research, query, context=context, **opts)


class FunctionResearchPipeline(ResearchPipeline):
    """Adapter over any plain callable (e.g. a Browser Intelligence accessor)."""

    def __init__(self, fn, name: str = "function") -> None:
        self._fn = fn
        self.name = name

    def research(self, query: str, context: str = "", **opts) -> dict:
        return self._fn(query, context=context, **opts)


def normalize_payload(payload: dict) -> dict:
    """Accept both ResearchRecord-field and uppercased pipeline payloads."""
    if not isinstance(payload, dict):
        return {}
    mapping = {
        "facts": "facts",
        "sources": "sources",
        "options": "options",
        "analysis": "analysis",
        "recommendation": "recommendation",
        "confidence": "confidence",
    }
    out: dict = {}
    for key, canonical in mapping.items():
        value = payload.get(key)
        if value is None:
            value = payload.get(key.upper())
        if value is not None:
            out[canonical] = value
    return out