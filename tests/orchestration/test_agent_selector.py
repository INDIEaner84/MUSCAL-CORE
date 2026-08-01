from __future__ import annotations

from features.orchestration.agent_selector import AgentSelector, DEFAULT_AGENTS
from features.orchestration.models import TaskAnalysis, AgentDefinition, AgentCapability


class TestAgentSelector:

    def _make_analysis(self, category: str = "bug_fix", complexity: str = "MODERATE",
                       risk: str = "MEDIUM", capabilities: list = None, effort: str = "medium"):
        return TaskAnalysis(
            task_id="t1", category=category, complexity=complexity,
            risk_level=risk, required_capabilities=capabilities or ["code_understanding", "debugging"],
            estimated_effort=effort, verification_required=True, recommended_autonomy="A3",
        )

    def test_select_agent_for_documentation(self):
        selector = AgentSelector()
        analysis = self._make_analysis("documentation", "SIMPLE", "LOW",
                                        capabilities=["code_understanding", "documentation", "communication"],
                                        effort="small")
        result = selector.select(analysis)
        assert result.selected_agent is not None
        assert result.confidence > 0.0

    def test_select_large_model_for_complex_debugging(self):
        selector = AgentSelector()
        analysis = self._make_analysis("bug_fix", "COMPLEX", "MEDIUM",
                                        capabilities=["code_understanding", "debugging", "architecture", "testing"])
        result = selector.select(analysis)
        assert result.selected_agent is not None
        assert result.selected_agent.agent_id == "large_model"

    def test_fallback_when_no_capability_match(self):
        selector = AgentSelector()
        analysis = self._make_analysis(capabilities=["unknown_capability"])
        result = selector.select(analysis)
        assert result.selected_agent is None
        assert result.confidence == 0.0

    def test_confidence_scoring(self):
        selector = AgentSelector()
        analysis = self._make_analysis("documentation", "SIMPLE", "LOW",
                                        capabilities=["documentation", "communication"])
        result = selector.select(analysis)
        assert 0.0 < result.confidence <= 1.0

    def test_alternatives_included(self):
        selector = AgentSelector()
        analysis = self._make_analysis()
        result = selector.select(analysis)
        assert len(result.alternatives) >= 0

    def test_evaluate_agent_efficiency(self):
        selector = AgentSelector()
        analysis = self._make_analysis()
        agent = DEFAULT_AGENTS[0]
        eff = selector.evaluate_agent_efficiency(agent, analysis)
        assert 0.0 <= eff.quality_estimate <= 1.0
        assert 0.0 <= eff.task_fit_score <= 1.0

    def test_estimate_cost_small(self):
        selector = AgentSelector()
        analysis = self._make_analysis(effort="small")
        agent = DEFAULT_AGENTS[0]
        cost = selector._estimate_cost(agent, analysis)
        assert "credits" in cost

    def test_knowledge_context_boost(self):
        selector = AgentSelector()
        analysis = self._make_analysis("documentation", "SIMPLE", "LOW",
                                        capabilities=["documentation", "communication"])
        result_no_ctx = selector.select(analysis)
        result_with_ctx = selector.select(analysis, knowledge_context="previous docs patterns")
        assert result_with_ctx.confidence >= result_no_ctx.confidence

    def test_custom_agents(self):
        custom = [
            AgentDefinition(
                agent_id="custom", capabilities=[AgentCapability("debugging", "Custom debug", 1.0)],
                models=["custom-model"], cost_profile="low", speed_profile="fast",
                quality_profile="high", allowed_actions=["modify_files"], autonomy_level="A4",
            )
        ]
        selector = AgentSelector(agents=custom)
        analysis = self._make_analysis(capabilities=["debugging"])
        result = selector.select(analysis)
        assert result.selected_agent.agent_id == "custom"

    def test_agents_property(self):
        selector = AgentSelector()
        agents = selector.agents
        assert len(agents) >= 2
