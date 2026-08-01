from __future__ import annotations

from typing import Any, Optional

from ..orchestration.models import TaskAnalysis, SelectionResult, AgentDefinition
from ..orchestration.agent_selector import AgentSelector
from .agent_profile import AgentProfileManager


class AdaptiveSelector:

    def __init__(self, selector: Optional[AgentSelector] = None,
                 profile_manager: Optional[AgentProfileManager] = None):
        self._selector = selector or AgentSelector()
        self._profiles = profile_manager or AgentProfileManager()

    def select(self, analysis: TaskAnalysis,
               knowledge_context: Optional[str] = None) -> SelectionResult:
        baseline = self._selector.select(analysis, knowledge_context)
        if baseline.selected_agent is None:
            return baseline

        scored: list[tuple[float, AgentDefinition, str]] = []
        for agent in self._selector.agents:
            score, reason = self._score_agent(agent, analysis, knowledge_context, baseline)
            scored.append((score, agent, reason))

        scored = [(s, a, r) for s, a, r in scored if s > 0.0]
        scored.sort(key=lambda x: x[0], reverse=True)

        if not scored:
            return baseline

        best_score, best_agent, best_reason = scored[0]
        alternatives = [a for _, a, _ in scored[1:]]
        confidence = min(1.0, best_score / 5.0)
        cost = best_agent.cost_profile
        cost_map = {"low": "1-5", "high": "10-30", "moderate": "5-15"}
        effort_map = {"small": "1x", "medium": "2x", "large": "5x"}
        estimated_cost = f"{cost_map.get(cost, '5-10')} credits ({effort_map.get(analysis.estimated_effort, '1x')})"

        return SelectionResult(
            selected_agent=best_agent,
            alternatives=alternatives,
            reason=best_reason,
            confidence=round(confidence, 2),
            estimated_cost=estimated_cost,
        )

    def _score_agent(self, agent: AgentDefinition, analysis: TaskAnalysis,
                     knowledge_context: Optional[str],
                     baseline: SelectionResult) -> tuple[float, str]:
        base_score, _ = self._selector._score_agent(agent, analysis, knowledge_context)
        if base_score <= 0.0:
            return 0.0, "No capability match"

        historical_boost = self._profiles.get_historical_boost(agent, analysis.category)
        adjusted = base_score + historical_boost

        reasons = [f"Capability score: {round(base_score, 2)}"]
        if historical_boost > 0:
            reasons.append(f"Historical boost: +{round(historical_boost, 2)}")
        elif historical_boost < 0:
            reasons.append(f"Historical penalty: {round(historical_boost, 2)}")

        return max(0.0, adjusted), "; ".join(reasons)

    @property
    def profile_manager(self) -> AgentProfileManager:
        return self._profiles
