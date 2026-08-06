"""Browser Intelligence - data model for structured research findings."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Source:
    url: str = ""
    title: str = ""
    snippet: str = ""

    def to_dict(self):
        return {"url": self.url, "title": self.title, "snippet": self.snippet}


@dataclass
class ResearchFindings:
    question: str = ""
    facts: list = field(default_factory=list)
    analysis: str = ""
    options: list = field(default_factory=list)
    recommendation: str = ""
    confidence: str = "Low"
    provider: str = "browser_use"
    sources: list = field(default_factory=list)
    elapsed_ms: int = 0
    warnings: list = field(default_factory=list)

    @property
    def empty(self):
        return not self.facts

    def to_dict(self):
        return {
            "FACTS": self.facts,
            "ANALYSIS": self.analysis,
            "OPTIONS": self.options,
            "RECOMMENDATION": self.recommendation,
            "CONFIDENCE": self.confidence,
            "PROVIDER": self.provider,
            "SOURCES": [s.to_dict() for s in self.sources],
        }

    def to_markdown(self):
        out = ["FACTS:"]
        if self.facts:
            for f in self.facts:
                out.append("- " + f)
        else:
            out.append("- No verified facts collected")
        out.append("")
        out.append("ANALYSIS:")
        out.append(self.analysis if self.analysis else "- No analysis available")
        out.append("")
        out.append("OPTIONS:")
        if self.options:
            for o in self.options:
                out.append("- " + o)
        else:
            out.append("- None recorded")
        out.append("")
        out.append("RECOMMENDATION:")
        out.append(self.recommendation if self.recommendation else "- No recommendation yet")
        out.append("")
        out.append("CONFIDENCE: " + self.confidence)
        if self.sources:
            out.append("")
            out.append("SOURCES:")
            for s in self.sources:
                out.append("- " + (s.title or s.url) + " : " + s.url)
        return "\n".join(out)
