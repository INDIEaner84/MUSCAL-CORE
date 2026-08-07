"""Research Pipeline - configuration.

Environment-driven, no Core imports, fires no side effects at import time.
"""

from __future__ import annotations

import os

try:
    from dotenv import load_dotenv

    load_dotenv()
except Exception:  # pragma: no cover - dotenv optional
    pass


class ResearchPipelineConfig:

    def __init__(self) -> None:
        self.default_provider = os.environ.get(
            "RESEARCH_PIPELINE_PROVIDER", "browser_intelligence"
        )
        self.default_depth = os.environ.get("RESEARCH_PIPELINE_DEPTH", "standard")

    def to_dict(self) -> dict:
        return {k: v for k, v in self.__dict__.items()}


_CONFIG: ResearchPipelineConfig | None = None


def get_config() -> ResearchPipelineConfig:
    global _CONFIG
    if _CONFIG is None:
        _CONFIG = ResearchPipelineConfig()
    return _CONFIG