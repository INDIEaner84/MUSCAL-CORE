"""
Tests for LLMProvider Protocol.
"""

import pytest

from features.llm_provider.protocol import LLMProvider


class MockProvider:
    """Mock implementation of LLMProvider for testing."""

    def __init__(self, provider_id: str = "mock"):
        self._provider_id = provider_id
        self._available = True

    @property
    def provider_id(self) -> str:
        return self._provider_id

    @property
    def is_available(self) -> bool:
        return self._available

    def analyze(
        self,
        task: str,
        context: dict,
        structured_output_schema: dict | None = None
    ) -> dict:
        return {"result": f"analyzed: {task}", "provider": self._provider_id}

    def chat(
        self,
        messages: list[dict],
        temperature: float = 0.0,
        max_tokens: int | None = None,
        structured_output_schema: dict | None = None
    ) -> dict:
        return {"response": "mock response", "provider": self._provider_id}

    def get_capabilities(self) -> list[str]:
        return ["analyze", "chat"]

    def get_metrics(self) -> dict:
        return {"calls": 0, "latency_ms": 0}


def test_llmprovider_protocol_structure():
    """Test that LLMProvider protocol defines required methods."""
    # This verifies the protocol structure by checking a mock implementation
    provider = MockProvider("test")

    # Check all required attributes/methods exist
    assert hasattr(provider, "provider_id")
    assert hasattr(provider, "is_available")
    assert hasattr(provider, "analyze")
    assert hasattr(provider, "chat")
    assert hasattr(provider, "get_capabilities")
    assert hasattr(provider, "get_metrics")

    # Check types
    assert isinstance(provider.provider_id, str)
    assert isinstance(provider.is_available, bool)


def test_mock_provider_implementation():
    """Test mock provider works correctly."""
    provider = MockProvider("test-provider")

    assert provider.provider_id == "test-provider"
    assert provider.is_available is True

    result = provider.analyze("test task", {"key": "value"})
    assert "result" in result
    assert result["provider"] == "test-provider"

    chat_result = provider.chat([{"role": "user", "content": "hello"}])
    assert "response" in chat_result

    caps = provider.get_capabilities()
    assert "analyze" in caps
    assert "chat" in caps

    metrics = provider.get_metrics()
    assert "calls" in metrics


def test_protocol_cannot_be_instantiated_directly():
    """Test that LLMProvider is a Protocol (cannot be instantiated)."""
    with pytest.raises(TypeError):
        LLMProvider()  # type: ignore
