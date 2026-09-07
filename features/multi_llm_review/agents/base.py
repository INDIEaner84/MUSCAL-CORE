"""
Base Review Agent - Common functionality for all review agents.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from uuid import uuid4

from features.llm_provider import LLMProviderRegistry, TaskFit, llm_provider_registry
from features.multi_llm_review.review_schemas import ReviewFinding, ReviewTask
from features.provenance.evaluation import EvidenceRef


@dataclass
class AgentConfig:
    """Configuration for a review agent."""
    role: str
    provider_id: str | None = None
    model: str | None = None
    temperature: float = 0.0
    max_tokens: int | None = None
    system_prompt: str = ""


class BaseReviewAgent(ABC):
    """Base class for all review agents."""

    def __init__(
        self,
        config: AgentConfig,
        provider_registry: LLMProviderRegistry | None = None,
    ):
        self.config = config
        self.provider_registry = provider_registry or llm_provider_registry
        self._provider = None

    @property
    def role(self) -> str:
        return self.config.role

    @property
    def provider(self):
        """Lazy-load provider from registry."""
        if self._provider is None:
            provider_id = self.config.provider_id
            task_fit = TaskFit(preferred_provider=provider_id) if provider_id else None
            self._provider = self.provider_registry.resolve(self.role, task_fit)
        return self._provider

    @abstractmethod
    def get_system_prompt(self) -> str:
        """Return the system prompt for this agent."""
        pass

    @abstractmethod
    def get_analysis_prompt(self, task: ReviewTask, context: str) -> str:
        """Return the analysis prompt for this agent."""
        pass

    def analyze(self, task: ReviewTask, context: str) -> list[ReviewFinding]:
        """Execute review analysis using the LLM provider."""
        system_prompt = self.get_system_prompt()
        analysis_prompt = self.get_analysis_prompt(task, context)

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": analysis_prompt},
        ]

        # Structured output schema for ReviewFinding
        output_schema: dict = {
            "type": "object",
            "properties": {
                "findings": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "finding_type": {"type": "string"},
                            "severity": {
                                "type": "string",
                                "enum": ["critical", "high", "medium", "low", "info"],
                            },
                            "confidence": {
                                "type": "number",
                                "minimum": 0.0,
                                "maximum": 1.0,
                            },
                            "claim": {"type": "string"},
                            "evidence_refs": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "source_id": {"type": "string"},
                                        "relation_type": {"type": "string"},
                                        "status": {"type": "string"},
                                        "evidence_source": {"type": "string"},
                                        "reason": {"type": "string"},
                                    },
                                    "required": [
                                        "source_id",
                                        "relation_type",
                                        "status",
                                        "evidence_source",
                                        "reason",
                                    ],
                                },
                            },
                            "file_refs": {"type": "array", "items": {"type": "string"}},
                        },
                        "required": [
                            "finding_type",
                            "severity",
                            "confidence",
                            "claim",
                            "evidence_refs",
                            "file_refs",
                        ],
                    },
                },
            },
            "required": ["findings"],
        }

        result = self.provider.chat(
            messages=messages,
            temperature=self.config.temperature,
            max_tokens=self.config.max_tokens,
            structured_output_schema=output_schema,
        )

        # Store cost info for tracking
        self.last_cost_info = {
            "cost_usd": result.get("cost_usd", 0.0),
            "tokens": result.get("tokens", 0),
        }

        return self._parse_findings(result, task)

    def _parse_findings(self, result: dict, task: ReviewTask) -> list:
        """Parse LLM result into ReviewFinding objects."""
        findings = []

        raw_findings = result.get("findings", [])
        for f in raw_findings:
            evidence_refs = []
            for e in f.get("evidence_refs", []):
                evidence_refs.append(EvidenceRef(
                    source_id=e.get("source_id", ""),
                    relation_type=e.get("relation_type", "CONTAINS"),
                    status=e.get("status", "INFERRED"),
                    evidence_source=e.get("evidence_source", "llm_analysis"),
                    reason=e.get("reason", ""),
                ))

            finding = ReviewFinding(
                finding_id=str(uuid4()),
                review_task_id=task.task_id,
                finding_type=f.get("finding_type", "quality"),
                severity=f.get("severity", "medium"),
                confidence=float(f.get("confidence", 0.5)),
                claim=f.get("claim", ""),
                evidence=evidence_refs,
                file_refs=f.get("file_refs", []),
            )
            findings.append(finding)

        return findings
