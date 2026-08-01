from __future__ import annotations

from features.optimization import (
    MetricsCollector, MREILEvaluator, AgentProfileManager,
    WorkflowOptimizer, AdaptiveSelector, ExecutionMetrics, QualityMetrics,
)
from features.orchestration.models import TaskAnalysis


class TestOptimizationIntegration:

    def test_full_flow_successful(self):
        # 1. Collect metrics
        collector = MetricsCollector()
        class MockOutput:
            status = "completed"
            task_id = "t1"
            agent_id = "large_model"
            model_id = "gpt-4o"
            execution_record = {"bridge_execution_id": "e1", "task_identity": {"id": "t1"}}
            normalized = type("N", (), {"to_dict": lambda self: {"result": {"meta": {"duration": 5.0, "tokens": 200, "latency": 4.5}}}})()
            def to_dict(self):
                return {"execution_record": self.execution_record, "normalized": self.normalized.to_dict()}
        class MockVer:
            def to_dict(self):
                return {"verification_report": {"status": "passed", "facts": []}}

        metrics = collector.collect(MockOutput(), MockVer())
        assert isinstance(metrics, ExecutionMetrics)
        assert metrics.success is True
        assert metrics.verification_score == 1.0

        # 2. Evaluate
        evaluator = MREILEvaluator()
        quality = collector.collect_quality(MockVer(), knowledge_value=0.8)
        result = evaluator.evaluate(metrics, quality=quality)
        assert result.overall_score > 0.5
        assert len(result.recommendations) == 0

        # 3. Update profile
        mgr = AgentProfileManager()
        profile = mgr.update_from_execution(metrics, task_category="bug_fix")
        assert profile.total_executions == 1
        assert profile.successful_executions == 1

        # 4. Record workflow (need 2+ records)
        opt = WorkflowOptimizer()
        opt.record_evaluation(result)
        opt.record_evaluation(result)
        recommendation = opt.optimize_workflow()
        assert recommendation.confidence > 0.0

        # 5. Adaptive selection
        selector = AdaptiveSelector(profile_manager=mgr)
        analysis = TaskAnalysis(
            task_id="t2", category="bug_fix", complexity="MODERATE",
            risk_level="MEDIUM", required_capabilities=["code_understanding", "debugging"],
            estimated_effort="medium", verification_required=True, recommended_autonomy="A3",
        )
        selection = selector.select(analysis)
        assert selection.selected_agent is not None
        assert selection.confidence > 0.0

    def test_failed_execution_flow(self):
        collector = MetricsCollector()
        class MockFailed:
            status = "failed"
            task_id = "t1"
            agent_id = "small_model"
            model_id = "gpt-4o-mini"
            execution_record = {"bridge_execution_id": "e2"}
            normalized = type("N", (), {"to_dict": lambda self: {"result": {"meta": {"duration": 30.0, "tokens": 1000}}}})()
            def to_dict(self):
                return {"execution_record": self.execution_record, "normalized": self.normalized.to_dict()}

        metrics = collector.collect(MockFailed())
        assert metrics.success is False

        evaluator = MREILEvaluator()
        result = evaluator.evaluate(metrics)
        assert result.overall_score < 0.5
        assert len(result.recommendations) > 0

        mgr = AgentProfileManager()
        profile = mgr.update_from_execution(metrics, task_category="bug_fix")
        assert profile.successful_executions == 0

    def test_no_auto_authority_escalation(self):
        from features.orchestration.policy import OrchestrationPolicy
        policy = OrchestrationPolicy()
        assert policy.can_execute_plan("A0") is False
        assert policy.can_execute_plan("A3") is True
        assert policy.requires_approval("push_remote", "A3") is True

    def test_adaptive_selection_with_profile_history(self):
        mgr = AgentProfileManager()
        for i in range(5):
            mgr.update_from_execution(
                ExecutionMetrics(
                    execution_id=f"e{i}", task_id="t1", agent_id="large_model",
                    model_id="gpt-4o", duration=5.0, tokens=200, cpu_time=1.0,
                    memory_usage=128, latency=4.5, success=True, verification_score=0.95,
                ), task_category="bug_fix")

        selector = AdaptiveSelector(profile_manager=mgr)
        analysis = TaskAnalysis(
            task_id="t2", category="bug_fix", complexity="COMPLEX",
            risk_level="MEDIUM", required_capabilities=["debugging", "architecture"],
            estimated_effort="large", verification_required=True, recommended_autonomy="A3",
        )
        result = selector.select(analysis)
        assert result.selected_agent is not None
        assert "historical" in result.reason.lower() or "capability" in result.reason.lower()
