from __future__ import annotations

from features.orchestration import (
    CognitiveOrchestrator, TaskAnalyzer, AgentSelector,
    ExecutionPlanner, OrchestrationPolicy,
)
from features.bridge.task_contract import TaskContract


class TestOrchestrationIntegration:

    def test_full_pipeline_bug_fix(self):
        task = TaskContract(
            id="t1", project="muscal-core",
            objective="fix the authentication token refresh bug",
            constraints=["no breaking changes"],
        )
        orch = CognitiveOrchestrator()
        result = orch.orchestrate(task)

        analysis = result["analysis"]["task_analysis"]
        assert analysis["category"] == "bug_fix"
        assert "debugging" in analysis["required_capabilities"]

        selection = result["selection"]["agent_selection"]
        assert selection["selected_agent"] is not None

        plan = result["plan"]["execution_plan"]
        assert len(plan["steps"]) >= 4
        assert any(s["plan_step"]["action"] in ("modify", "test", "verify") for s in plan["steps"])

    def test_full_pipeline_documentation(self):
        task = TaskContract(
            id="t2", project="muscal-core",
            objective="write API documentation for the bridge module",
        )
        orch = CognitiveOrchestrator()
        result = orch.orchestrate(task)

        analysis = result["analysis"]["task_analysis"]
        assert analysis["category"] == "documentation"
        assert analysis["complexity"] == "SIMPLE"
        assert analysis["risk_level"] == "LOW"

        selection = result["selection"]["agent_selection"]
        assert selection["selected_agent"] is not None

    def test_policy_respected(self):
        task = TaskContract(
            id="t3", project="muscal-core",
            objective="deploy to production",
            constraints=["production environment"],
        )
        orch = CognitiveOrchestrator()
        result = orch.orchestrate(task)

        analysis = result["analysis"]["task_analysis"]
        assert analysis["risk_level"] == "HIGH"
        assert analysis["recommended_autonomy"] == "A2"

        plan = result["plan"]["execution_plan"]
        controls = plan["risk_controls"]
        assert any("approval" in c.lower() for c in controls)

    def test_high_risk_deployment_task(self):
        task = TaskContract(
            id="t4", project="muscal-core",
            objective="deploy release to production",
        )
        orch = CognitiveOrchestrator()
        result = orch.orchestrate(task)

        analysis = result["analysis"]["task_analysis"]
        assert analysis["category"] == "deployment"
        assert analysis["risk_level"] == "HIGH"
        assert analysis["recommended_autonomy"] == "A2"

    def test_knowledge_context_affects_confidence(self):
        task = TaskContract(
            id="t5", project="muscal-core",
            objective="refactor the data access layer",
        )
        orch_no_ctx = CognitiveOrchestrator()
        orch_ctx = CognitiveOrchestrator(
            knowledge_context="previous refactoring used strategy pattern with dependency injection"
        )
        r1 = orch_no_ctx.orchestrate(task)
        r2 = orch_ctx.orchestrate(task)
        assert r2["selection"]["agent_selection"]["confidence"] >= r1["selection"]["agent_selection"]["confidence"]

    def test_custom_components_composable(self):
        task = TaskContract(id="t6", project="muscal-core", objective="add unit tests")
        analyzer = TaskAnalyzer()
        selector = AgentSelector()
        policy = OrchestrationPolicy()
        planner = ExecutionPlanner(policy=policy)
        orch = CognitiveOrchestrator(analyzer=analyzer, selector=selector, planner=planner, policy=policy)
        result = orch.orchestrate(task)
        assert result["analysis"]["task_analysis"]["category"] == "testing"

    def test_testing_task_analysis(self):
        task = TaskContract(id="t7", project="muscal-core", objective="run coverage tests and assert results")
        analyzer = TaskAnalyzer()
        analysis = analyzer.analyze(task)
        assert analysis.category == "testing"

    def test_efficiency_estimate_ranges(self):
        from features.orchestration import AgentSelector, EfficiencyEstimate
        from features.orchestration.models import TaskAnalysis

        selector = AgentSelector()
        analysis = TaskAnalysis(
            task_id="t1", category="bug_fix", complexity="MODERATE",
            risk_level="MEDIUM", required_capabilities=["debugging", "code_understanding"],
            estimated_effort="medium", verification_required=True, recommended_autonomy="A3",
        )
        for agent in selector.agents:
            eff = selector.evaluate_agent_efficiency(agent, analysis)
            assert isinstance(eff, EfficiencyEstimate)
            assert 0.0 <= eff.quality_estimate <= 1.0
            assert 0.0 <= eff.task_fit_score <= 1.0
            assert 0.0 <= eff.confidence <= 1.0
