"""Risk Classifier — klassifiziert Drift-Änderungen als LOW/MEDIUM/HIGH.

Regeln:
    LOW    — Metriken, Statistiken
    MEDIUM – Dokumentstatus, Featurestatus
    HIGH   – Architektur, Security, Datenmodell
"""

from __future__ import annotations

from typing import Iterable, List

from .models.drift import DriftDifference, RiskLevel

# Keypath-Kennungen -> Risikostufe
_HIGH_KEYWORDS = (
    "architecture",
    "security",
    "data_model",
    "schema",
    "auth",
    "authorization",
    "encryption",
    "permission",
    "role",
    "threat",
)
_MEDIUM_KEYWORDS = (
    "document_status",
    "feature_status",
    "status",
    "version",
    "release",
)
_LOW_KEYWORDS = (
    "metrics",
    "statistics",
    "stats",
    "counter",
    "metric",
    "latency",
)


class RiskClassifier:
    """Bestimmt das Risiko eines einzelnen Drifts und des Reports."""

    def classify_keypath(self, keypath: str) -> RiskLevel:
        lower = keypath.lower()
        for kw in _HIGH_KEYWORDS:
            if kw in lower:
                return RiskLevel.HIGH
        for kw in _MEDIUM_KEYWORDS:
            if kw in lower:
                return RiskLevel.MEDIUM
        for kw in _LOW_KEYWORDS:
            if kw in lower:
                return RiskLevel.LOW
        return RiskLevel.MEDIUM if lower else RiskLevel.LOW

    def classify(self, difference: DriftDifference) -> RiskLevel:
        return self.classify_keypath(difference.keypath)

    def classify_report(self, differences: Iterable[DriftDifference]) -> RiskLevel:
        """Report-Risiko = Maximum der Einzeldiffs."""
        if not differences:
            return RiskLevel.LOW
        levels = {self.classify(d) for d in differences}
        if RiskLevel.HIGH in levels:
            return RiskLevel.HIGH
        if RiskLevel.MEDIUM in levels:
            return RiskLevel.MEDIUM
        return RiskLevel.LOW

    def risk_requires_approval(self, level: RiskLevel) -> bool:
        """HIGH -> approval erforderlich."""
        return level == RiskLevel.HIGH


__all__ = ["RiskClassifier", "RiskLevel"]