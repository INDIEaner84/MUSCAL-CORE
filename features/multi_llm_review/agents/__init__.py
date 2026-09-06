"""
Review Agents Package - Multi-LLM Review Agents.

Provides specialized agents for different review perspectives.
"""

from features.multi_llm_review.agents.architect import ArchitectAgent
from features.multi_llm_review.agents.auditor import AuditorAgent
from features.multi_llm_review.agents.base import AgentConfig, BaseReviewAgent
from features.multi_llm_review.agents.judge import JudgeAgent
from features.multi_llm_review.agents.reviewer import ImplementationReviewerAgent

__version__ = "0.1.0"
__all__ = [
    "BaseReviewAgent",
    "AgentConfig",
    "AuditorAgent",
    "ArchitectAgent",
    "ImplementationReviewerAgent",
    "JudgeAgent",
    "create_agent",
    "create_all_agents",
]


def create_agent(role: str, provider_registry=None, **kwargs) -> BaseReviewAgent:
    """Factory function to create a review agent by role."""
    agents = {
        "auditor": AuditorAgent,
        "architect": ArchitectAgent,
        "reviewer": ImplementationReviewerAgent,
        "judge": JudgeAgent,
    }

    if role not in agents:
        raise ValueError(f"Unknown agent role: {role}. Available: {list(agents.keys())}")

    return agents[role](provider_registry)


def create_all_agents(provider_registry=None) -> dict[str, BaseReviewAgent]:
    """Create all standard review agents."""
    return {
        "auditor": AuditorAgent(provider_registry),
        "architect": ArchitectAgent(provider_registry),
        "reviewer": ImplementationReviewerAgent(provider_registry),
        "judge": JudgeAgent(provider_registry),
    }
