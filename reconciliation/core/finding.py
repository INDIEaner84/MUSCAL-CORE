from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class Category(Enum):
    A = "A"
    B = "B"
    C = "C"
    D = "D"


class Severity(Enum):
    CRITICAL = "Critical"
    HIGH = "High"
    MEDIUM = "Medium"
    LOW = "Low"


class FindingStatus(Enum):
    OPEN = "OPEN"
    FIXED = "FIXED"
    WONT_FIX = "WONT_FIX"
    DEFERRED = "DEFERRED"


@dataclass
class Finding:
    finding_id: str
    scanner: str
    file: str
    severity: Severity
    category: Category
    status: FindingStatus = FindingStatus.OPEN
    line: int | None = None
    description: str = ""
    current_value: str = ""
    expected_value: str = ""
    suggested_fix: str = ""
    validation: str = ""
    extra: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        d: dict[str, Any] = {
            "finding_id": self.finding_id,
            "scanner": self.scanner,
            "file": self.file,
            "severity": self.severity.value,
            "category": self.category.value,
            "status": self.status.value,
        }
        if self.line is not None:
            d["line"] = self.line
        if self.description:
            d["description"] = self.description
        if self.current_value:
            d["current_value"] = self.current_value
        if self.expected_value:
            d["expected_value"] = self.expected_value
        if self.suggested_fix:
            d["suggested_fix"] = self.suggested_fix
        if self.extra:
            d.update(self.extra)
        return d


@dataclass
class FindingSet:
    scanner: str
    findings: list[Finding] = field(default_factory=list)

    @property
    def by_category(self) -> dict[Category, list[Finding]]:
        result: dict[Category, list[Finding]] = {}
        for f in self.findings:
            result.setdefault(f.category, []).append(f)
        return result

    @property
    def by_severity(self) -> dict[Severity, list[Finding]]:
        result: dict[Severity, list[Finding]] = {}
        for f in self.findings:
            result.setdefault(f.severity, []).append(f)
        return result

    @property
    def count(self) -> int:
        return len(self.findings)
