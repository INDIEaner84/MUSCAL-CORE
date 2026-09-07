"""
Pipeline Integration - Integrates Multi-LLM Review into MUSCAL Pipeline.
"""

from dataclasses import dataclass
from typing import Optional
from uuid import uuid4

from features.multi_llm_review.orchestrator.orchestrator import (
    OrchestratorConfig,
    ReviewOrchestrator,
    ReviewResult,
)
from features.multi_llm_review.review_schemas import ReviewTask
from runtime.event_store import EventStore


@dataclass
class PipelineReviewConfig:
    """Configuration for pipeline-integrated review."""
    enabled: bool = True
    run_on_commit: bool = True
    run_on_pr: bool = True
    run_on_schedule: bool = False
    orchestrator_config: OrchestratorConfig = None


class PipelineReviewIntegration:
    """Integrates Multi-LLM Review into MUSCAL execution pipeline."""

    def __init__(
        self,
        event_store: EventStore,
        config: PipelineReviewConfig | None = None,
    ):
        self.event_store = event_store
        self.config = config or PipelineReviewConfig()
        self.orchestrator_config = self.config.orchestrator_config or OrchestratorConfig()
        self.orchestrator = ReviewOrchestrator(event_store, self.orchestrator_config)

    def on_execution_completed(self, execution_id: str, commit_sha: str) -> Optional[ReviewResult]:
        """Hook called when execution completes - triggers review if enabled."""
        if not self.config.enabled:
            return None

        if not self.config.run_on_commit:
            return None

        # Create review task
        task = ReviewTask(
            task_id=str(uuid4()),
            target_commit=commit_sha,
            review_type="full",
        )

        return self.run_review(task)

    def on_pull_request(self, pr_number: int, commit_sha: str) -> Optional[ReviewResult]:
        """Hook called for PR events."""
        if not self.config.enabled:
            return None

        if not self.config.run_on_pr:
            return None

        task = ReviewTask(
            task_id=str(uuid4()),
            target_commit=commit_sha,
            target_files=[],  # Would be populated from PR diff
            review_type="pr",
        )

        return self.run_review(task)

    def run_review(self, task: ReviewTask) -> ReviewResult:
        """Execute review and return result."""
        return self.orchestrator.run_review(task)

    def get_review_result(self, task_id: str) -> Optional[ReviewResult]:
        """Retrieve a previous review result (placeholder)."""
        # Would query event store for previous results
        return None
