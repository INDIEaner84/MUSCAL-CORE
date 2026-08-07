"""Research Memory - data model.

A ``ResearchRecord`` is a self-contained, cacheable unit of research output:
the query that produced it plus the structured findings. Records are stored by
Research Memory in a feature-owned SQLite database; nothing here touches Core.

Import-safe: stdlib only.
"""

from __future__ import annotations

import enum
import hashlib
import re
import uuid as _uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone


class Confidence(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class RecordStatus(str, enum.Enum):
    NEW = "new"
    REVIEWED = "reviewed"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    OBSOLETE = "obsolete"
    ARCHIVED = "archived"


def _coerce_enum(enum_cls, value, default):
    if value is None:
        return default
    if isinstance(value, enum_cls):
        return value
    key = str(value).strip().lower()
    for member in enum_cls:
        if member.value == key or member.name.lower() == key:
            return member
    return default


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _normalize(text) -> str:
    return re.sub(r"\s+", " ", str(text or "")).strip().lower()


def research_hash(query, context="") -> str:
    """Deterministic cache key: hash(normalized query + normalized context).

    No embeddings, no vector search - v1 cache strategy.
    """
    canonical = f"{_normalize(query)}\x1f{_normalize(context)}"
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


@dataclass
class Source:
    url: str = ""
    title: str = ""
    snippet: str = ""

    def to_dict(self) -> dict:
        return {"url": self.url, "title": self.title, "snippet": self.snippet}

    @classmethod
    def from_dict(cls, raw: dict) -> "Source":
        raw = raw or {}
        return cls(
            url=raw.get("url", ""),
            title=raw.get("title", ""),
            snippet=raw.get("snippet", ""),
        )


@dataclass
class ResearchRecord:
    """A stored research result. ``hash`` is the deterministic cache key."""

    id: str = ""
    query: str = ""
    context: str = ""
    domain: str = ""
    created_at: str = ""
    updated_at: str = ""
    sources: list[Source] = field(default_factory=list)
    facts: list[str] = field(default_factory=list)
    options: list[str] = field(default_factory=list)
    analysis: str = ""
    recommendation: str = ""
    confidence: str = "low"
    status: str = "new"
    hash: str = ""
    ttl: int | None = None

    def __post_init__(self) -> None:
        ts = now_iso()
        if not self.id:
            self.id = _uuid.uuid4().hex
        if not self.created_at:
            self.created_at = ts
        if not self.updated_at:
            self.updated_at = ts
        if not self.hash:
            self.hash = research_hash(self.query, self.context)
        self.confidence = _coerce_enum(Confidence, self.confidence, Confidence.LOW).value
        self.status = _coerce_enum(
            RecordStatus, self.status, RecordStatus.NEW
        ).value
        self.sources = [
            s if isinstance(s, Source) else Source.from_dict(s or {})
            for s in (self.sources or [])
        ]

    @property
    def confidence_enum(self) -> Confidence:
        return _coerce_enum(Confidence, self.confidence, Confidence.LOW)

    @property
    def status_enum(self) -> RecordStatus:
        return _coerce_enum(RecordStatus, self.status, RecordStatus.NEW)

    @property
    def age_seconds(self) -> float:
        try:
            return (datetime.now(timezone.utc) - datetime.fromisoformat(self.updated_at)).total_seconds()
        except (ValueError, TypeError):
            return float("inf")

    def touch(self) -> None:
        self.updated_at = now_iso()
        if not self.created_at:
            self.created_at = self.updated_at

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "query": self.query,
            "context": self.context,
            "domain": self.domain,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "sources": [s.to_dict() for s in self.sources],
            "facts": list(self.facts),
            "options": list(self.options),
            "analysis": self.analysis,
            "recommendation": self.recommendation,
            "confidence": self.confidence,
            "status": self.status,
            "hash": self.hash,
            "ttl": self.ttl,
        }

    @classmethod
    def from_dict(cls, raw: dict) -> "ResearchRecord":
        raw = raw or {}
        return cls(
            id=raw.get("id", ""),
            query=raw.get("query", ""),
            context=raw.get("context", ""),
            domain=raw.get("domain", ""),
            created_at=raw.get("created_at", ""),
            updated_at=raw.get("updated_at", ""),
            sources=raw.get("sources", []) or [],
            facts=list(raw.get("facts", []) or []),
            options=list(raw.get("options", []) or []),
            analysis=raw.get("analysis", ""),
            recommendation=raw.get("recommendation", ""),
            confidence=raw.get("confidence", "low"),
            status=raw.get("status", "new"),
            hash=raw.get("hash", ""),
            ttl=raw.get("ttl"),
        )

    def to_markdown(self) -> str:
        out = [
            f"# {self.query}",
            "",
            f"Status: **{self.status}** | Confidence: **{self.confidence}**",
            f"Domain: {self.domain or '-'} | Updated: {self.updated_at}",
            "",
            "## FACTS",
        ]
        if self.facts:
            out.extend(f"- {f}" for f in self.facts)
        else:
            out.append("- (no facts)")
        out.append("")
        out.append("## ANALYSIS")
        out.append(self.analysis or "- (no analysis)")
        out.append("")
        out.append("## OPTIONS")
        if self.options:
            out.extend(f"- {o}" for o in self.options)
        else:
            out.append("- (no options)")
        out.append("")
        out.append("## RECOMMENDATION")
        out.append(self.recommendation or "- (no recommendation)")
        if self.sources:
            out.append("")
            out.append("## SOURCES")
            for s in self.sources:
                label = s.title or s.url
                out.append(f"- {label} : {s.url}")
        return "\n".join(out)