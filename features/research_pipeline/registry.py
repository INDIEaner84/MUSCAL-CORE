"""Research Pipeline - provider registry.

Named provider registry with lazy factories so nothing heavy is imported at
module load time (the plugin loader imports every .py under features/).

Initial provider: ``browser_intelligence``.
Extension points prepared (not yet registered):
    - ``github``            (future)
    - ``documentation``     (future)
    - ``local_knowledge``   (future)
"""

from __future__ import annotations

from typing import Callable

from .interfaces import ResearchProvider

ProviderFactory = Callable[[], ResearchProvider]


class ResearchProviderRegistry:

    def __init__(self) -> None:
        self._factories: dict[str, ProviderFactory] = {}
        self._instances: dict[str, ResearchProvider] = {}

    def register(self, name: str, factory: ProviderFactory) -> None:
        if not name or not name.strip():
            raise ValueError("provider name is required")
        self._factories[name.strip()] = factory

    def register_instance(self, name: str, provider: ResearchProvider) -> None:
        self._instances[name.strip()] = provider

    def unregister(self, name: str) -> bool:
        name = name.strip()
        self._instances.pop(name, None)
        return self._factories.pop(name, None) is not None

    def get(self, name: str) -> ResearchProvider:
        name = name.strip()
        if name in self._instances:
            return self._instances[name]
        factory = self._factories.get(name)
        if factory is None:
            raise ValueError(f"unknown research provider: {name!r}")
        provider = factory()
        self._instances[name] = provider
        return provider

    def names(self) -> list[str]:
        return sorted(set(self._factories) | set(self._instances))


def _browser_intelligence_factory() -> ResearchProvider:
    from .adapters.browser_intelligence import BrowserIntelligenceAdapter

    return BrowserIntelligenceAdapter()


_registry: ResearchProviderRegistry | None = None


def get_default_registry() -> ResearchProviderRegistry:
    global _registry
    if _registry is None:
        _registry = ResearchProviderRegistry()
        _registry.register("browser_intelligence", _browser_intelligence_factory)
    return _registry