from __future__ import annotations

from features.optimization.optimizer import WorkflowOptimizer
from features.optimization.models import MREILResult, WorkflowRecommendation


class TestWorkflowOptimizer:

    def test_optimize_insufficient_data(self):
        opt = WorkflowOptimizer()
        result = opt.optimize_workflow([])
        assert result.confidence == 0.0
        assert result.current_pattern == "insufficient_data"

    def test_optimize_single_record(self):
        opt = WorkflowOptimizer()
        result = opt.optimize_workflow([{"quality_score": 0.8, "resource_efficiency": 0.7}])
        assert result.confidence == 0.0

    def test_optimize_low_quality(self):
        opt = WorkflowOptimizer()
        history = [
            {"quality_score": 0.3, "resource_efficiency": 0.7, "task_fit_score": 0.4, "overall_score": 0.4},
            {"quality_score": 0.2, "resource_efficiency": 0.8, "task_fit_score": 0.3, "overall_score": 0.3},
            {"quality_score": 0.25, "resource_efficiency": 0.6, "task_fit_score": 0.35, "overall_score": 0.35},
        ]
        result = opt.optimize_workflow(history)
        assert "quality" in result.current_pattern.lower() or "review" in result.recommended_pattern.lower()

    def test_optimize_low_efficiency(self):
        opt = WorkflowOptimizer()
        history = [
            {"quality_score": 0.9, "resource_efficiency": 0.2, "task_fit_score": 0.8, "overall_score": 0.7},
            {"quality_score": 0.85, "resource_efficiency": 0.15, "task_fit_score": 0.85, "overall_score": 0.65},
        ]
        result = opt.optimize_workflow(history)
        assert "cost" in result.recommended_pattern.lower() or "efficien" in result.recommended_pattern.lower()

    def test_optimize_good_performance(self):
        opt = WorkflowOptimizer()
        history = [
            {"quality_score": 0.9, "resource_efficiency": 0.8, "task_fit_score": 0.85, "overall_score": 0.85},
            {"quality_score": 0.85, "resource_efficiency": 0.75, "task_fit_score": 0.8, "overall_score": 0.8},
            {"quality_score": 0.95, "resource_efficiency": 0.85, "task_fit_score": 0.9, "overall_score": 0.9},
        ]
        result = opt.optimize_workflow(history)
        assert "continue" in result.recommended_pattern.lower()

    def test_record_evaluation(self):
        opt = WorkflowOptimizer()
        result = MREILResult(
            execution_id="e1", overall_score=0.8,
            task_fit_score=0.8, resource_efficiency=0.7, quality_score=0.9,
        )
        opt.record_evaluation(result)
        assert len(opt._history) == 1

    def test_optimize_from_recorded_history(self):
        opt = WorkflowOptimizer()
        for i in range(3):
            opt.record_evaluation(MREILResult(
                execution_id=f"e{i}", overall_score=0.3,
                task_fit_score=0.3, resource_efficiency=0.7, quality_score=0.25,
            ))
        result = opt.optimize_workflow()
        assert result.confidence > 0.0
