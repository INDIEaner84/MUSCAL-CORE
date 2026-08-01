from __future__ import annotations

from enum import Enum
from typing import Any, Optional

from ..bridge.task_contract import TaskContract
from .models import TaskAnalysis


class ComplexityLevel(str, Enum):
    SIMPLE = "SIMPLE"
    MODERATE = "MODERATE"
    COMPLEX = "COMPLEX"


class RiskLevel(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class TaskCategory(str, Enum):
    BUG_FIX = "bug_fix"
    FEATURE = "feature"
    REFACTOR = "refactor"
    DOCUMENTATION = "documentation"
    TESTING = "testing"
    DEPLOYMENT = "deployment"
    ANALYSIS = "analysis"
    OTHER = "other"

    @classmethod
    def classify(cls, objective: str) -> TaskCategory:
        lower = objective.lower()
        if any(w in lower for w in ("deploy", "release", "publish")):
            return cls.DEPLOYMENT
        if any(w in lower for w in ("refactor", "restructure", "clean")):
            return cls.REFACTOR
        if any(w in lower for w in ("bug", "fix", "error", "crash", "issue")):
            return cls.BUG_FIX
        if any(w in lower for w in ("test", "coverage", "assert")):
            return cls.TESTING
        if any(w in lower for w in ("feature", "add", "implement", "new")):
            return cls.FEATURE
        if any(w in lower for w in ("analyze", "audit", "review", "inspect")):
            return cls.ANALYSIS
        if any(w in lower for w in ("doc", "readme", "comment", "document")):
            return cls.DOCUMENTATION
        return cls.OTHER


class TaskAnalyzer:

    def analyze(self, task: TaskContract) -> TaskAnalysis:
        category = TaskCategory.classify(task.objective)
        complexity = self._estimate_complexity(task)
        risk = self._estimate_risk(task, category)
        capabilities = self._required_capabilities(category, complexity)
        effort = self._estimate_effort(complexity)
        recommended = self._recommend_autonomy(risk, complexity)
        reasoning = self._build_reasoning(task, category, complexity, risk)

        return TaskAnalysis(
            task_id=task.id,
            category=category.value,
            complexity=complexity.value,
            risk_level=risk.value,
            required_capabilities=capabilities,
            estimated_effort=effort,
            verification_required=task.verification_required,
            recommended_autonomy=recommended,
            reasoning=reasoning,
        )

    def _estimate_complexity(self, task: TaskContract) -> ComplexityLevel:
        word_count = len(task.objective.split())
        constraint_count = len(task.constraints)
        has_expected = bool(task.expected_output)
        if word_count < 10 and constraint_count == 0 and not has_expected:
            return ComplexityLevel.SIMPLE
        if word_count > 50 or constraint_count > 3:
            return ComplexityLevel.COMPLEX
        return ComplexityLevel.MODERATE

    def _estimate_risk(self, task: TaskContract, category: TaskCategory) -> RiskLevel:
        high_risk_cats = {TaskCategory.DEPLOYMENT}
        medium_risk_cats = {TaskCategory.FEATURE, TaskCategory.REFACTOR, TaskCategory.BUG_FIX}
        if category in high_risk_cats:
            return RiskLevel.HIGH
        if category in medium_risk_cats:
            return RiskLevel.MEDIUM
        if any("prod" in c.lower() or "production" in c.lower() for c in task.constraints):
            return RiskLevel.HIGH
        return RiskLevel.LOW

    def _required_capabilities(self, category: TaskCategory, complexity: ComplexityLevel) -> list[str]:
        base: list[str] = ["code_understanding"]
        cat_map = {
            TaskCategory.BUG_FIX: ["debugging", "testing"],
            TaskCategory.FEATURE: ["code_generation", "architecture"],
            TaskCategory.REFACTOR: ["code_analysis", "architecture"],
            TaskCategory.DOCUMENTATION: ["documentation", "communication"],
            TaskCategory.TESTING: ["testing", "code_analysis"],
            TaskCategory.DEPLOYMENT: ["devops", "testing"],
            TaskCategory.ANALYSIS: ["code_analysis", "communication"],
        }
        base.extend(cat_map.get(category, []))
        if complexity in (ComplexityLevel.MODERATE, ComplexityLevel.COMPLEX):
            base.append("architecture")
        return base

    def _estimate_effort(self, complexity: ComplexityLevel) -> str:
        return {
            ComplexityLevel.SIMPLE: "small",
            ComplexityLevel.MODERATE: "medium",
            ComplexityLevel.COMPLEX: "large",
        }[complexity]

    def _recommend_autonomy(self, risk: RiskLevel, complexity: ComplexityLevel) -> str:
        if risk == RiskLevel.HIGH:
            return "A2"
        if complexity == ComplexityLevel.COMPLEX:
            return "A3"
        if complexity == ComplexityLevel.SIMPLE:
            return "A4"
        return "A3"

    def _build_reasoning(self, task: TaskContract, category: TaskCategory,
                         complexity: ComplexityLevel, risk: RiskLevel) -> str:
        return (
            f"Task '{task.objective[:60]}' classified as {category.value} "
            f"with {complexity.value} complexity and {risk.value} risk. "
            f"{len(task.constraints)} constraint(s) applied."
        )
