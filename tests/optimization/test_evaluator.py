from __future__ import annotations

from features.optimization.evaluator import MREILEvaluator
from features.optimization.models import ExecutionMetrics, QualityMetrics, MREILResult


class TestMREILEvaluator:

    def _make_metrics(self, success=True, v_score=0.9, duration=10.0, tokens=500, cpu=2.0, memory=256, latency=9.5):
        return ExecutionMetrics(
            execution_id="e1", task_id="t1", agent_id="a1", model_id="m1",
            duration=duration, tokens=tokens, cpu_time=cpu,
            memory_usage=memory, latency=latency,
            success=success, verification_score=v_score,
        )

    def test_evaluate_successful(self):
        evaluator = MREILEvaluator()
        m = self._make_metrics()
        result = evaluator.evaluate(m)
        assert isinstance(result, MREILResult)
        assert result.execution_id == "e1"
        assert 0.0 <= result.overall_score <= 1.0

    def test_evaluate_failed(self):
        evaluator = MREILEvaluator()
        m = self._make_metrics(success=False, v_score=0.0)
        result = evaluator.evaluate(m)
        assert result.quality_score < 0.5
        assert len(result.recommendations) > 0

    def test_evaluate_with_quality(self):
        evaluator = MREILEvaluator()
        m = self._make_metrics()
        q = QualityMetrics(correctness=0.9, completeness=0.85, verification_confidence=0.95, knowledge_value=0.8)
        result = evaluator.evaluate(m, quality=q)
        assert result.quality_score > 0.5

    def test_evaluate_low_confidence(self):
        evaluator = MREILEvaluator()
        m = self._make_metrics(v_score=0.1, success=False)
        result = evaluator.evaluate(m)
        assert result.quality_score < 0.3

    def test_negative_recommendations_for_failure(self):
        evaluator = MREILEvaluator()
        m = self._make_metrics(success=False, v_score=0.0)
        result = evaluator.evaluate(m)
        rec_text = " ".join(result.recommendations).lower()
        assert "fail" in rec_text or "review" in rec_text

    def test_high_quality_no_recommendations(self):
        evaluator = MREILEvaluator()
        m = self._make_metrics(success=True, v_score=1.0, duration=1.0, tokens=50)
        result = evaluator.evaluate(m)
        assert len(result.recommendations) == 0

    def test_resource_efficiency_low(self):
        evaluator = MREILEvaluator()
        m = self._make_metrics(duration=1000.0, tokens=50000, cpu=500.0)
        result = evaluator.evaluate(m)
        assert result.resource_efficiency < 0.3

    def test_resource_efficiency_high(self):
        evaluator = MREILEvaluator()
        m = self._make_metrics(duration=0.5, tokens=10, cpu=0.1)
        result = evaluator.evaluate(m)
        assert result.resource_efficiency > 0.5

    def test_overall_score_bounds(self):
        evaluator = MREILEvaluator()
        m = self._make_metrics(success=True, v_score=1.0, duration=0.1, tokens=5)
        result = evaluator.evaluate(m)
        assert 0.0 <= result.overall_score <= 1.0
