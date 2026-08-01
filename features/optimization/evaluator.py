from __future__ import annotations

from typing import Any, Optional

from .models import ExecutionMetrics, QualityMetrics, EfficiencyMetrics, MREILResult


class MREILEvaluator:

    def evaluate(self, exec_metrics: ExecutionMetrics,
                 quality: Optional[QualityMetrics] = None) -> MREILResult:
        quality_score = self._compute_quality_score(exec_metrics, quality)
        resource_eff = self._compute_resource_efficiency(exec_metrics)
        task_fit = self._compute_task_fit(exec_metrics)
        overall = self._compute_overall(quality_score, resource_eff, task_fit)
        recommendations = self._generate_recommendations(exec_metrics, quality_score, resource_eff)

        return MREILResult(
            execution_id=exec_metrics.execution_id,
            overall_score=round(overall, 2),
            task_fit_score=round(task_fit, 2),
            resource_efficiency=round(resource_eff, 2),
            quality_score=round(quality_score, 2),
            recommendations=recommendations,
        )

    def _compute_quality_score(self, exec_metrics: ExecutionMetrics,
                                quality: Optional[QualityMetrics]) -> float:
        if quality is not None:
            base = (
                quality.correctness * 0.4 +
                quality.completeness * 0.3 +
                quality.verification_confidence * 0.3
            )
        else:
            base = exec_metrics.verification_score
        if exec_metrics.success:
            return max(0.0, base)
        return max(0.0, base * 0.3)

    def _compute_resource_efficiency(self, m: ExecutionMetrics) -> float:
        if m.duration <= 0 or m.tokens <= 0:
            return 0.5
        time_eff = 1.0 / (1.0 + m.duration)
        token_eff = 1.0 / (1.0 + m.tokens / 1000.0)
        cpu_eff = 1.0 / (1.0 + max(m.cpu_time, 0.01))
        return (time_eff * 0.3 + token_eff * 0.4 + cpu_eff * 0.3)

    def _compute_task_fit(self, m: ExecutionMetrics) -> float:
        score = m.verification_score
        if not m.success:
            score *= 0.3
        return max(0.0, min(1.0, score))

    def _compute_overall(self, quality: float, efficiency: float, fit: float) -> float:
        return quality * 0.4 + efficiency * 0.3 + fit * 0.3

    def _generate_recommendations(self, m: ExecutionMetrics,
                                   quality: float, efficiency: float) -> list[str]:
        recs: list[str] = []
        if not m.success:
            recs.append(f"Execution {m.execution_id} failed — review error and retry")
        if quality < 0.5:
            recs.append("Quality score below threshold — consider using a more capable agent")
        if efficiency < 0.3:
            recs.append("Resource efficiency is low — consider a faster/cheaper model")
        if m.verification_score < 0.5:
            recs.append("Verification score low — review verification findings")
        return recs
