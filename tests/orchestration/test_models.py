from __future__ import annotations

from features.orchestration.models import (
    TaskAnalysis, AgentCapability, AgentDefinition, ExecutionPlan,
    PlanStep, SelectionResult, EfficiencyEstimate, ORCHESTRATION_EVENTS,
)


class TestOrchestrationModels:

    def test_task_analysis_defaults(self):
        ta = TaskAnalysis(
            task_id="t1", category="bug_fix", complexity="SIMPLE",
            risk_level="LOW", required_capabilities=["debugging"],
            estimated_effort="small", verification_required=True,
            recommended_autonomy="A3",
        )
        assert ta.task_id == "t1"
        assert ta.reasoning == ""

    def test_task_analysis_to_dict(self):
        ta = TaskAnalysis(
            task_id="t1", category="bug_fix", complexity="MODERATE",
            risk_level="MEDIUM", required_capabilities=["debugging", "testing"],
            estimated_effort="medium", verification_required=True,
            recommended_autonomy="A3", reasoning="test",
        )
        d = ta.to_dict()
        assert d["task_analysis"]["task_id"] == "t1"
        assert d["task_analysis"]["category"] == "bug_fix"

    def test_agent_capability(self):
        cap = AgentCapability("debugging", "Complex debugging", 0.9)
        assert cap.strength == 0.9
        d = cap.to_dict()
        assert d["agent_capability"]["name"] == "debugging"

    def test_agent_definition(self):
        cap = AgentCapability("testing", "Writing tests", 0.8)
        agent = AgentDefinition(
            agent_id="test-agent", capabilities=[cap],
            models=["gpt-4o"], cost_profile="low",
            speed_profile="fast", quality_profile="adequate",
            allowed_actions=["run_tests"], autonomy_level="A3",
        )
        assert agent.agent_id == "test-agent"
        d = agent.to_dict()
        assert d["agent_definition"]["agent_id"] == "test-agent"

    def test_selection_result_no_agent(self):
        sr = SelectionResult(selected_agent=None, alternatives=[], reason="none", confidence=0.0)
        assert sr.selected_agent is None
        d = sr.to_dict()
        assert d["agent_selection"]["selected_agent"] is None

    def test_selection_result_with_agent(self):
        agent = AgentDefinition(
            agent_id="a1", capabilities=[],
            models=[], cost_profile="low",
            speed_profile="fast", quality_profile="adequate",
            allowed_actions=[], autonomy_level="A3",
        )
        sr = SelectionResult(selected_agent=agent, alternatives=[], reason="best match", confidence=0.85)
        d = sr.to_dict()
        assert d["agent_selection"]["confidence"] == 0.85

    def test_efficiency_estimate(self):
        ee = EfficiencyEstimate(quality_estimate=0.9, cost_estimate=0.3, latency_estimate=0.2, task_fit_score=0.85, confidence=0.8)
        d = ee.to_dict()
        assert d["efficiency"]["quality_estimate"] == 0.9

    def test_plan_step(self):
        ps = PlanStep(step_id="s1", action="modify", description="Implement fix")
        assert ps.risk_controls == []
        d = ps.to_dict()
        assert d["plan_step"]["action"] == "modify"

    def test_execution_plan(self):
        step = PlanStep(step_id="s1", action="analyze", description="Analyze")
        plan = ExecutionPlan(
            task_id="t1", steps=[step],
            required_agents=["a1"], risk_controls=["verify"],
            autonomy_level="A3",
        )
        d = plan.to_dict()
        assert d["execution_plan"]["task_id"] == "t1"
        assert d["execution_plan"]["estimated_effort"] == "unknown"

    def test_orchestration_events(self):
        expected = {
            "orchestration.task.analyzed",
            "orchestration.agent.selected",
            "orchestration.plan.created",
            "orchestration.execution.requested",
        }
        assert ORCHESTRATION_EVENTS == expected
