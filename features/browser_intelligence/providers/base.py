"""Browser Intelligence - provider abstraction."""

from __future__ import annotations

from abc import ABC, abstractmethod

from ..models import ResearchFindings


class ResearchProvider(ABC):

    name: str = "base"

    @abstractmethod
    async def research(
        self,
        question: str,
        topic: str = "",
        constraints: list | None = None,
    ) -> ResearchFindings:
        """Run a research task and return structured findings."""
