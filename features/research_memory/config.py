"""Research Memory - configuration.

Environment-driven, no Core imports, no side effects at import time (reads
happen inside the constructor). The database lives in a feature-owned data
directory, so the Core database and EventStore stay untouched.
"""

from __future__ import annotations

import os
from pathlib import Path

try:
    from dotenv import load_dotenv

    load_dotenv()
except Exception:  # pragma: no cover - dotenv optional
    pass

_DEFAULT_DB = str(Path(__file__).resolve().parent / "data" / "research_memory.db")


class ResearchMemoryConfig:

    def __init__(self) -> None:
        self.db_path = os.environ.get("RESEARCH_MEMORY_DB_PATH", _DEFAULT_DB)
        self.default_ttl = os.environ.get("RESEARCH_MEMORY_DEFAULT_TTL", "604800")
        self.list_limit = int(os.environ.get("RESEARCH_MEMORY_MAX_RESULTS", "100"))
        self.metrics_enabled = os.environ.get("RESEARCH_MEMORY_METRICS", "1").lower() not in (
            "0",
            "false",
            "no",
        )

    @property
    def ttl_seconds(self) -> int | None:
        try:
            value = int(self.default_ttl)
            return value if value > 0 else None
        except (TypeError, ValueError):
            return None

    def to_dict(self) -> dict:
        return {k: v for k, v in self.__dict__.items()}


_CONFIG: ResearchMemoryConfig | None = None


def get_config() -> ResearchMemoryConfig:
    global _CONFIG
    if _CONFIG is None:
        _CONFIG = ResearchMemoryConfig()
    return _CONFIG