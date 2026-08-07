"""Drift Detector — vergleicht Runtime State gegen Canonical State.

Erzeugt einen ``DriftReport``. Pure Funktion: keine Seiteneffekte, kein
Schreiben auf den EventStore.
"""

from __future__ import annotations

import hashlib
import json
import time
import uuid
from typing import Any, Dict, List, Optional

from .models.drift import DriftDifference, DriftReport, RiskLevel
from .risk_classifier import RiskClassifier
from .validators.consistency import ConsistencyValidator, InvalidStateError


class DriftDetector:
    """Vergleicht zwei Zustände und beschreibt die Unterschiede.

    - ``runtime_state``: rekonstruierter Zustand (z. B. ``ReconstructedState``
      aus ``features/events/state_model`` oder ein dict).
    - ``canonical_state``: etablierte/erwartete Sicht (z. B. Knowledge/Canonical).

    Ein „Key" ist ein Pfad wie ``entities.node:abc.status`` — dadurch bleibt
    der Vergleich schema-agnostisch und wiederverwendbar.
    """

    def __init__(
        self,
        validator: Optional[ConsistencyValidator] = None,
        classifier: Optional[RiskClassifier] = None,
    ):
        self._validator = validator or ConsistencyValidator()
        self._classifier = classifier or RiskClassifier()

    def detect(self, runtime_state: Any, canonical_state: Any) -> DriftReport:
        """Berechnet den Drift-Report.

        Raises ``InvalidStateError`` wenn einer der beiden Zustände
        nicht konsistent ist (Testfall 7: ungültiger State wird abgelehnt).
        """
        runtime = self._validator.validate(runtime_state)
        canonical = self._validator.validate(canonical_state)

        differences = self._diff(runtime, canonical)
        risk = self._classifier.classify_report(differences)
        has_drift = len(differences) > 0

        return DriftReport(
            id=str(uuid.uuid4()),
            source="runtime",
            target="canonical",
            timestamp=time.time(),
            differences=differences,
            risk_level=risk,
            recommended_action=self._recommended_action(risk, has_drift),
            has_drift=has_drift,
        )

    def _diff(self, runtime: Dict[str, Any], canonical: Dict[str, Any]) -> List[DriftDifference]:
        diffs: List[DriftDifference] = []
        keys = set(runtime) | set(canonical)

        for section in sorted(keys):
            rv = runtime.get(section)
            cv = canonical.get(section)

            if section in ("timestamp", "events_processed", "source", "target"):
                continue

            if isinstance(rv, dict) and isinstance(cv, dict):
                self._diff_dict(section, rv, cv, diffs)
            elif rv != cv:
                diffs.append(
                    DriftDifference(
                        keypath=section,
                        runtime_value=rv,
                        canonical_value=cv,
                        change_type="modified",
                    )
                )
        return diffs

    def _diff_dict(
        self,
        prefix: str,
        runtime: Dict[str, Any],
        canonical: Dict[str, Any],
        out: List[DriftDifference],
    ) -> None:
        keys = set(runtime) | set(canonical)
        for key in sorted(keys):
            keypath = f"{prefix}.{key}"
            rv = runtime.get(key)
            cv = canonical.get(key)

            if isinstance(rv, dict) and isinstance(cv, dict):
                self._diff_dict(keypath, rv, cv, out)
                continue
            if isinstance(rv, list) and isinstance(cv, list):
                if rv != cv:
                    out.append(
                        DriftDifference(
                            keypath=keypath,
                            runtime_value=rv,
                            canonical_value=cv,
                            change_type="modified",
                            object_id=key,
                        )
                    )
                continue

            if rv == cv:
                continue
            change_type = "removed" if rv is None else "added" if cv is None else "modified"
            out.append(
                DriftDifference(
                    keypath=keypath,
                    runtime_value=rv,
                    canonical_value=cv,
                    change_type=change_type,
                    object_id=key,
                )
            )

    @staticmethod
    def _recommended_action(risk: RiskLevel, has_drift: bool) -> str:
        if not has_drift:
            return "no_sync"
        return {
            RiskLevel.LOW: "auto_sync",
            RiskLevel.MEDIUM: "review",
            RiskLevel.HIGH: "require_approval",
        }[risk]

    @staticmethod
    def hash_difference(diff: DriftDifference) -> str:
        """Stabiler Hash über einen einzelnen Drift-Unterschied."""
        canonical = json.dumps(
            {
                "keypath": diff.keypath,
                "change_type": diff.change_type,
                "runtime_value": diff.runtime_value,
                "canonical_value": diff.canonical_value,
            },
            sort_keys=True,
            default=str,
        )
        return hashlib.sha256(canonical.encode()).hexdigest()


__all__ = ["DriftDetector"]