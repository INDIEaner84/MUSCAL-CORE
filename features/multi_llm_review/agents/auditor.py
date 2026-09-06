"""
Auditor Agent - Security, Gaps, Stubs, Demo-vs-Production, Execution Gap.
"""

from features.multi_llm_review.agents.base import AgentConfig, BaseReviewAgent
from features.multi_llm_review.review_schemas import ReviewTask


class AuditorAgent(BaseReviewAgent):
    """Adversarial Auditor - focuses on security, gaps, and execution integrity."""

    def __init__(self, provider_registry=None):
        config = AgentConfig(
            role="auditor",
            temperature=0.1,
            max_tokens=4096,
        )
        super().__init__(config, provider_registry)

    def get_system_prompt(self) -> str:
        return """You are an adversarial security auditor for MUSCAL CORE.

Your mission: Find security vulnerabilities, architectural gaps, stub implementations,
demo-vs-production mismatches, and execution gaps.

Focus areas:
1. SECURITY: Injection, path traversal, auth bypass, secrets exposure
2. GAPS: Unimplemented features, missing error handling, incomplete contracts
3. STUBS: Placeholder implementations, TODO/FIXME in production paths
4. DEMO-VS-PROD: Hardcoded values, mock data in production paths
5. EXECUTION GAP: Planned vs executed, unmapped tasks, failed recoveries

Output ONLY structured findings. Be thorough and adversarial."""

    def get_analysis_prompt(self, task: "ReviewTask", context: str) -> str:
        return (
            f"""Analyze the following codebase for security, gaps, and execution integrity.

TARGET COMMIT: {task.target_commit}
TARGET FILES: {', '.join(task.target_files) if task.target_files else 'All changed files'}
REVIEW TYPE: {task.review_type}

CONTEXT:
{context}

Produce structured findings covering:
- Security vulnerabilities (injection, traversal, auth, secrets)
- Architectural gaps (unimplemented contracts, missing handlers)
- Stub implementations in production paths
- Demo/production mismatches (hardcoded values, mocks)
- Execution gaps (unmapped tasks, failed recoveries, incomplete pipelines)

Each finding must include: finding_type, severity, confidence (0-1), claim,
evidence_refs, file_refs."""
        )
