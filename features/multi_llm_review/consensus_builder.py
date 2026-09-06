"""
Consensus Builder - Baut Konsens aus Model Consensus + Technical Verification.

Kernregel: Technical Verification > Model Consensus bei Widersprüchen.
"""

from features.multi_llm_review.review_schemas import (
    Consensus,
    ReviewFinding,
    ReviewTask,
    TechnicalVerification,
)


class ConsensusBuilder:
    """Bewertet Konsens aus LLM-Befunden und technischer Verifikation."""

    def build(
        self,
        task: ReviewTask,
        model_findings: list[ReviewFinding],
        technical_verification: TechnicalVerification | None,
    ) -> Consensus:
        """Baut Consensus mit Evidence-Priorisierung."""

        # Technische Verifikation hat Vorrang
        tech_verification = technical_verification or TechnicalVerification(
            review_task_id=task.task_id,
            tests_passed=True,
            tests_total=0,
        )

        # Status basierend auf Evidence-Hierarchie bestimmen
        status = self._determine_status(model_findings, tech_verification)

        # Confidence berechnen
        confidence = self._calculate_confidence(model_findings, tech_verification)

        # Dissent extrahieren
        dissent = self._extract_dissent(model_findings)

        # Empfohlene Aktionen
        recommended_actions = self._recommend_actions(
            status, model_findings, tech_verification
        )

        return Consensus(
            review_task_id=task.task_id,
            model_findings=model_findings,
            technical_verification=tech_verification,
            status=status,
            confidence=confidence,
            dissent=dissent,
            recommended_actions=recommended_actions,
        )

    def _determine_status(
        self, model_findings: list[ReviewFinding], tech_verification: TechnicalVerification
    ) -> str:
        """Bestimmt Consensus-Status basierend auf Evidence-Hierarchie."""

        # Keine Findings
        if not model_findings:
            return "UNVERIFIED"

        # Technische Verifikation schlägt fehl -> CONTRADICTION
        if not tech_verification.tests_passed:
            return "CONTRADICTION"

        # Alle Findings high confidence + technisch OK -> VERIFIED
        high_confidence = all(f.confidence > 0.7 for f in model_findings)
        if high_confidence:
            return "VERIFIED"

        # Gemischte Confidence -> PARTIALLY
        return "PARTIALLY"

    def _calculate_confidence(
        self, model_findings: list[ReviewFinding], tech_verification: TechnicalVerification
    ) -> float:
        """Berechnet gewichteten Confidence-Score."""

        if not model_findings:
            return 0.0

        # Technical Verification Weight: 2x
        tech_weight = 2.0
        tech_confidence = 1.0 if tech_verification.tests_passed else 0.0

        # Gewichteter Durchschnitt
        total_weight = len(model_findings) + tech_weight
        weighted_sum = sum(f.confidence for f in model_findings) + (tech_confidence * tech_weight)

        return round(weighted_sum / total_weight, 3)

    def _extract_dissent(self, model_findings: list[ReviewFinding]) -> list[str]:
        """Extrahiert Widersprüche zwischen Findings."""
        dissent = []

        # Confidence-Spread
        if len(model_findings) > 1:
            confidences = [f.confidence for f in model_findings]
            spread = max(confidences) - min(confidences)
            if spread > 0.3:
                dissent.append(f"High confidence spread: {spread:.2f}")

        # Schweregrade
        severities = [f.severity for f in model_findings]
        if "critical" in severities and "low" in severities:
            dissent.append("Severity conflict: critical vs low findings")

        # Finding-Types
        types = [f.finding_type for f in model_findings]
        if len(set(types)) > 2:
            dissent.append(f"Diverse finding types: {', '.join(set(types))}")

        return dissent

    def _recommend_actions(
        self,
        status: str,
        model_findings: list[ReviewFinding],
        tech_verification: TechnicalVerification,
    ) -> list[str]:
        """Empfiehlt nächste Schritte basierend auf Status."""
        actions = []

        if status == "CONTRADICTION":
            actions.append("Fix failing tests before proceeding")
            actions.append("Investigate technical verification failures")
            if tech_verification.findings:
                actions.extend(tech_verification.findings[:3])

        elif status == "UNVERIFIED":
            actions.append("Run model review agents to generate findings")
            actions.append("Ensure review task has sufficient context")

        elif status == "PARTIALLY":
            actions.append("Address low-confidence findings")
            actions.append("Request additional model review for disputed areas")
            critical_findings = [f for f in model_findings if f.severity == "critical"]
            if critical_findings:
                actions.append(f"Prioritize {len(critical_findings)} critical findings")

        elif status == "VERIFIED":
            actions.append("No blocking issues found")
            actions.append("Proceed with integration")

        # Allgemeine Empfehlungen
        if tech_verification.coverage_pct < 80:
            pct = tech_verification.coverage_pct
            actions.append(f"Improve test coverage (current: {pct:.1f}%)")

        return actions[:5]  # Max 5 Aktionen
