"""Reality Synchronization Layer (RSL).

Kontrollierte Verbindung zwischen Runtime Events, State Reconstruction,
Reality Evaluation und Canonical Update Proposal.

Keine Core-Änderungen: RSL liest nur den EventStore (replay) und erzeugt
reine Datenobjekte (Report/Proposal); kein automatisches Schreiben.
"""

from .drift_detector import DriftDetector
from .evaluator import RealitySynchronizer, RSL_VERSION
from .models import (
    ChangeEvidence,
    DriftDifference,
    DriftReport,
    RiskLevel,
    UpdateProposal,
)
from .proposal_engine import ProposalEngine
from .risk_classifier import RiskClassifier
from .validators.consistency import ConsistencyValidator, InvalidStateError

__all__ = [
    "RealitySynchronizer",
    "DriftDetector",
    "RiskClassifier",
    "ProposalEngine",
    "ConsistencyValidator",
    "InvalidStateError",
    "DriftReport",
    "DriftDifference",
    "RiskLevel",
    "ChangeEvidence",
    "UpdateProposal",
    "RSL_VERSION",
]