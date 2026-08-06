"""Browser Intelligence - ResearchService facade.

Sync API for convenience (CLI, tests), async API for embedding.
Provider selection is pluggable: browser_use today, MCP / web_search later.
"""

from __future__ import annotations

import asyncio

from .models import ResearchFindings
from .providers import get_provider


class ResearchService:

    def __init__(self, provider: str = "browser_use"):
        self.provider_name = provider
        self._provider = get_provider(provider)

    async def research_async(
        self,
        question: str,
        topic: str = "",
        constraints: list | None = None,
    ) -> ResearchFindings:
        return await self._provider.research(question, topic=topic, constraints=constraints)

    def research(
        self,
        question: str,
        topic: str = "",
        constraints: list | None = None,
    ) -> ResearchFindings:
        return asyncio.run(self.research_async(question, topic, constraints))
