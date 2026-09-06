"""
Implementation Reviewer Agent - Code Quality, Correctness, Standards.
"""

from features.multi_llm_review.agents.base import AgentConfig, BaseReviewAgent
from features.multi_llm_review.review_schemas import ReviewTask


class ImplementationReviewerAgent(BaseReviewAgent):
    """Implementation Reviewer - focuses on code quality, correctness, and standards."""

    def __init__(self, provider_registry=None):
        config = AgentConfig(
            role="reviewer",
            temperature=0.1,
            max_tokens=4096,
        )
        super().__init__(config, provider_registry)

    def get_system_prompt(self) -> str:
        return """You are an implementation reviewer for MUSCAL CORE.

Your mission: Verify code quality, correctness, and adherence to standards.

Focus areas:
1. CORRECTNESS: Logic errors, edge cases, race conditions, resource leaks
2. QUALITY: Readability, maintainability, complexity, naming
3. STANDARDS: Type hints, docstrings, error handling, logging
4. TESTING: Test coverage, test quality, deterministic tests
5. PERFORMANCE: Unnecessary allocations, blocking calls, N+1 queries

Output ONLY structured findings. Be thorough but fair."""

    def get_analysis_prompt(self, task: "ReviewTask", context: str) -> str:
        return (
            f"""Analyze the following codebase for implementation quality and correctness.

TARGET COMMIT: {task.target_commit}
TARGET FILES: {', '.join(task.target_files) if task.target_files else 'All changed files'}
REVIEW TYPE: {task.review_type}

CONTEXT:
{context}

Produce structured findings covering:
- Correctness issues (logic bugs, edge cases, races, leaks)
- Quality issues (complexity, naming, readability)
- Standards violations (types, docs, errors, logging)
- Testing gaps (missing tests, flaky tests, low coverage)
- Performance issues (allocations, blocking, N+1)

Each finding must include: finding_type, severity, confidence (0-1), claim,
evidence_refs, file_refs."""
        )
