from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional


@dataclass
class Intent:
    task_id: str
    type: str
    goal: str
    constraints: list[str]
    priority: str
    risk: str
    required_capabilities: list[str]
    expected_outcome: str
    confidence: float
    reasoning: str = ""

    def to_dict(self) -> dict:
        return {
            "intent": {
                "task_id": self.task_id,
                "type": self.type,
                "goal": self.goal,
                "constraints": self.constraints,
                "priority": self.priority,
                "risk": self.risk,
                "required_capabilities": self.required_capabilities,
                "expected_outcome": self.expected_outcome,
                "confidence": self.confidence,
                "reasoning": self.reasoning,
            }
        }


class GoalPriority(str, Enum):
    PRIMARY = "PRIMARY"
    SECONDARY = "SECONDARY"
    SAFETY = "SAFETY"
    VERIFICATION = "VERIFICATION"
    KNOWLEDGE = "KNOWLEDGE"
    OPTIMIZATION = "OPTIMIZATION"


@dataclass
class Goal:
    id: str
    description: str
    priority: GoalPriority
    dependencies: list[str] = field(default_factory=list)
    status: str = "pending"

    def to_dict(self) -> dict:
        return {
            "goal": {
                "id": self.id,
                "description": self.description,
                "priority": self.priority.value,
                "dependencies": self.dependencies,
                "status": self.status,
            }
        }


@dataclass
class GoalSet:
    goals: list[Goal] = field(default_factory=list)

    def by_priority(self, priority: GoalPriority) -> list[Goal]:
        return [g for g in self.goals if g.priority == priority]

    def to_dict(self) -> dict:
        return {
            "goal_set": {
                "goals": [g.to_dict() for g in self.goals],
            }
        }


@dataclass
class UnifiedContext:
    runtime_state: dict = field(default_factory=dict)
    knowledge: list[dict] = field(default_factory=list)
    session: Optional[dict] = None
    agent_profiles: list[dict] = field(default_factory=list)
    task_analysis: Optional[dict] = None
    event_history: list[dict] = field(default_factory=list)
    memory_context: Optional[dict] = None
    execution_id: str = ""

    def to_dict(self) -> dict:
        return {
            "unified_context": {
                "runtime_state": self.runtime_state,
                "knowledge": self.knowledge,
                "session": self.session,
                "agent_profiles": self.agent_profiles,
                "task_analysis": self.task_analysis,
                "event_history_count": len(self.event_history),
                "memory_context": self.memory_context,
                "execution_id": self.execution_id,
            }
        }


class StrategyType(str, Enum):
    ARCHITECTURE = "architecture"
    IMPLEMENTATION = "implementation"
    INVESTIGATION = "investigation"
    REPAIR = "repair"
    VALIDATION = "validation"
    DOCUMENTATION = "documentation"


@dataclass
class Strategy:
    type: StrategyType
    description: str
    reasoning: str
    recommended_autonomy: str

    def to_dict(self) -> dict:
        return {
            "strategy": {
                "type": self.type.value,
                "description": self.description,
                "reasoning": self.reasoning,
                "recommended_autonomy": self.recommended_autonomy,
            }
        }
