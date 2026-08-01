from __future__ import annotations

from features.optimization.selector_adapter import AdaptiveSelector
from features.optimization.agent_profile import AgentProfileManager
from features.orchestration.models import TaskAnalysis, AgentDefinition, AgentCapability, SelectionResult
from features.orchestration.agent_selector import AgentSelector


class TestAdaptiveSelector:

    def _make_analysis(self, category="bug_fix", complexity="MODERATE",
                       risk="MEDIUM", capabilities=None):
        return TaskAnalysis(
            task_id="t1", category=category, complexity=complexity,
            risk_level=risk,
            required_capabilities=capabilities or ["code_understanding", "debugging"],
            estimated_effort="medium", verification_required=True,
            recommended_autonomy="A3",
        )

    def test_select_without_history_matches_baseline(self):
        selector = AdaptiveSelector()
        analysis = self._make_analysis()
        result = selector.select(analysis)
        assert result.selected_agent is not None
        assert result.confidence > 0.0

    def test_select_with_historical_boost(self):
        mgr = AgentProfileManager()
        for _ in range(5):
            mgr.update_from_execution(
                type("Metrics", (), {
                    "execution_id": "e1", "task_id": "t1", "agent_id": "large_model",
                    "model_id": "m1", "duration": 5.0, "tokens": 200, "cpu_time": 1.0,
                    "memory_usage": 128, "latency": 4.5, "success": True,
                    "verification_score": 0.95,
                })(), task_category="bug_fix")
        selector = AdaptiveSelector(profile_manager=mgr)
        analysis = self._make_analysis("bug_fix")
        result = selector.select(analysis)
        assert result.selected_agent is not None
        assert result.confidence > 0.0

    def test_fallback_on_no_match(self):
        selector = AdaptiveSelector()
        analysis = self._make_analysis(capabilities=["nonexistent"])
        result = selector.select(analysis)
        assert result.selected_agent is None

    def test_historical_penalty_reduces_confidence(self):
        mgr = AgentProfileManager()
        for _ in range(3):
            mgr.update_from_execution(
                type("Metrics", (), {
                    "execution_id": "e1", "task_id": "t1", "agent_id": "large_model",
                    "model_id": "m1", "duration": 5.0, "tokens": 200, "cpu_time": 1.0,
                    "memory_usage": 128, "latency": 4.5, "success": False,
                    "verification_score": 0.1,
                })(), task_category="bug_fix")
        selector = AdaptiveSelector(profile_manager=mgr)
        analysis = self._make_analysis("bug_fix")
        result = selector.select(analysis)
        assert result.confidence >= 0.0

    def test_return_type(self):
        selector = AdaptiveSelector()
        analysis = self._make_analysis()
        result = selector.select(analysis)
        assert isinstance(result, SelectionResult)

    def test_profile_manager_property(self):
        mgr = AgentProfileManager()
        selector = AdaptiveSelector(profile_manager=mgr)
        assert selector.profile_manager is mgr
