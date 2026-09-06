"""
Tests for LLMProviderRegistry.
"""

import pytest

from features.llm_provider.registry import (
    LLMProviderRegistry,
    TaskFit,
    llm_provider_registry,
)


class MockProvider:
    """Mock provider for testing."""

    def __init__(self, provider_id: str = "mock", available: bool = True):
        self._provider_id = provider_id
        self._available = available

    @property
    def provider_id(self) -> str:
        return self._provider_id

    @property
    def is_available(self) -> bool:
        return self._available

    def analyze(
        self, task: str, context: dict, structured_output_schema: dict | None = None
    ) -> dict:
        return {"provider": self._provider_id}

    def chat(self, messages: list[dict], temperature: float = 0.0,
             max_tokens: int | None = None, structured_output_schema: dict | None = None) -> dict:
        return {"provider": self._provider_id}

    def get_capabilities(self) -> list[str]:
        return ["analyze", "chat"]

    def get_metrics(self) -> dict:
        return {}


def test_registry_register_and_resolve():
    """Test basic register and resolve."""
    registry = LLMProviderRegistry()
    provider = MockProvider("test-provider")

    registry.register("auditor", "test-provider", provider, set_default=True)

    resolved = registry.resolve("auditor")
    assert resolved.provider_id == "test-provider"


def test_registry_multiple_providers_same_role():
    """Test multiple providers for same role."""
    registry = LLMProviderRegistry()
    provider1 = MockProvider("provider-1")
    provider2 = MockProvider("provider-2")

    registry.register("auditor", "provider-1", provider1, set_default=True)
    registry.register("auditor", "provider-2", provider2)

    providers = registry.list_providers("auditor")
    assert set(providers) == {"provider-1", "provider-2"}

    # Default should be provider-1
    resolved = registry.resolve("auditor")
    assert resolved.provider_id == "provider-1"


def test_registry_preferred_provider():
    """Test resolving with preferred provider."""
    registry = LLMProviderRegistry()
    provider1 = MockProvider("provider-1")
    provider2 = MockProvider("provider-2")

    registry.register("auditor", "provider-1", provider1, set_default=True)
    registry.register("auditor", "provider-2", provider2)

    task_fit = TaskFit(preferred_provider="provider-2")
    resolved = registry.resolve("auditor", task_fit)
    assert resolved.provider_id == "provider-2"


def test_registry_preferred_provider_not_found():
    """Test error when preferred provider not registered."""
    registry = LLMProviderRegistry()
    provider1 = MockProvider("provider-1")

    registry.register("auditor", "provider-1", provider1)

    task_fit = TaskFit(preferred_provider="non-existent")
    with pytest.raises(ValueError, match="Preferred provider non-existent not registered"):
        registry.resolve("auditor", task_fit)


def test_registry_no_providers_for_role():
    """Test error when no providers for role."""
    registry = LLMProviderRegistry()

    with pytest.raises(ValueError, match="No providers registered for role: unknown"):
        registry.resolve("unknown")


def test_registry_no_available_providers():
    """Test error when all providers unavailable."""
    registry = LLMProviderRegistry()
    provider = MockProvider("unavailable", available=False)

    registry.register("auditor", "unavailable", provider)

    with pytest.raises(ValueError, match="No available providers for role: auditor"):
        registry.resolve("auditor")


def test_registry_set_default():
    """Test setting default provider."""
    registry = LLMProviderRegistry()
    provider1 = MockProvider("provider-1")
    provider2 = MockProvider("provider-2")

    registry.register("auditor", "provider-1", provider1, set_default=True)
    registry.register("auditor", "provider-2", provider2)

    assert registry.get_default("auditor") == "provider-1"

    registry.set_default("auditor", "provider-2")
    assert registry.get_default("auditor") == "provider-2"

    resolved = registry.resolve("auditor")
    assert resolved.provider_id == "provider-2"


def test_registry_set_default_invalid():
    """Test setting default to unregistered provider."""
    registry = LLMProviderRegistry()
    provider = MockProvider("provider-1")

    registry.register("auditor", "provider-1", provider)

    with pytest.raises(ValueError, match="Provider provider-2 not registered"):
        registry.set_default("auditor", "provider-2")


def test_task_fit_creation():
    """Test TaskFit creation with various options."""
    fit = TaskFit(
        required_capabilities=["analyze", "chat"],
        max_cost_per_token=0.001,
        max_latency_ms=5000,
        preferred_provider="specific-provider"
    )

    assert fit.required_capabilities == ["analyze", "chat"]
    assert fit.max_cost_per_token == 0.001
    assert fit.max_latency_ms == 5000
    assert fit.preferred_provider == "specific-provider"


def test_global_registry_exists():
    """Test global registry instance exists."""
    assert llm_provider_registry is not None
    assert isinstance(llm_provider_registry, LLMProviderRegistry)
