from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class ExecutionMetrics:
    execution_id: str
    task_id: str
    agent_id: str
    model_id: str
    duration: float
    tokens: int
    cpu_time: float
    memory_usage: int
    latency: float
    success: bool
    verification_score: float

    def to_dict(self) -> dict:
        return {
            "execution_metrics": {
                "execution_id": self.execution_id,
                "task_id": self.task_id,
                "agent_id": self.agent_id,
                "model_id": self.model_id,
                "duration": self.duration,
                "tokens": self.tokens,
                "cpu_time": self.cpu_time,
                "memory_usage": self.memory_usage,
                "latency": self.latency,
                "success": self.success,
                "verification_score": self.verification_score,
            }
        }


@dataclass
class QualityMetrics:
    correctness: float
    completeness: float
    verification_confidence: float
    knowledge_value: float
    human_feedback: float = 0.0

    def to_dict(self) -> dict:
        return {
            "quality_metrics": {
                "correctness": self.correctness,
                "completeness": self.completeness,
                "verification_confidence": self.verification_confidence,
                "knowledge_value": self.knowledge_value,
                "human_feedback": self.human_feedback,
            }
        }


@dataclass
class EfficiencyMetrics:
    quality_per_token: float
    quality_per_cpu: float
    quality_per_second: float
    task_fit_score: float
    consensus_efficiency_score: float

    def to_dict(self) -> dict:
        return {
            "efficiency_metrics": {
                "quality_per_token": self.quality_per_token,
                "quality_per_cpu": self.quality_per_cpu,
                "quality_per_second": self.quality_per_second,
                "task_fit_score": self.task_fit_score,
                "consensus_efficiency_score": self.consensus_efficiency_score,
            }
        }


@dataclass
class MREILResult:
    execution_id: str
    overall_score: float
    task_fit_score: float
    resource_efficiency: float
    quality_score: float
    recommendations: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "mreil_result": {
                "execution_id": self.execution_id,
                "overall_score": self.overall_score,
                "task_fit_score": self.task_fit_score,
                "resource_efficiency": self.resource_efficiency,
                "quality_score": self.quality_score,
                "recommendations": self.recommendations,
            }
        }


@dataclass
class AgentProfile:
    agent_id: str
    task_categories: dict[str, int] = field(default_factory=dict)
    total_executions: int = 0
    successful_executions: int = 0
    average_quality: float = 0.0
    average_latency: float = 0.0
    average_cost: float = 0.0
    strengths: list[str] = field(default_factory=list)
    weaknesses: list[str] = field(default_factory=list)

    @property
    def success_rate(self) -> float:
        if self.total_executions == 0:
            return 0.0
        return self.successful_executions / self.total_executions

    def to_dict(self) -> dict:
        return {
            "agent_profile": {
                "agent_id": self.agent_id,
                "task_categories": self.task_categories,
                "total_executions": self.total_executions,
                "successful_executions": self.successful_executions,
                "success_rate": round(self.success_rate, 2),
                "average_quality": round(self.average_quality, 2),
                "average_latency": round(self.average_latency, 2),
                "average_cost": round(self.average_cost, 2),
                "strengths": self.strengths,
                "weaknesses": self.weaknesses,
            }
        }


@dataclass
class WorkflowRecommendation:
    current_pattern: str
    recommended_pattern: str
    expected_improvement: str
    confidence: float
    reasoning: str = ""

    def to_dict(self) -> dict:
        return {
            "workflow_recommendation": {
                "current_pattern": self.current_pattern,
                "recommended_pattern": self.recommended_pattern,
                "expected_improvement": self.expected_improvement,
                "confidence": self.confidence,
                "reasoning": self.reasoning,
            }
        }
