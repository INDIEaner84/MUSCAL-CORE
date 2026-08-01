from __future__ import annotations

from features.optimization.agent_profile import AgentProfileManager
from features.optimization.models import ExecutionMetrics, AgentProfile
from features.orchestration.models import AgentDefinition, AgentCapability


class TestAgentProfileManager:

    def _make_metrics(self, agent_id="a1", success=True, v_score=0.9, duration=10.0, latency=5.0):
        return ExecutionMetrics(
            execution_id="e1", task_id="t1", agent_id=agent_id, model_id="m1",
            duration=duration, tokens=500, cpu_time=2.0, memory_usage=256,
            latency=latency, success=success, verification_score=v_score,
        )

    def test_get_profile_creates_new(self):
        mgr = AgentProfileManager()
        profile = mgr.get_profile("new_agent")
        assert profile.agent_id == "new_agent"
        assert profile.total_executions == 0

    def test_update_from_execution(self):
        mgr = AgentProfileManager()
        metrics = self._make_metrics("a1")
        profile = mgr.update_from_execution(metrics, task_category="bug_fix")
        assert profile.total_executions == 1
        assert profile.successful_executions == 1
        assert "bug_fix" in profile.strengths

    def test_update_from_failed_execution(self):
        mgr = AgentProfileManager()
        metrics = self._make_metrics("a1", success=False, v_score=0.0)
        profile = mgr.update_from_execution(metrics, task_category="deployment")
        assert profile.total_executions == 1
        assert profile.successful_executions == 0
        assert profile.success_rate == 0.0
        assert "deployment" in profile.weaknesses

    def test_success_rate_multiple(self):
        mgr = AgentProfileManager()
        for i in range(5):
            m = self._make_metrics("a1", success=True)
            mgr.update_from_execution(m, "bug_fix")
        for i in range(5):
            m = self._make_metrics("a1", success=False, v_score=0.0)
            mgr.update_from_execution(m, "refactor")
        profile = mgr.get_profile("a1")
        assert profile.total_executions == 10
        assert profile.successful_executions == 5
        assert profile.success_rate == 0.5

    def test_average_quality_tracking(self):
        mgr = AgentProfileManager()
        m1 = self._make_metrics("a1", v_score=1.0)
        mgr.update_from_execution(m1, "bug_fix")
        m2 = self._make_metrics("a1", v_score=0.5)
        mgr.update_from_execution(m2, "bug_fix")
        profile = mgr.get_profile("a1")
        assert profile.average_quality == 0.75

    def test_get_all_profiles(self):
        mgr = AgentProfileManager()
        mgr.update_from_execution(self._make_metrics("a1"), "bug_fix")
        mgr.update_from_execution(self._make_metrics("a2"), "feature")
        assert len(mgr.get_all_profiles()) == 2

    def test_calculate_success_rate_no_data(self):
        mgr = AgentProfileManager()
        assert mgr.calculate_success_rate("nonexistent") == 0.0

    def test_get_historical_boost_strength(self):
        mgr = AgentProfileManager()
        agent = AgentDefinition(
            agent_id="a1", capabilities=[AgentCapability("debugging", "test", 0.9)],
            models=[], cost_profile="low", speed_profile="fast",
            quality_profile="adequate", allowed_actions=[], autonomy_level="A3",
        )
        for _ in range(5):
            mgr.update_from_execution(self._make_metrics("a1"), "bug_fix")
        boost = mgr.get_historical_boost(agent, "bug_fix")
        assert boost > 0.0

    def test_get_historical_boost_weakness(self):
        mgr = AgentProfileManager()
        agent = AgentDefinition(
            agent_id="a1", capabilities=[AgentCapability("debugging", "test", 0.9)],
            models=[], cost_profile="low", speed_profile="fast",
            quality_profile="adequate", allowed_actions=[], autonomy_level="A3",
        )
        mgr.update_from_execution(self._make_metrics("a1", success=False), "deployment")
        boost = mgr.get_historical_boost(agent, "deployment")
        assert boost < 0.0

    def test_get_historical_boost_no_data(self):
        mgr = AgentProfileManager()
        agent = AgentDefinition(
            agent_id="a1", capabilities=[],
            models=[], cost_profile="low", speed_profile="fast",
            quality_profile="adequate", allowed_actions=[], autonomy_level="A3",
        )
        boost = mgr.get_historical_boost(agent, "bug_fix")
        assert boost == 0.0
