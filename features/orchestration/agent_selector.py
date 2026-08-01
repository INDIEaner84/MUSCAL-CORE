from __future__ import annotations

from typing import Any, Optional

from .models import TaskAnalysis, AgentDefinition, AgentCapability, SelectionResult, EfficiencyEstimate


DEFAULT_AGENTS: list[AgentDefinition] = [
    AgentDefinition(
        agent_id="small_model",
        capabilities=[
            AgentCapability("code_understanding", "Basic code comprehension", 0.6),
            AgentCapability("documentation", "Writing documentation and comments", 0.9),
            AgentCapability("communication", "Clear communication", 0.8),
            AgentCapability("testing", "Simple unit tests", 0.7),
            AgentCapability("code_generation", "Simple code transformations", 0.6),
        ],
        models=["gpt-4o-mini", "claude-3-haiku"],
        cost_profile="low",
        speed_profile="fast",
        quality_profile="adequate",
        allowed_actions=["modify_files", "run_tests", "create_reports", "read_only"],
        autonomy_level="A3",
    ),
    AgentDefinition(
        agent_id="large_model",
        capabilities=[
            AgentCapability("code_understanding", "Deep code comprehension", 0.95),
            AgentCapability("architecture", "System architecture design", 0.9),
            AgentCapability("debugging", "Complex debugging and root cause analysis", 0.95),
            AgentCapability("code_generation", "Complex code generation and refactoring", 0.9),
            AgentCapability("code_analysis", "Static and dynamic code analysis", 0.85),
            AgentCapability("testing", "Advanced test generation and coverage", 0.8),
            AgentCapability("documentation", "Technical documentation", 0.85),
            AgentCapability("communication", "Detailed technical communication", 0.85),
            AgentCapability("devops", "Deployment and infrastructure", 0.75),
        ],
        models=["gpt-4o", "claude-3-opus", "claude-3-sonnet"],
        cost_profile="high",
        speed_profile="moderate",
        quality_profile="excellent",
        allowed_actions=["modify_files", "run_tests", "create_reports", "read_only"],
        autonomy_level="A3",
    ),
]


class AgentSelector:

    def __init__(self, agents: Optional[list[AgentDefinition]] = None):
        self._agents = agents or list(DEFAULT_AGENTS)

    @property
    def agents(self) -> list[AgentDefinition]:
        return list(self._agents)

    def select(self, analysis: TaskAnalysis, knowledge_context: Optional[str] = None) -> SelectionResult:
        scored: list[tuple[float, AgentDefinition, str]] = []

        for agent in self._agents:
            score, reason = self._score_agent(agent, analysis, knowledge_context)
            scored.append((score, agent, reason))

        scored = [(s, a, r) for s, a, r in scored if s > 0.0]
        scored.sort(key=lambda x: x[0], reverse=True)

        if not scored:
            return SelectionResult(
                selected_agent=None, alternatives=[], reason="No agents available with matching capabilities",
                confidence=0.0, estimated_cost="unknown",
            )

        best_score, best_agent, best_reason = scored[0]
        alternatives = [a for _, a, _ in scored[1:]]
        confidence = min(1.0, best_score / 5.0)
        cost = best_agent.cost_profile
        estimated_cost = self._estimate_cost(best_agent, analysis)

        return SelectionResult(
            selected_agent=best_agent,
            alternatives=alternatives,
            reason=best_reason,
            confidence=round(confidence, 2),
            estimated_cost=estimated_cost,
        )

    def _score_agent(self, agent: AgentDefinition, analysis: TaskAnalysis,
                     knowledge_context: Optional[str] = None) -> tuple[float, str]:
        score = 0.0
        reasons: list[str] = []

        required = set(analysis.required_capabilities)
        agent_caps = {c.name for c in agent.capabilities}
        matched = required & agent_caps

        if not matched:
            return 0.0, "No capability match"

        for cap in agent.capabilities:
            if cap.name in required:
                score += cap.strength

        missing = required - agent_caps
        if missing:
            reasons.append(f"Missing: {', '.join(missing)}")
            score *= 0.5

        if knowledge_context:
            score += 0.2

        reason_parts = [f"Capability match: {', '.join(matched)}"]
        reason_parts.extend(reasons)
        return score, "; ".join(reason_parts)

    def _estimate_cost(self, agent: AgentDefinition, analysis: TaskAnalysis) -> str:
        cost_map = {"low": "1-5", "high": "10-30", "moderate": "5-15"}
        base = cost_map.get(agent.cost_profile, "5-10")
        effort_map = {"small": "1x", "medium": "2x", "large": "5x"}
        effort = effort_map.get(analysis.estimated_effort, "1x")
        return f"{base} credits ({effort})"

    def evaluate_agent_efficiency(self, agent: AgentDefinition, analysis: TaskAnalysis) -> EfficiencyEstimate:
        required = set(analysis.required_capabilities)
        agent_caps = {c.name for c in agent.capabilities}
        matched = required & agent_caps
        fit_score = len(matched) / max(len(required), 1)

        quality_map = {"excellent": 0.9, "high": 0.8, "adequate": 0.6, "low": 0.4}
        quality = quality_map.get(agent.quality_profile, 0.6)

        cost_map = {"low": 0.3, "moderate": 0.6, "high": 0.9}
        cost = cost_map.get(agent.cost_profile, 0.5)

        speed_map = {"fast": 0.3, "moderate": 0.6, "slow": 0.9}
        latency = speed_map.get(agent.speed_profile, 0.5)

        confidence = quality * 0.5 + fit_score * 0.3 + (1.0 - latency) * 0.2

        return EfficiencyEstimate(
            quality_estimate=round(quality, 2),
            cost_estimate=round(cost, 2),
            latency_estimate=round(latency, 2),
            task_fit_score=round(fit_score, 2),
            confidence=round(confidence, 2),
        )
