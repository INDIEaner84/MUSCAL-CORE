from __future__ import annotations

from features.orchestration.planner import ExecutionPlanner
from features.orchestration.models import TaskAnalysis, SelectionResult, AgentDefinition, AgentCapability


class TestExecutionPlanner:

    def _make_analysis(self, category: str = "bug_fix", risk: str = "MEDIUM",
                       complexity: str = "MODERATE", effort: str = "medium"):
        return TaskAnalysis(
            task_id="t1", category=category, complexity=complexity,
            risk_level=risk, required_capabilities=["debugging"],
            estimated_effort=effort, verification_required=True,
            recommended_autonomy="A3",
        )

    def _make_selection(self, agent_id: str = "large_model"):
        agent = AgentDefinition(
            agent_id=agent_id, capabilities=[AgentCapability("debugging", "test", 0.9)],
            models=["gpt-4o"], cost_profile="high", speed_profile="moderate",
            quality_profile="excellent", allowed_actions=["modify_files"],
            autonomy_level="A3",
        )
        return SelectionResult(selected_agent=agent, alternatives=[], reason="best", confidence=0.9)

    def test_plan_for_bug_fix(self):
        planner = ExecutionPlanner()
        analysis = self._make_analysis("bug_fix")
        selection = self._make_selection()
        plan = planner.plan(analysis, selection)
        assert len(plan.steps) >= 4
        actions = [s.action for s in plan.steps]
        assert "modify" in actions
        assert "verify" in actions

    def test_plan_for_feature(self):
        planner = ExecutionPlanner()
        analysis = self._make_analysis("feature")
        selection = self._make_selection()
        plan = planner.plan(analysis, selection)
        assert len(plan.steps) >= 5
        assert "document" in [s.action for s in plan.steps]

    def test_plan_for_documentation(self):
        planner = ExecutionPlanner()
        analysis = self._make_analysis("documentation", "LOW", "SIMPLE", "small")
        selection = self._make_selection("small_model")
        plan = planner.plan(analysis, selection)
        assert len(plan.steps) == 3

    def test_plan_for_refactor(self):
        planner = ExecutionPlanner()
        analysis = self._make_analysis("refactor")
        selection = self._make_selection()
        plan = planner.plan(analysis, selection)
        assert "modify" in [s.action for s in plan.steps]

    def test_plan_has_risk_controls_for_high_risk(self):
        planner = ExecutionPlanner()
        analysis = self._make_analysis("deployment", "HIGH", "COMPLEX", "large")
        selection = self._make_selection()
        plan = planner.plan(analysis, selection)
        assert len(plan.risk_controls) > 0
        assert any("approval" in c.lower() for c in plan.risk_controls)

    def test_plan_assigns_agent_to_modify_steps(self):
        planner = ExecutionPlanner()
        analysis = self._make_analysis("bug_fix")
        selection = self._make_selection("large_model")
        plan = planner.plan(analysis, selection)
        modify_steps = [s for s in plan.steps if s.action == "modify"]
        if modify_steps:
            assert modify_steps[0].agent == "large_model"

    def test_plan_autonomy_level_matches_analysis(self):
        planner = ExecutionPlanner()
        analysis = self._make_analysis()
        selection = self._make_selection()
        plan = planner.plan(analysis, selection)
        assert plan.autonomy_level == analysis.recommended_autonomy

    def test_plan_estimated_effort(self):
        planner = ExecutionPlanner()
        analysis = self._make_analysis(effort="large")
        selection = self._make_selection()
        plan = planner.plan(analysis, selection)
        assert plan.estimated_effort == "large"
