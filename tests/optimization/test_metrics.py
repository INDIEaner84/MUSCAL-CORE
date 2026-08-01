from __future__ import annotations

from features.optimization.metrics import MetricsCollector
from features.optimization.models import ExecutionMetrics, QualityMetrics


class TestMetricsCollector:

    def _make_bridge_output(self, status="completed", task_id="t1", duration=10.0, tokens=500):
        class MockBridgeOutput:
            def __init__(self):
                self.status = status
                self.task_id = task_id
                self.agent_id = "a1"
                self.model_id = "m1"
                self.execution_record = {"bridge_execution_id": "e1", "task_identity": {"id": task_id}}
                self.normalized = type("MockNormalized", (), {
                    "to_dict": lambda self: {"result": {"meta": {"duration": duration, "tokens": tokens, "latency": duration}}}
                })()

            def to_dict(self):
                return {
                    "execution_record": self.execution_record,
                    "normalized": self.normalized.to_dict(),
                }
        return MockBridgeOutput()

    def _make_verification(self, status="passed"):
        class MockVerification:
            def to_dict(self):
                return {"verification_report": {"status": status, "facts": [{"status": "passed"}], "verification_findings": []}}
        return MockVerification()

    def test_collect_success(self):
        collector = MetricsCollector()
        output = self._make_bridge_output()
        metrics = collector.collect(output, self._make_verification("passed"))
        assert isinstance(metrics, ExecutionMetrics)
        assert metrics.success is True
        assert metrics.verification_score == 1.0

    def test_collect_failed(self):
        collector = MetricsCollector()
        output = self._make_bridge_output(status="failed")
        metrics = collector.collect(output)
        assert metrics.success is False

    def test_collect_no_verification(self):
        collector = MetricsCollector()
        output = self._make_bridge_output()
        metrics = collector.collect(output)
        assert metrics.verification_score == 0.0

    def test_collect_quality_verified(self):
        collector = MetricsCollector()
        quality = collector.collect_quality(self._make_verification("passed"), knowledge_value=0.8)
        assert isinstance(quality, QualityMetrics)
        assert quality.correctness == 1.0
        assert quality.knowledge_value == 0.8

    def test_collect_quality_no_verification(self):
        collector = MetricsCollector()
        quality = collector.collect_quality(None)
        assert quality.verification_confidence == 0.0

    def test_verification_score_passed(self):
        collector = MetricsCollector()
        score = collector._compute_verification_score(self._make_verification("passed"))
        assert score == 1.0

    def test_verification_score_failed(self):
        collector = MetricsCollector()
        score = collector._compute_verification_score(self._make_verification("failed"))
        assert score == 0.0

    def test_verification_score_none(self):
        collector = MetricsCollector()
        score = collector._compute_verification_score(None)
        assert score == 0.0
