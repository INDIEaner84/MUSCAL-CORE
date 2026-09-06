"""
LLM Provider Protocol for Provider-Agnostic Multi-LLM Architecture.

Defines the interface that all LLM providers must implement.
"""

from typing import Any, Dict, List, Optional, Protocol


class LLMProvider(Protocol):
    """Provider-agnostic interface for LLM interactions."""

    @property
    def provider_id(self) -> str: ...

    @property
    def is_available(self) -> bool: ...

    def analyze(
        self,
        task: str,
        context: Dict[str, Any],
        structured_output_schema: Optional[Dict] = None
    ) -> Dict[str, Any]: ...

    def chat(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.0,
        max_tokens: Optional[int] = None,
        structured_output_schema: Optional[Dict] = None
    ) -> Dict[str, Any]: ...

    def get_capabilities(self) -> List[str]: ...

    def get_metrics(self) -> Dict[str, Any]: ...
