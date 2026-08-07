"""Research Memory - persistent, cacheable store for research results.

Stores and reuses research findings in a feature-owned SQLite database, with a
deterministic hash cache (v1, no embeddings). Independent from Browser
Intelligence: fresh computation happens only through an injected
``ResearchPipeline`` (see ``pipeline.py``).

Usage:
    from features.research_memory import ResearchMemoryService
    service = ResearchMemoryService()
    service.save_research("what is browser-use?", payload={...})
"""

from .cache import ResearchMemoryCache
from .config import ResearchMemoryConfig, get_config
from .metrics import MREILMetrics
from .models import (
    Confidence,
    ResearchRecord,
    RecordStatus,
    Source,
    research_hash,
)
from .pipeline import FunctionResearchPipeline, ResearchPipeline
from .repository import ResearchMemoryRepository
from .service import ResearchMemoryService

__all__ = [
    "ResearchMemoryCache",
    "ResearchMemoryConfig",
    "ResearchMemoryRepository",
    "ResearchMemoryService",
    "Confidence",
    "RecordStatus",
    "ResearchRecord",
    "Source",
    "ResearchPipeline",
    "FunctionResearchPipeline",
    "MREILMetrics",
    "get_config",
    "research_hash",
]
__version__ = "0.1.0"