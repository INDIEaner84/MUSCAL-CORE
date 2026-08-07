"""Research Pipeline - data model.

`ResearchRequest` is the public input contract; `ResearchResult` the unified
output contract of the pipeline layer, independent of any concrete provider
(normalized by adapters). Import-safe: stdlib only.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone

ALLOWED_DEPTHS = ("quick", "standard", "deep")

_DEPTH_CONSTRAINTS = {
    "quick": ["answer concisely", "prefer the first reliable source"],
    "standard": [],
    "deep": ["research multiple sources", "cross-check claims", "cover alternatives"],
}


def resolve_constraints(depth: str) -> list:
    return list(_DEPTH_CONSTRAINTS.get((depth or "").strip().lower(), []))


def validate_depth(depth: str) -> str:
    value = (depth or "").strip().lower() or "standard"
    if value not in ALLOWED_DEPTHS:
        raise ValueError(f"depth must be one of {list(ALLOWED_DEPTHS)}; got {depth!r}")
    return value


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


@dataclass
class ResearchRequest:
    question: str
    context: str = ""
    depth: str = "standard"
    force_refresh: bool = False
    metadata: dict = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.question or not self.question.strip():
            raise ValueError("question is required and must be a non-empty string")
        self.depth = validate_depth(self.depth)


@dataclass
class ResearchResult:
    source: str = "unknown"
    facts: list = field(default_factory=list)
    analysis: str = ""
    options: list = field(default_factory=list)
    recommendation: str = ""
    confidence: str = "low"
    sources: list = field(default_factory=list)
    warnings: list = field(default_factory=list)
    timestamp: str = field(default_factory=now_iso)

    def to_dict(self) -> dict:
        return {
            "source": self.source,
            "facts": list(self.facts),
            "analysis": self.analysis,
            "options": list(self.options),
            "recommendation": self.recommendation,
            "confidence": self.confidence,
            "sources": list(self.sources),
            "warnings": list(self.warnings),
            "timestamp": self.timestamp,
        }

    @classmethod
    def from_dict(cls, raw: dict) -> "ResearchResult":
        raw = raw or {}
        return cls(
            source=raw.get("source", "unknown"),
            facts=list(raw.get("facts", []) or []),
            analysis=raw.get("analysis", ""),
            options=list(raw.get("options", []) or []),
            recommendation=raw.get("recommendation", ""),
            confidence=raw.get("confidence", "low"),
            sources=list(raw.get("sources", []) or []),
            warnings=list(raw.get("warnings", []) or []),
            timestamp=raw.get("timestamp", now_iso()),
        )