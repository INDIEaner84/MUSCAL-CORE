from __future__ import annotations

from features.optimization.models import (
    ExecutionMetrics, QualityMetrics, EfficiencyMetrics, MREILResult,
    WorkflowRecommendation, AgentProfile,
)


class TestOptimizationModels:

    def test_execution_metrics(self):
        m = ExecutionMetrics(
            execution_id="e1", task_id="t1", agent_id="a1", model_id="m1",
            duration=10.0, tokens=500, cpu_time=2.0, memory_usage=256,
            latency=9.5, success=True, verification_score=0.9,
        )
        assert m.execution_id == "e1"
        d = m.to_dict()
        assert d["execution_metrics"]["success"] is True

    def test_execution_metrics_failed(self):
        m = ExecutionMetrics(
            execution_id="e2", task_id="t1", agent_id="a1", model_id="m1",
            duration=5.0, tokens=100, cpu_time=0.5, memory_usage=128,
            latency=4.8, success=False, verification_score=0.0,
        )
        assert m.success is False

    def test_quality_metrics(self):
        q = QualityMetrics(correctness=0.9, completeness=0.8, verification_confidence=0.95, knowledge_value=0.7)
        d = q.to_dict()
        assert d["quality_metrics"]["correctness"] == 0.9

    def test_quality_metrics_default_human_feedback(self):
        q = QualityMetrics(correctness=0.5, completeness=0.5, verification_confidence=0.5, knowledge_value=0.0)
        assert q.human_feedback == 0.0

    def test_efficiency_metrics(self):
        e = EfficiencyMetrics(
            quality_per_token=0.002, quality_per_cpu=0.5,
            quality_per_second=0.1, task_fit_score=0.85,
            consensus_efficiency_score=0.7,
        )
        d = e.to_dict()
        assert d["efficiency_metrics"]["task_fit_score"] == 0.85

    def test_mreil_result(self):
        r = MREILResult(
            execution_id="e1", overall_score=0.75,
            task_fit_score=0.8, resource_efficiency=0.6,
            quality_score=0.85, recommendations=["test"],
        )
        d = r.to_dict()
        assert d["mreil_result"]["overall_score"] == 0.75
        assert "test" in d["mreil_result"]["recommendations"]

    def test_mreil_result_empty_recommendations(self):
        r = MREILResult(
            execution_id="e2", overall_score=1.0,
            task_fit_score=1.0, resource_efficiency=1.0, quality_score=1.0,
        )
        assert r.recommendations == []

    def test_workflow_recommendation(self):
        wr = WorkflowRecommendation(
            current_pattern="high_cost", recommended_pattern="cost_aware",
            expected_improvement="+20%", confidence=0.8,
        )
        d = wr.to_dict()
        assert d["workflow_recommendation"]["current_pattern"] == "high_cost"

    def test_agent_profile_defaults(self):
        p = AgentProfile(agent_id="a1")
        assert p.total_executions == 0
        assert p.success_rate == 0.0

    def test_agent_profile_success_rate(self):
        p = AgentProfile(agent_id="a1", total_executions=10, successful_executions=7)
        assert p.success_rate == 0.7

    def test_agent_profile_to_dict(self):
        p = AgentProfile(
            agent_id="a1", total_executions=5, successful_executions=4,
            average_quality=0.85, average_latency=5.0, average_cost=10.0,
            strengths=["debugging"], weaknesses=[],
        )
        d = p.to_dict()
        assert d["agent_profile"]["success_rate"] == 0.8
