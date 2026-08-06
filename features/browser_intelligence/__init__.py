"""Browser Intelligence - MUSCAL extension.

LLM-driven web research via Browser-Use, using the local Ollama instance by
default. Exposes a ResearchService abstraction that can later back MCP tools
or other research providers.

Usage:
    from features.browser_intelligence import ResearchService
    findings = ResearchService().research("What is browser-use?")
    print(findings.to_markdown())
"""

from .models import ResearchFindings, Source
from .research_service import ResearchService

__all__ = ["ResearchService", "ResearchFindings", "Source"]
__version__ = "0.1.0"
