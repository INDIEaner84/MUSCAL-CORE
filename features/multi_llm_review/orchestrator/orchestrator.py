"""
Review Orchestrator - Coordinates multi-agent review pipeline.

Integrates Phase 1 (Evidence), Phase 1b (Provider), Phase 2 (Agents)
into a complete review pipeline.
"""

import time
from dataclasses import dataclass, field
from uuid import uuid4

from features.multi_llm_review.agents import (
    BaseReviewAgent,
    create_all_agents,
)
from features.multi_llm_review.consensus_builder import ConsensusBuilder
from features.multi_llm_review.evidence_store import ReviewEvidenceStore
from features.multi_llm_review.review_schemas import (
    Consensus,
    ReviewTask,
    TechnicalVerification,
)
from features.multi_llm_review.technical_verifier import TechnicalVerifier
from runtime.event_store import EventStore


@dataclass
class OrchestratorConfig:
    """Configuration for the review orchestrator."""
    enable_auditor: bool = True
    enable_architect: bool = True
    enable_reviewer: bool = True
    enable_judge: bool = True
    max_parallel_agents: int = 4
    timeout_seconds: int = 300
    # Cost tracking
    track_costs: bool = True
    cost_budget_usd: float = 50.0


@dataclass
class ReviewResult:
    """Complete result of a review run."""
    run_id: str
    review_task: ReviewTask
    technical_verification: TechnicalVerification
    agent_findings: dict[str, list]  # role -> findings
    consensus: Consensus
    started_at: float
    completed_at: float
    duration_seconds: float
    errors: list[str] = field(default_factory=list)
    total_cost_usd: float = 0.0
    total_tokens: int = 0
    cost_per_agent: dict[str, float] = field(default_factory=dict)
    tokens_per_agent: dict[str, int] = field(default_factory=dict)


class ReviewOrchestrator:
    """Orchestrates the complete multi-LLM review pipeline."""

    def __init__(
        self,
        event_store: EventStore,
        config: OrchestratorConfig | None = None,
    ):
        self.event_store = event_store
        self.config = config or OrchestratorConfig()
        self.evidence_store = ReviewEvidenceStore(event_store)
        self.technical_verifier = TechnicalVerifier()
        self.consensus_builder = ConsensusBuilder()
        self._agents: dict[str, BaseReviewAgent] = {}

    def _get_agents(self) -> dict[str, BaseReviewAgent]:
        """Get or create all review agents."""
        if not self._agents:
            all_agents = create_all_agents()
            self._agents = {
                role: agent
                for role, agent in all_agents.items()
                if self._is_enabled(role)
            }
        return self._agents

    def _is_enabled(self, role: str) -> bool:
        """Check if agent role is enabled."""
        return getattr(self.config, f"enable_{role}", True)

    def run_review(self, task: ReviewTask) -> ReviewResult:
        """Execute complete review pipeline for a task."""
        run_id = str(uuid4())
        started_at = time.time()
        errors = []
        total_cost_usd = 0.0
        total_tokens = 0
        cost_per_agent = {}
        tokens_per_agent = {}

        try:
            # 1. Record review task
            self.evidence_store.record_review_task(task)

            # 2. Technical Verification (deterministic, strongest evidence)
            tech_verification = self.technical_verifier.verify(task)
            self.evidence_store.record_technical_verification(tech_verification)

            # 3. Run Model Agents in parallel (or sequential)
            agent_findings, cost_info = self._run_model_agents(task, errors)

            # 4. Build Consensus (Judge agent + Technical Verification)
            consensus = self._build_consensus(task, agent_findings, tech_verification, errors)
            self.evidence_store.record_consensus(consensus)

            # Aggregate costs from agents
            for role, cost in self._agent_costs.items():
                total_cost_usd += cost.get("cost_usd", 0.0)
                total_tokens += cost.get("tokens", 0)
                cost_per_agent[role] = cost.get("cost_usd", 0.0)
                tokens_per_agent[role] = cost.get("tokens", 0)

        except Exception as e:
            errors.append(f"Orchestrator error: {e}")

        completed_at = time.time()

        return ReviewResult(
            run_id=run_id,
            review_task=task,
            technical_verification=tech_verification,
            agent_findings=agent_findings,
            consensus=consensus,
            started_at=started_at,
            completed_at=completed_at,
            duration_seconds=completed_at - started_at,
            errors=errors,
            total_cost_usd=total_cost_usd,
            total_tokens=total_tokens,
            cost_per_agent=cost_per_agent,
            tokens_per_agent=tokens_per_agent,
        )

    def _run_model_agents(
        self,
        task: ReviewTask,
        errors: list[str],
    ) -> tuple[dict[str, list], dict[str, dict]]:
        """Run all enabled model agents and collect findings with cost tracking."""
        agents = self._get_agents()
        agent_findings = {}
        self._agent_costs = {}  # role -> {"cost_usd": float, "tokens": int}

        # Collect context for agents (repo state, diff, etc.)
        context = self._build_context(task)

        for role, agent in agents.items():
            try:
                findings = agent.analyze(task, context)
                agent_findings[role] = findings

                # Record each finding
                for finding in findings:
                    self.evidence_store.record_review_finding(finding)

                # Extract cost info from agent if available
                cost_info = getattr(agent, "last_cost_info", None)
                if cost_info:
                    self._agent_costs[role] = {
                        "cost_usd": cost_info.get("cost_usd", 0.0),
                        "tokens": cost_info.get("tokens", 0),
                    }
                else:
                    self._agent_costs[role] = {"cost_usd": 0.0, "tokens": 0}

            except Exception as e:
                errors.append(f"Agent {role} error: {e}")
                agent_findings[role] = []
                self._agent_costs[role] = {"cost_usd": 0.0, "tokens": 0}

        return agent_findings, self._agent_costs

    def _build_context(self, task: ReviewTask) -> str:
        """Build context string for agents (repo info, diff, etc.)."""
        # In production, this would fetch git diff, file contents, etc.
        files_str = ", ".join(task.target_files) if task.target_files else "All changed files"
        context_parts = [
            f"Review Task: {task.task_id}",
            f"Target Commit: {task.target_commit}",
            f"Review Type: {task.review_type}",
            f"Target Files: {files_str}",
        ]
        return "\n".join(context_parts)

    def _build_consensus(
        self,
        task: ReviewTask,
        agent_findings: dict[str, list],
        tech_verification: TechnicalVerification,
        errors: list[str],
    ) -> Consensus:
        """Build consensus using Judge agent + Technical Verification."""
        # Flatten all findings
        all_findings = []
        for findings in agent_findings.values():
            all_findings.extend(findings)

        # Use ConsensusBuilder (which applies Technical > Model priority)
        consensus = self.consensus_builder.build(
            task=task,
            model_findings=all_findings,
            technical_verification=tech_verification,
        )

        # If Judge agent enabled, could run it for additional synthesis
        # For now, ConsensusBuilder handles the core logic

        return consensus
