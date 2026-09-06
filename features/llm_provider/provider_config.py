"""
LLM Provider Configuration - Env-based configuration.

All provider configuration via environment variables.
No hardcoded model names.
"""

import os
from dataclasses import dataclass, field
from typing import Any, Dict, Optional


@dataclass
class ProviderConfig:
    """Configuration for a single provider."""
    provider_id: str
    provider_type: str  # "ollama", "openai", "anthropic", etc.
    model: str
    base_url: Optional[str] = None
    api_key: Optional[str] = None
    temperature: float = 0.0
    max_tokens: Optional[int] = None
    extra_params: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_env(cls, prefix: str) -> Optional["ProviderConfig"]:
        """Create config from environment variables with given prefix."""
        provider_id = os.getenv(f"{prefix}_PROVIDER_ID")
        if not provider_id:
            return None

        return cls(
            provider_id=provider_id,
            provider_type=os.getenv(f"{prefix}_TYPE", "ollama"),
            model=os.getenv(f"{prefix}_MODEL", "qwen2.5:7b-instruct"),
            base_url=os.getenv(f"{prefix}_BASE_URL"),
            api_key=os.getenv(f"{prefix}_API_KEY"),
            temperature=float(os.getenv(f"{prefix}_TEMPERATURE", "0.0")),
            max_tokens=int(os.getenv(f"{prefix}_MAX_TOKENS", "0")) or None,
        )


def load_provider_configs() -> Dict[str, ProviderConfig]:
    """Load all provider configs from environment."""
    configs = {}

    # Standard roles
    roles = ["AUDITOR", "ARCHITECT", "REVIEWER", "JUDGE", "ORCHESTRATOR"]

    for role in roles:
        config = ProviderConfig.from_env(f"LLM_{role}")
        if config:
            configs[role.lower()] = config

    # Also check for generic numbered providers
    i = 1
    while True:
        config = ProviderConfig.from_env(f"LLM_PROVIDER_{i}")
        if not config:
            break
        configs[f"provider_{i}"] = config
        i += 1

    return configs


def get_default_role_config(role: str) -> Optional[ProviderConfig]:
    """Get default config for a role from env."""
    return ProviderConfig.from_env(f"LLM_{role.upper()}")


# Default role mappings (can be overridden by env)
DEFAULT_ROLE_CONFIGS = {
    "auditor": {
        "provider": "env:LLM_AUDITOR_PROVIDER",
        "model": "env:LLM_AUDITOR_MODEL",
    },
    "architect": {
        "provider": "env:LLM_ARCHITECT_PROVIDER",
        "model": "env:LLM_ARCHITECT_MODEL",
    },
    "reviewer": {
        "provider": "env:LLM_REVIEWER_PROVIDER",
        "model": "env:LLM_REVIEWER_MODEL",
    },
    "judge": {
        "provider": "env:LLM_JUDGE_PROVIDER",
        "model": "env:LLM_JUDGE_MODEL",
    },
    "orchestrator": {
        "provider": "env:LLM_ORCHESTRATOR_PROVIDER",
        "model": "env:LLM_ORCHESTRATOR_MODEL",
    },
}
