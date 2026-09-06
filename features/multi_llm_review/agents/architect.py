"""
Architect Agent - Architecture, Design, Contracts, Invariants.
"""

from features.multi_llm_review.agents.base import AgentConfig, BaseReviewAgent
from features.multi_llm_review.review_schemas import ReviewTask


class ArchitectAgent(BaseReviewAgent):
    """Architecture Reviewer - focuses on design, contracts, and invariants."""

    def __init__(self, provider_registry=None):
        config = AgentConfig(
            role="architect",
            temperature=0.2,
            max_tokens=4096,
        )
        super().__init__(config, provider_registry)

    def get_system_prompt(self) -> str:
        return """You are an architecture reviewer for MUSCAL CORE.

Your mission: Verify architectural integrity, contract compliance, and invariant preservation.

Focus areas:
1. ARCHITECTURE: Layer separation, dependency direction, plugin boundaries
2. CONTRACTS: Interface compliance, schema validation, event schemas
3. INVARIANTS: Core immutability, write guards, hash chain integrity
4. PLUGIN SYSTEM: Isolation, hook contracts, sandbox compliance
5. DATA FLOW: Event sourcing, state reconstruction, provenance

Output ONLY structured findings. Be precise and architectural."""

    def get_analysis_prompt(self, task: "ReviewTask", context: str) -> str:
        return (
            f"""Analyze the following codebase for architectural integrity and contract compliance.

TARGET COMMIT: {task.target_commit}
TARGET FILES: {', '.join(task.target_files) if task.target_files else 'All changed files'}
REVIEW TYPE: {task.review_type}

CONTEXT:
{context}

Produce structured findings covering:
- Architecture violations (layer crossing, wrong dependencies)
- Contract violations (interface changes, schema drift)
- Invariant violations (core mutations, guard bypasses)
- Plugin system issues (isolation failures, hook contract breaks)
- Data flow problems (event sourcing gaps, state reconstruction)

Each finding must include: finding_type, severity, confidence (0-1), claim,
evidence_refs, file_refs."""
        )
