from __future__ import annotations

from typing import Any, Optional

from ..bridge.task_contract import TaskContract
from .models import Intent


class IntentEngine:

    def create(self, task: TaskContract) -> Intent:
        lower = task.objective.lower()
        intent_type = self._classify_type(lower)
        priority = self._determine_priority(task)
        risk = self._determine_risk(task, intent_type)
        capabilities = self._determine_capabilities(intent_type, lower)
        confidence = self._compute_confidence(task)
        reasoning = f"Task '{task.objective[:60]}' classified as {intent_type} with {priority} priority"

        return Intent(
            task_id=task.id,
            type=intent_type,
            goal=task.objective,
            constraints=task.constraints,
            priority=priority,
            risk=risk,
            required_capabilities=capabilities,
            expected_outcome=task.expected_output or "completed successfully",
            confidence=confidence,
            reasoning=reasoning,
        )

    def _classify_type(self, lower: str) -> str:
        if any(w in lower for w in ("architect", "design", "structure")):
            return "architecture"
        if any(w in lower for w in ("implement", "add", "feature", "create")):
            return "implementation"
        if any(w in lower for w in ("investigate", "analyze", "audit", "root cause")):
            return "investigation"
        if any(w in lower for w in ("bug", "fix", "repair", "error", "crash")):
            return "repair"
        if any(w in lower for w in ("test", "verify", "validate", "coverage")):
            return "validation"
        if any(w in lower for w in ("doc", "readme", "document")):
            return "documentation"
        return "implementation"

    def _determine_priority(self, task: TaskContract) -> str:
        lower = task.objective.lower()
        if any(w in lower for w in ("critical", "urgent", "p0", "blocker", "production")):
            return "critical"
        if any(w in lower for w in ("high", "important", "p1")):
            return "high"
        if any(w in lower for w in ("medium", "p2")):
            return "medium"
        return "normal"

    def _determine_risk(self, task: TaskContract, intent_type: str) -> str:
        if intent_type == "architecture":
            return "high"
        if intent_type == "repair" and any("production" in c.lower() for c in task.constraints):
            return "critical"
        if task.constraints:
            return "medium"
        return "low"

    def _determine_capabilities(self, intent_type: str, lower: str) -> list[str]:
        base = ["code_understanding"]
        type_map = {
            "architecture": ["architecture", "code_analysis"],
            "implementation": ["code_generation", "architecture"],
            "investigation": ["code_analysis", "debugging"],
            "repair": ["debugging", "testing"],
            "validation": ["testing", "code_analysis"],
            "documentation": ["documentation", "communication"],
        }
        base.extend(type_map.get(intent_type, []))
        return base

    def _compute_confidence(self, task: TaskContract) -> float:
        score = 0.5
        if task.objective and len(task.objective) > 20:
            score += 0.2
        if task.expected_output:
            score += 0.15
        if task.constraints:
            score += 0.1
        return min(1.0, score)
