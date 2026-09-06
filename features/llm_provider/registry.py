"""
LLM Provider Registry - Maps roles to providers and handles routing.

Reuses existing CapabilityRegistry pattern from features/capability_registry/
"""

from typing import Dict, List, Optional

from features.llm_provider.protocol import LLMProvider


class TaskFit:
    """Describes how well a provider fits a task."""
    def __init__(
        self,
        required_capabilities: Optional[List[str]] = None,
        max_cost_per_token: Optional[float] = None,
        max_latency_ms: Optional[int] = None,
        preferred_provider: Optional[str] = None
    ):
        self.required_capabilities = required_capabilities or []
        self.max_cost_per_token = max_cost_per_token
        self.max_latency_ms = max_latency_ms
        self.preferred_provider = preferred_provider


class LLMProviderRegistry:
    """Maps role -> provider_id -> LLMProvider. Provider-agnostic."""

    def __init__(self):
        self._providers: Dict[str, Dict[str, LLMProvider]] = {}  # role -> {provider_id: provider}
        self._default_for_role: Dict[str, str] = {}  # role -> provider_id

    def register(
        self,
        role: str,
        provider_id: str,
        provider: LLMProvider,
        set_default: bool = False,
    ) -> None:
        """Register a provider for a role."""
        if role not in self._providers:
            self._providers[role] = {}
        self._providers[role][provider_id] = provider
        if set_default or role not in self._default_for_role:
            self._default_for_role[role] = provider_id

    def resolve(self, role: str, task_fit: Optional[TaskFit] = None) -> LLMProvider:
        """Resolve the best provider for a role."""
        if role not in self._providers or not self._providers[role]:
            raise ValueError(f"No providers registered for role: {role}")

        providers = self._providers[role]

        # If specific provider requested
        if task_fit and task_fit.preferred_provider:
            if task_fit.preferred_provider in providers:
                provider = providers[task_fit.preferred_provider]
                if not provider.is_available:
                    raise ValueError(
                        f"Preferred provider {task_fit.preferred_provider} not available"
                    )
                return provider
            raise ValueError(
                f"Preferred provider {task_fit.preferred_provider} not registered for role {role}"
            )

        # Return default (if available)
        default_id = self._default_for_role.get(role)
        if default_id and default_id in providers:
            provider = providers[default_id]
            if provider.is_available:
                return provider
            # Default not available, fall through to find available

        # Fallback: first available
        for pid, provider in providers.items():
            if provider.is_available:
                return provider

        raise ValueError(f"No available providers for role: {role}")

    def list_providers(self, role: str) -> List[str]:
        """List all provider IDs for a role."""
        return list(self._providers.get(role, {}).keys())

    def get_default(self, role: str) -> Optional[str]:
        """Get default provider ID for a role."""
        return self._default_for_role.get(role)

    def set_default(self, role: str, provider_id: str) -> None:
        """Set default provider for a role."""
        if role in self._providers and provider_id in self._providers[role]:
            self._default_for_role[role] = provider_id
        else:
            raise ValueError(f"Provider {provider_id} not registered for role {role}")


# Global registry instance
llm_provider_registry = LLMProviderRegistry()
