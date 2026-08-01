from __future__ import annotations

from typing import Any, Optional

from .models import ExecutionMetrics, MREILResult, WorkflowRecommendation


class WorkflowOptimizer:

    def __init__(self):
        self._history: list[dict] = []

    def record_evaluation(self, result: MREILResult) -> None:
        self._history.append({
            "execution_id": result.execution_id,
            "overall_score": result.overall_score,
            "quality_score": result.quality_score,
            "resource_efficiency": result.resource_efficiency,
            "task_fit_score": result.task_fit_score,
        })

    def optimize_workflow(self, history: Optional[list[dict]] = None) -> WorkflowRecommendation:
        records = history or self._history
        if len(records) < 2:
            return WorkflowRecommendation(
                current_pattern="insufficient_data",
                recommended_pattern="collect_more_executions",
                expected_improvement="unknown",
                confidence=0.0,
                reasoning="Need at least 2 execution records to detect patterns",
            )

        recent = records[-5:]
        avg_quality = sum(r.get("quality_score", 0) for r in recent) / len(recent)
        avg_efficiency = sum(r.get("resource_efficiency", 0) for r in recent) / len(recent)

        if avg_quality < 0.5:
            confidence = 1.0 - avg_quality
            return WorkflowRecommendation(
                current_pattern="low_quality_auto_select",
                recommended_pattern="human_review_required",
                expected_improvement=f"+{round((1.0 - avg_quality) * 50, 1)}% quality",
                confidence=round(confidence, 2),
                reasoning=f"Average quality {round(avg_quality, 2)} below threshold",
            )

        if avg_efficiency < 0.3:
            confidence = 1.0 - avg_efficiency
            return WorkflowRecommendation(
                current_pattern="high_cost_routing",
                recommended_pattern="cost_aware_routing",
                expected_improvement=f"+{round((1.0 - avg_efficiency) * 40, 1)}% efficiency",
                confidence=round(confidence, 2),
                reasoning=f"Average efficiency {round(avg_efficiency, 2)} indicates resource waste",
            )

        return WorkflowRecommendation(
            current_pattern="current_execution_pattern",
            recommended_pattern="continue_current_pattern",
            expected_improvement="marginal",
            confidence=round(avg_quality, 2),
            reasoning=f"System performing adequately (quality={round(avg_quality, 2)}, efficiency={round(avg_efficiency, 2)})",
        )
