"""Research Pipeline - MUSCAL extension.

Unified research orchestration between OpenCode/MCP, Research Memory and
research providers (Browser Intelligence today). The pipeline layer itself
imports no provider implementation: every provider enters through the
``ResearchProvider`` interface (adapters)."""

from .config import ResearchPipelineConfig, get_config
from .interfaces import ResearchProvider, ResearchProviderError
from .models import (
    ALLOWED_DEPTHS,
    ResearchRequest,
    ResearchResult,
    now_iso,
    resolve_constraints,
    validate_depth,
)
from .registry import ResearchProviderRegistry, get_default_registry
from .service import ResearchPipelineService

__all__ = [
    "ResearchPipelineConfig",
    "ResearchPipelineService",
    "ResearchProvider",
    "ResearchProviderError",
    "ResearchProviderRegistry",
    "ResearchRequest",
    "ResearchResult",
    "ALLOWED_DEPTHS",
    "now_iso",
    "resolve_constraints",
    "validate_depth",
    "get_config",
    "get_default_registry",
]
__version__ = "0.1.0"