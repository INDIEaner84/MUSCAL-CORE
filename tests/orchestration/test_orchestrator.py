from __future__ import annotations

from features.orchestration.orchestrator import CognitiveOrchestrator
from features.orchestration.models import TaskAnalysis, SelectionResult, AgentDefinition, AgentCapability
from features.bridge.task_contract import TaskContract


class TestCognitiveOrchestrator:

    def _make_task(self, objective: str = "fix the login bug"):
        return TaskContract(id="t1", project="muscal-core", objective=objective)

    def test_orchestrate_full_flow(self):
        orch = CognitiveOrchestrator()
        task = self._make_task()
        result = orch.orchestrate(task)
        assert "analysis" in result
        assert "selection" in result
        assert "plan" in result

    def test_analyze_only(self):
        orch = CognitiveOrchestrator()
        task = self._make_task()
        analysis = orch.analyze(task)
        assert isinstance(analysis, TaskAnalysis)
        assert analysis.task_id == "t1"

    def test_select_agent_only(self):
        orch = CognitiveOrchestrator()
        analysis = TaskAnalysis(
            task_id="t1", category="bug_fix", complexity="MODERATE",
            risk_level="MEDIUM", required_capabilities=["debugging", "code_understanding"],
            estimated_effort="medium", verification_required=True, recommended_autonomy="A3",
        )
        selection = orch.select_agent(analysis)
        assert isinstance(selection, SelectionResult)

    def test_create_plan_only(self):
        orch = CognitiveOrchestrator()
        analysis = TaskAnalysis(
            task_id="t1", category="documentation", complexity="SIMPLE",
            risk_level="LOW", required_capabilities=["documentation"],
            estimated_effort="small", verification_required=False, recommended_autonomy="A4",
        )
        agent = AgentDefinition(
            agent_id="small_model", capabilities=[AgentCapability("documentation", "write docs", 0.9)],
            models=["gpt-4o-mini"], cost_profile="low", speed_profile="fast",
            quality_profile="adequate", allowed_actions=["modify_files"], autonomy_level="A3",
        )
        selection = SelectionResult(selected_agent=agent, alternatives=[], reason="best fit", confidence=0.9)
        plan = orch.create_plan(analysis, selection)
        assert len(plan.steps) > 0
        assert plan.task_id == "t1"

    def test_with_knowledge_context(self):
        orch = CognitiveOrchestrator(knowledge_context="previous fix for login bug used pattern X")
        task = self._make_task()
        result = orch.orchestrate(task)
        assert result["selection"]["agent_selection"]["confidence"] > 0

    def test_event_emitter(self):
        events = []
        class MockEmitter:
            def emit(self, topic, payload, **kwargs):
                events.append((topic, payload))
        orch = CognitiveOrchestrator(event_emitter=MockEmitter())
        task = self._make_task()
        orch.orchestrate(task)
        topics = [e[0] for e in events]
        assert "orchestration.task.analyzed" in topics
        assert "orchestration.agent.selected" in topics
        assert "orchestration.plan.created" in topics
