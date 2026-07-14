from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from reconciliation.core.finding import Category, Severity


@dataclass
class Rule:
    rule_id: str
    description: str
    severity: Severity
    category: Category
    auto_fixable: bool = False
    checker_type: str = ""
    params: dict[str, Any] = field(default_factory=dict)


@dataclass
class RuleSet:
    name: str
    rules: list[Rule]
    source: str = ""
