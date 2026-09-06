"""
Judge Agent - Meta-Analysis, Conflict Resolution, Dissent Detection.
"""


from features.multi_llm_review.agents.base import AgentConfig, BaseReviewAgent
from features.multi_llm_review.review_schemas import ReviewTask


class JudgeAgent(BaseReviewAgent):
    """Meta-Judge - synthesizes findings, resolves conflicts, detects dissent."""

    def __init__(self, provider_registry=None):
        config = AgentConfig(
            role="judge",
            temperature=0.0,
            max_tokens=4096,
        )
        super().__init__(config, provider_registry)

    def get_system_prompt(self) -> str:
        return """You are the meta-judge for MUSCAL CORE multi-LLM review.

Your mission: Synthesize findings from multiple agents, resolve conflicts,
detect dissent, and produce consensus recommendations.

Focus areas:
1. SYNTHESIS: Aggregate findings across agents, deduplicate
2. CONFLICT RESOLUTION: Technical Verification > Model Consensus
3. DISSENT DETECTION: Identify disagreements between agents
4. PRIORITIZATION: Rank by severity, confidence, evidence strength
5. ACTIONABILITY: Concrete, prioritized next steps

Evidence Hierarchy (strongest first):
1. Runtime Observables
2. Executable Test Results
3. Repository Code
4. Cryptographic Integrity
5. EventStore/MCPL Events
6. Configuration
7. ADRs
8. SSOT
9. LLM Analysis (weakest)
10. LLM Consensus (weakest)

Output ONLY structured consensus with status, confidence, dissent, recommended_actions."""

    def get_analysis_prompt(self, task: "ReviewTask", context: str) -> str:
        return f"""Synthesize the multi-agent review findings for this task.

TARGET COMMIT: {task.target_commit}
TARGET FILES: {', '.join(task.target_files) if task.target_files else 'All changed files'}
REVIEW TYPE: {task.review_type}

AGENT FINDINGS:
{context}

Produce a consensus with:
- status: VERIFIED | PARTIALLY | UNVERIFIED | CONTRADICTION
- confidence: 0.0-1.0 (weighted: Technical Verification 2x, Model Consensus 1x)
- dissent: list of conflicts between agents
- recommended_actions: prioritized next steps (max 5)

Apply Evidence Hierarchy: Technical Verification > Model Consensus.
If tests fail but LLMs say VERIFIED -> CONTRADICTION.
If all LLMs high confidence + tests pass -> VERIFIED.
If mixed confidence -> PARTIALLY.
If no LLM findings -> UNVERIFIED."""
