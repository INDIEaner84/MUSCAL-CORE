"""Reality Synchronization Layer — Evaluator (Orchestrierung).

Kontrollierte Verbindung:

    Runtime Events (EventStore v2)
        → State Reconstruction (ReconstructedState)
        → Reality Evaluation (DriftDetector)
        → Canonical Update Proposal (ProposalEngine)

KEIN automatisches Schreiben: Diese Pipeline liefert ausschließlich einen
Vorschlag (UpdateProposal) und ändert weder Runtime- noch Canonical-State.
"""

from __future__ import annotations

from typing import Any, Dict, Optional

from .drift_detector import DriftDetector
from .models.drift import DriftReport
from .models.evidence import ChangeEvidence
from .models.proposal import UpdateProposal
from .proposal_engine import ProposalEngine
from .validators.consistency import ConsistencyValidator, InvalidStateError

# Feature-Version (RSL)
RSL_VERSION = "1.0.0"


class RealitySynchronizer:
    """Führt die RSL-Pipeline aus.

    Typische Verwendung:

        sync = RealitySynchronizer(event_store=store)      # EventStore v2
        result = sync.evaluate(canonical_state=canonical)   # dict oder Objekt

    Wenn ``event_store`` übergeben wird, wird der Runtime-State über
    ``features/events/state_model.reconstruct_from_store`` rekonstruiert
    (bestehende Rekonstruktion; kein eigener Speichermechanismus).
    Andernfalls kann ``runtime_state`` direkt übergeben werden.
    """

    def __init__(
        self,
        event_store: Optional[Any] = None,
        detector: Optional[DriftDetector] = None,
        proposal_engine: Optional[ProposalEngine] = None,
        validator: Optional[ConsistencyValidator] = None,
    ):
        self._event_store = event_store
        self._detector = detector or DriftDetector()
        self._proposals = proposal_engine or ProposalEngine()
        self._validator = validator or ConsistencyValidator()

    @property
    def event_store(self) -> Optional[Any]:
        return self._event_store

    @property
    def detector(self) -> DriftDetector:
        return self._detector

    def reconstruct_runtime_state(self) -> Dict[str, Any]:
        """Rekonstruiert den Runtime-State aus dem EventStore (bestehende API)."""
        if self._event_store is None:
            raise ValueError("Kein event_store konfiguriert")

        from features.events.state_model import reconstruct_from_store

        state = reconstruct_from_store(self._event_store)
        data = state.to_dict()
        data["timestamp"] = state.last_event_hash or 0.0
        return data

    def evaluate(
        self,
        canonical_state: Any,
        runtime_state: Optional[Any] = None,
        change_type: str = "state.sync",
        event_reference: str = "",
    ) -> Dict[str, Any]:
        """Führt Drift-Detection + Proposal-Erstellung aus.

        - ``runtime_state``: optional; wenn None → Rekonstruktion aus dem Store.
        - ``canonical_state``: Pflicht; kann dict oder Objekt mit to_dict sein.

        Returns ein dict:
            {
              "version": RSL_VERSION,
              "runtime_state": <dict>,
              "drift_report": {...},
              "proposal": {...},
            }
        """
        if runtime_state is None:
            if self._event_store is None:
                raise ValueError(
                    "runtime_state erforderlich oder event_store konfigurieren"
                )
            runtime_state = self.reconstruct_runtime_state()

        report = self._detector.detect(runtime_state, canonical_state)
        proposal = self._proposals.build(
            report,
            change_type=change_type,
            event_reference=event_reference,
        )

        return {
            "version": RSL_VERSION,
            "runtime_state": self._as_dict(runtime_state),
            "drift_report": report.to_dict(),
            "proposal": proposal.to_dict(),
        }

    def drift_only(self, runtime_state: Any, canonical_state: Any) -> DriftReport:
        """Nur den Drift-Report berechnen (ohne Proposal)."""
        return self._detector.detect(runtime_state, canonical_state)

    def propose(self, report: DriftReport, change_type: str = "state.sync",
                event_reference: str = "") -> UpdateProposal:
        return self._proposals.build(report, change_type=change_type,
                                     event_reference=event_reference)

    def validate(self, state: Any) -> dict:
        return self._validator.validate(state)

    @staticmethod
    def _as_dict(state: Any) -> Any:
        if hasattr(state, "to_dict") and callable(getattr(state, "to_dict")):
            return state.to_dict()
        return state


__all__ = ["RealitySynchronizer", "RSL_VERSION"]