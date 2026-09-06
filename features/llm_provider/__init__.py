"""
LLM Provider Package - Provider-agnostic LLM abstraction.

Provides:
- LLMProvider protocol
- LLMProviderRegistry for role-based routing
- Env-based configuration
"""

from features.llm_provider.protocol import LLMProvider
from features.llm_provider.provider_config import (
    DEFAULT_ROLE_CONFIGS,
    ProviderConfig,
    get_default_role_config,
    load_provider_configs,
)
from features.llm_provider.registry import (
    LLMProviderRegistry,
    TaskFit,
    llm_provider_registry,
)

__version__ = "0.1.0"
__all__ = [
    "LLMProvider",
    "LLMProviderRegistry",
    "TaskFit",
    "llm_provider_registry",
    "ProviderConfig",
    "load_provider_configs",
    "get_default_role_config",
    "DEFAULT_ROLE_CONFIGS",
]
