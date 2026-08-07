"""Proposal Engine — erzeugt ``UpdateProposal``.

WICHTIG: erzeugt NUR einen Vorschlag. Kein automatisches Schreiben auf den
EventStore, keine Mutation von Runtime- oder Canonical-State. Damit bleibt
„Runtime Reality darf nicht ungeprüft Knowledge Reality verändern"
strukturell gewahrt.
"""

from __future__ import annotations

from typing import Dict, List, Optional, Any

from .models.drift import DriftReport, RiskLevel
from .models.evidence import ChangeEvidence
from .models.proposal import UpdateProposal
from .risk_classifier import RiskClassifier


class ProposalEngine:
    """Übersetzt einen Drift-Report in einen kanonischen Update-Vorschlag."""

    def __init__(self, classifier: Optional[RiskClassifier] = None):
        self._classifier = classifier or RiskClassifier()

    def build(
        self,
        report: DriftReport,
        change_type: str = "state.sync",
        event_reference: str = "",
        evidence_override: Optional[Dict[str, Any]] = None,
    ) -> UpdateProposal:
        """Leitet aus dem Drift-Report einen Proposal ab.

        - ``approval_required`` wird automatisch aus dem Risiko gesetzt
          (HIGH -> True; LOW/MEDIUM -> False im default).
        - ``affected_objects`` = alle betroffenen Objekt-IDs aus dem Report.
        """
        if not report.has_drift and not report.differences:
            risk = RiskLevel.LOW
        else:
            risk = report.risk_level or self._classifier.classify_report(report.differences)

        affected: list[str] = []
        for d in report.differences:
            oid = d.object_id
            if oid and oid not in affected:
                affected.append(oid)

        evidence = self._build_evidence(report, event_reference, evidence_override)
        approval_required = self._classifier.risk_requires_approval(risk)

        return UpdateProposal(
            change_type=change_type,
            affected_objects=affected,
            evidence=evidence,
            approval_required=approval_required,
            risk_level=risk,
        )

    def _build_evidence(
        self,
        report: DriftReport,
        event_reference: str,
        override: Optional[Dict[str, Any]],
    ) -> list[ChangeEvidence]:
        if override is not None:
            return [
                ChangeEvidence(
                    source=override.get("source", report.source),
                    timestamp=override.get("timestamp", report.timestamp),
                    event_reference=override.get("event_reference", event_reference),
                    event_hash=override.get("event_hash", ""),
                    comparison_result=override.get("comparison_result"),
                )
            ]
        return [
            ChangeEvidence(
                source=report.source,
                timestamp=report.timestamp,
                event_reference=event_reference,
                event_hash=self._report_hash(report),
                comparison_result={
                    "difference_count": len(report.differences),
                    "risk_level": report.risk_level.value if report.risk_level else "LOW",
                },
            )
        ]

    @staticmethod
    def _report_hash(report: DriftReport) -> str:
        import hashlib
        import json

        content = json.dumps(
            {
                "id": report.id,
                "source": report.source,
                "target": report.target,
                "differences": [d.to_dict() for d in report.differences],
            },
            sort_keys=True,
            default=str,
        )
        return hashlib.sha256(content.encode()).hexdigest()


__all__ = ["ProposalEngine"]