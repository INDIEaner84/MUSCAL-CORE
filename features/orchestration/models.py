from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class TaskAnalysis:
    task_id: str
    category: str
    complexity: str
    risk_level: str
    required_capabilities: list[str]
    estimated_effort: str
    verification_required: bool
    recommended_autonomy: str
    reasoning: str = ""

    def to_dict(self) -> dict:
        return {
            "task_analysis": {
                "task_id": self.task_id,
                "category": self.category,
                "complexity": self.complexity,
                "risk_level": self.risk_level,
                "required_capabilities": self.required_capabilities,
                "estimated_effort": self.estimated_effort,
                "verification_required": self.verification_required,
                "recommended_autonomy": self.recommended_autonomy,
                "reasoning": self.reasoning,
            }
        }


@dataclass
class AgentCapability:
    name: str
    description: str
    strength: float

    def to_dict(self) -> dict:
        return {
            "agent_capability": {
                "name": self.name,
                "description": self.description,
                "strength": self.strength,
            }
        }


@dataclass
class AgentDefinition:
    agent_id: str
    capabilities: list[AgentCapability]
    models: list[str]
    cost_profile: str
    speed_profile: str
    quality_profile: str
    allowed_actions: list[str]
    autonomy_level: str

    def to_dict(self) -> dict:
        return {
            "agent_definition": {
                "agent_id": self.agent_id,
                "capabilities": [c.to_dict() for c in self.capabilities],
                "models": self.models,
                "cost_profile": self.cost_profile,
                "speed_profile": self.speed_profile,
                "quality_profile": self.quality_profile,
                "allowed_actions": self.allowed_actions,
                "autonomy_level": self.autonomy_level,
            }
        }


@dataclass
class SelectionResult:
    selected_agent: Optional[AgentDefinition]
    alternatives: list[AgentDefinition]
    reason: str
    confidence: float
    estimated_cost: str = "unknown"

    def to_dict(self) -> dict:
        return {
            "agent_selection": {
                "selected_agent": self.selected_agent.to_dict() if self.selected_agent else None,
                "alternatives": [a.to_dict() for a in self.alternatives],
                "reason": self.reason,
                "confidence": self.confidence,
                "estimated_cost": self.estimated_cost,
            }
        }


@dataclass
class EfficiencyEstimate:
    quality_estimate: float
    cost_estimate: float
    latency_estimate: float
    task_fit_score: float
    confidence: float

    def to_dict(self) -> dict:
        return {
            "efficiency": {
                "quality_estimate": self.quality_estimate,
                "cost_estimate": self.cost_estimate,
                "latency_estimate": self.latency_estimate,
                "task_fit_score": self.task_fit_score,
                "confidence": self.confidence,
            }
        }


@dataclass
class PlanStep:
    step_id: str
    action: str
    description: str
    agent: Optional[str] = None
    risk_controls: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "plan_step": {
                "step_id": self.step_id,
                "action": self.action,
                "description": self.description,
                "agent": self.agent,
                "risk_controls": self.risk_controls,
            }
        }


@dataclass
class ExecutionPlan:
    task_id: str
    steps: list[PlanStep]
    required_agents: list[str]
    risk_controls: list[str]
    autonomy_level: str
    estimated_effort: str = "unknown"

    def to_dict(self) -> dict:
        return {
            "execution_plan": {
                "task_id": self.task_id,
                "steps": [s.to_dict() for s in self.steps],
                "required_agents": self.required_agents,
                "risk_controls": self.risk_controls,
                "autonomy_level": self.autonomy_level,
                "estimated_effort": self.estimated_effort,
            }
        }


ORCHESTRATION_EVENTS = frozenset({
    "orchestration.task.analyzed",
    "orchestration.agent.selected",
    "orchestration.plan.created",
    "orchestration.execution.requested",
})
