"""Research Pipeline - provider interface.

The pipeline layer talks to research providers ONLY through this abstract
interface. Concrete providers (Browser Intelligence today; github, docs, local
knowledge tomorrow) are wrapped by adapters that normalize results.
"""

from __future__ import annotations

import abc

from .models import ResearchRequest, ResearchResult


class ResearchProviderError(Exception):
    """Raised when a provider fails or returns unusable output."""


class ResearchProvider(abc.ABC):
    """A source of fresh research results (no memory, no caching)."""

    name: str = "abstract"

    @abc.abstractmethod
    async def research(self, request: ResearchRequest) -> ResearchResult:
        raise NotImplementedError