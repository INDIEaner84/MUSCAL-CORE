from __future__ import annotations

from typing import Any, Optional

from .models import AgentProfile, ExecutionMetrics
from ..orchestration.models import AgentDefinition


class AgentProfileManager:

    def __init__(self):
        self._profiles: dict[str, AgentProfile] = {}

    def get_profile(self, agent_id: str) -> AgentProfile:
        if agent_id not in self._profiles:
            self._profiles[agent_id] = AgentProfile(agent_id=agent_id)
        return self._profiles[agent_id]

    def update_from_execution(self, metrics: ExecutionMetrics, task_category: str = "") -> AgentProfile:
        profile = self.get_profile(metrics.agent_id)
        profile.total_executions += 1
        if metrics.success:
            profile.successful_executions += 1
        if task_category:
            profile.task_categories[task_category] = profile.task_categories.get(task_category, 0) + 1

        n = profile.total_executions
        profile.average_quality = (
            (profile.average_quality * (n - 1) + metrics.verification_score) / n
        )
        profile.average_latency = (
            (profile.average_latency * (n - 1) + metrics.latency) / n
        )
        profile.average_cost = (
            (profile.average_cost * (n - 1) + metrics.duration) / n
        )
        self._update_strengths_weaknesses(profile, metrics, task_category)
        return profile

    def _update_strengths_weaknesses(self, profile: AgentProfile,
                                      metrics: ExecutionMetrics,
                                      task_category: str) -> None:
        if task_category and metrics.success:
            if task_category not in profile.strengths:
                profile.strengths.append(task_category)
        if task_category and not metrics.success:
            if task_category not in profile.strengths and task_category not in profile.weaknesses:
                profile.weaknesses.append(task_category)
            if task_category in profile.strengths:
                profile.strengths.remove(task_category)

    def get_all_profiles(self) -> list[AgentProfile]:
        return list(self._profiles.values())

    def calculate_success_rate(self, agent_id: str) -> float:
        profile = self._profiles.get(agent_id)
        if profile is None or profile.total_executions == 0:
            return 0.0
        return profile.success_rate

    def get_historical_boost(self, agent: AgentDefinition, task_category: str) -> float:
        profile = self._profiles.get(agent.agent_id)
        if profile is None or profile.total_executions == 0:
            return 0.0
        boost = 0.0
        if task_category in profile.strengths:
            boost += 0.15
        if task_category in profile.weaknesses:
            boost -= 0.2
        boost += profile.success_rate * 0.1
        return max(-0.5, min(0.5, boost))
