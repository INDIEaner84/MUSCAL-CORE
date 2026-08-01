from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Optional

from features.verification.verifier import Verifier, VerificationResult
from features.verification.orchestrator import VerificationOrchestrator
from features.verification.rules import HardRuleViolation, RuleEngine


_CATEGORY_TO_ATTR = {
    "fact": "facts",
    "observation": "observations",
    "verification_finding": "verification_findings",
    "risk": "risks",
    "recommendation": "recommendations",
}

VERIFICATION_EVIDENCE_CATEGORIES = frozenset(_CATEGORY_TO_ATTR.keys())


@dataclass
class BridgeVerificationFinding:
    category: str
    statement: str
    evidence: str
    source: str
    severity: str = "info"

    def validate(self) -> None:
        if self.category not in VERIFICATION_EVIDENCE_CATEGORIES:
            raise ValueError(
                f"Invalid category '{self.category}'. "
                f"Must be one of: {sorted(VERIFICATION_EVIDENCE_CATEGORIES)}"
            )


@dataclass
class BridgeVerificationReport:
    status: str
    facts: list[BridgeVerificationFinding] = field(default_factory=list)
    observations: list[BridgeVerificationFinding] = field(default_factory=list)
    verification_findings: list[BridgeVerificationFinding] = field(default_factory=list)
    risks: list[BridgeVerificationFinding] = field(default_factory=list)
    recommendations: list[BridgeVerificationFinding] = field(default_factory=list)
    evidence_missing: list[str] = field(default_factory=list)
    verified_at: str = ""

    def __post_init__(self):
        if not self.verified_at:
            self.verified_at = datetime.now(timezone.utc).isoformat()

    def add_finding(self, finding: BridgeVerificationFinding) -> None:
        finding.validate()
        attr = _CATEGORY_TO_ATTR.get(finding.category)
        if attr is None:
            self.observations.append(finding)
        else:
            target = getattr(self, attr)
            target.append(finding)

    def to_dict(self) -> dict:
        def f_item(f: BridgeVerificationFinding) -> dict:
            return {
                "statement": f.statement,
                "evidence": f.evidence,
                "source": f.source,
                "severity": f.severity,
            }
        return {
            "verification": {
                "status": self.status,
                "facts": [f_item(f) for f in self.facts],
                "observations": [f_item(f) for f in self.observations],
                "verification_findings": [f_item(f) for f in self.verification_findings],
                "risks": [f_item(f) for f in self.risks],
                "recommendations": [f_item(f) for f in self.recommendations],
                "evidence_missing": self.evidence_missing,
                "verified_at": self.verified_at,
            }
        }


class BridgeVerifier:

    def __init__(self, orchestrator: Optional[VerificationOrchestrator] = None):
        self._orchestrator = orchestrator or VerificationOrchestrator(
            rule_engine=RuleEngine(),
        )

    def verify_bridge_result(
        self,
        result: dict,
        expected: Optional[dict] = None,
    ) -> BridgeVerificationReport:
        report = BridgeVerificationReport(status="pending")

        self._verify_return_code(result, report)
        self._verify_evidence_presence(result, report)
        self._verify_duration(result, report)
        self._verify_session_reference(result, report)
        if expected:
            self._verify_expected_state(result, expected, report)

        if not report.verification_findings:
            report.status = "passed"
            report.add_finding(BridgeVerificationFinding(
                category="verification_finding",
                statement="All bridge execution checks passed",
                evidence="No failed checks detected",
                source="bridge_verifier",
            ))
            report.add_finding(BridgeVerificationFinding(
                category="recommendation",
                statement="Execution result is ready for downstream processing",
                evidence="All verification criteria satisfied",
                source="bridge_verifier",
            ))
        else:
            report.status = "failed"
            report.add_finding(BridgeVerificationFinding(
                category="recommendation",
                statement="Review failed checks before using execution result",
                evidence=f"{len(report.verification_findings)} checks failed",
                source="bridge_verifier",
                severity="high",
            ))

        return report

    def _verify_return_code(
        self, result: dict, report: BridgeVerificationReport
    ) -> None:
        rc = result.get("execution", {}).get("return_code")
        if rc is None:
            report.evidence_missing.append("execution.return_code")
            report.add_finding(BridgeVerificationFinding(
                category="verification_finding",
                statement="Return code missing — cannot verify execution completion",
                evidence="No return_code field in execution info",
                source="bridge_verifier",
                severity="high",
            ))
        elif rc != 0:
            report.add_finding(BridgeVerificationFinding(
                category="verification_finding",
                statement=f"Execution failed with return code {rc}",
                evidence=f"return_code={rc}",
                source="bridge_verifier",
                severity="high",
            ))
        else:
            report.add_finding(BridgeVerificationFinding(
                category="fact",
                statement=f"Execution completed with exit code 0",
                evidence=f"return_code={rc}",
                source="bridge_verifier",
            ))

    def _verify_evidence_presence(
        self, result: dict, report: BridgeVerificationReport
    ) -> None:
        unknowns = result.get("unknowns", [])
        if unknowns:
            report.add_finding(BridgeVerificationFinding(
                category="observation",
                statement=f"Execution has {len(unknowns)} unknown items",
                evidence=f"unknowns: {unknowns[:3]}",
                source="bridge_verifier",
            ))

        facts = result.get("facts", {}).get("verified", [])
        if not facts:
            report.evidence_missing.append("verified_facts")
            report.add_finding(BridgeVerificationFinding(
                category="verification_finding",
                statement="No verified facts in execution result",
                evidence="facts.verified is empty",
                source="bridge_verifier",
                severity="warning",
            ))

    def _verify_duration(
        self, result: dict, report: BridgeVerificationReport
    ) -> None:
        duration = result.get("execution", {}).get("duration")
        if duration is not None:
            report.add_finding(BridgeVerificationFinding(
                category="observation",
                statement=f"Execution duration: {duration:.2f}s",
                evidence=f"duration={duration}",
                source="bridge_verifier",
            ))
            if duration > 300:
                report.add_finding(BridgeVerificationFinding(
                    category="risk",
                    statement=f"Execution exceeded 5 minutes ({duration:.0f}s)",
                    evidence=f"duration={duration}",
                    source="bridge_verifier",
                    severity="warning",
                ))
        else:
            report.evidence_missing.append("execution.duration")

    def _verify_session_reference(
        self, result: dict, report: BridgeVerificationReport
    ) -> None:
        session = result.get("execution", {}).get("session_reference")
        if session:
            report.add_finding(BridgeVerificationFinding(
                category="fact",
                statement=f"OpenCode session captured: {session}",
                evidence=f"session_reference={session}",
                source="bridge_verifier",
            ))
        else:
            report.evidence_missing.append("execution.session_reference")
            report.add_finding(BridgeVerificationFinding(
                category="observation",
                statement="No OpenCode session reference available",
                evidence="session_reference is null",
                source="bridge_verifier",
            ))

    def _verify_expected_state(
        self, result: dict, expected: dict, report: BridgeVerificationReport
    ) -> None:
        for key, expected_val in expected.items():
            actual = result
            for part in key.split("."):
                actual = actual.get(part, {}) if isinstance(actual, dict) else {}
            if actual != expected_val:
                report.add_finding(BridgeVerificationFinding(
                    category="verification_finding",
                    statement=f"Expected {key}={expected_val}, got {actual}",
                    evidence=f"key={key}, expected={expected_val}, actual={actual}",
                    source="bridge_verifier",
                    severity="high",
                ))
