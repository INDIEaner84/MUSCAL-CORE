"""
Review Schemas for Multi-LLM Evidence Architecture.

Extends existing EvaluationClaim and EvidenceRef from features.provenance.evaluation
instead of duplicating them.
"""

import time
from dataclasses import dataclass, field
from typing import Any
from uuid import uuid4

from features.provenance.evaluation import EvaluationClaim, EvidenceRef
from features.provenance.models import EvidenceStatus


@dataclass
class ReviewTask:
    """Was soll reviewt werden."""

    task_id: str = field(default_factory=lambda: str(uuid4()))
    target_commit: str = ""
    target_files: list[str] = field(default_factory=list)
    review_type: str = "full"
    created_at: float = field(default_factory=time.time)

    def to_dict(self) -> dict[str, Any]:
        return {
            "task_id": self.task_id,
            "target_commit": self.target_commit,
            "target_files": self.target_files,
            "review_type": self.review_type,
            "created_at": self.created_at,
        }


@dataclass
class ReviewFinding:
    """Einzelner Review-Befund (strukturiert)."""

    finding_id: str = field(default_factory=lambda: str(uuid4()))
    review_task_id: str = ""
    finding_type: str = "quality"
    severity: str = "medium"
    confidence: float = 0.5
    claim: str = ""
    evidence: list[EvidenceRef] = field(default_factory=list)
    file_refs: list[str] = field(default_factory=list)
    created_at: float = field(default_factory=time.time)

    def to_dict(self) -> dict[str, Any]:
        return {
            "finding_id": self.finding_id,
            "review_task_id": self.review_task_id,
            "finding_type": self.finding_type,
            "severity": self.severity,
            "confidence": self.confidence,
            "claim": self.claim,
            "evidence": [e.to_dict() for e in self.evidence],
            "file_refs": self.file_refs,
            "created_at": self.created_at,
        }

    def to_evaluation_claim(self) -> EvaluationClaim:
        """Konvertiert zu bestehendem EvaluationClaim."""
        return EvaluationClaim(
            claim_id=self.finding_id,
            target_id=self.review_task_id,
            criterion=self.finding_type,
            conclusion=self.claim,
            evidence=self.evidence,
            evidence_status=EvidenceStatus.INFERRED.value,
            rationale=f"Severity: {self.severity}, Confidence: {self.confidence}",
            uncertainty="",
            conflicts=[],
        )


@dataclass
class TechnicalVerification:
    """Deterministische Verifikation (stark)."""

    verification_id: str = field(default_factory=lambda: str(uuid4()))
    review_task_id: str = ""
    tests_passed: bool = False
    tests_total: int = 0
    tests_failed: int = 0
    tests_skipped: int = 0
    coverage_pct: float = 0.0
    static_analysis: dict[str, Any] = field(default_factory=dict)
    import_checks: dict[str, Any] = field(default_factory=dict)
    findings: list[str] = field(default_factory=list)
    created_at: float = field(default_factory=time.time)

    def to_dict(self) -> dict[str, Any]:
        return {
            "verification_id": self.verification_id,
            "review_task_id": self.review_task_id,
            "tests_passed": self.tests_passed,
            "tests_total": self.tests_total,
            "tests_failed": self.tests_failed,
            "tests_skipped": self.tests_skipped,
            "coverage_pct": self.coverage_pct,
            "static_analysis": self.static_analysis,
            "import_checks": self.import_checks,
            "findings": self.findings,
            "created_at": self.created_at,
        }


@dataclass
class Consensus:
    """Bewerteter Konsens aus Model Consensus + Technical Verification."""

    consensus_id: str = field(default_factory=lambda: str(uuid4()))
    review_task_id: str = ""
    model_findings: list[ReviewFinding] = field(default_factory=list)
    technical_verification: TechnicalVerification | None = None
    status: str = "UNVERIFIED"
    confidence: float = 0.0
    dissent: list[str] = field(default_factory=list)
    recommended_actions: list[str] = field(default_factory=list)
    created_at: float = field(default_factory=time.time)

    def to_dict(self) -> dict[str, Any]:
        tech_ver = self.technical_verification
        tv_dict = tech_ver.to_dict() if tech_ver else None
        return {
            "consensus_id": self.consensus_id,
            "review_task_id": self.review_task_id,
            "model_findings": [f.to_dict() for f in self.model_findings],
            "technical_verification": tv_dict,
            "status": self.status,
            "confidence": self.confidence,
            "dissent": self.dissent,
            "recommended_actions": self.recommended_actions,
            "created_at": self.created_at,
        }
