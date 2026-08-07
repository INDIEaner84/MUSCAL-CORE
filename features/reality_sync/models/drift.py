"""Drift report models.

Stellt fest, wo sich der Runtime-State vom Canonical-State unterscheidet.
Keine Annahmen über die konkrete Schema-Darstellung — vergleicht generische
``keypath`` (z. B. ``entities.node:abc.status``).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional

DEFAULT_SOURCE = "runtime"
DEFAULT_TARGET = "canonical"


class RiskLevel(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


@dataclass
class DriftDifference:
    """Ein einzelner Unterschied zwischen Runtime- und Canonical-State."""

    keypath: str
    runtime_value: Any = None
    canonical_value: Any = None
    change_type: str = "modified"
    object_id: str = ""

    def to_dict(self) -> dict:
        return {
            "keypath": self.keypath,
            "object_id": self.object_id,
            "change_type": self.change_type,
            "runtime_value": self.runtime_value,
            "canonical_value": self.canonical_value,
        }


@dataclass
class DriftReport:
    """Ergebnis des Drift-Vergleichs.

    - ``source``/``target``: Namen der verglichenen Zustände.
    - ``differences``: Liste aller Abweichungen.
    - ``risk_level``: aggregierter Risikowert (max der Einzeldiffs).
    """

    id: str
    source: str = "runtime"
    target: str = "canonical"
    timestamp: Optional[float] = None
    differences: List[DriftDifference] = field(default_factory=list)
    risk_level: RiskLevel = RiskLevel.LOW
    recommended_action: str = "no_sync"
    has_drift: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "drift_report": {
                "id": self.id,
                "source": self.source,
                "target": self.target,
                "timestamp": self.timestamp,
                "has_drift": self.has_drift,
                "risk_level": self.risk_level.value,
                "recommended_action": self.recommended_action,
                "difference_count": len(self.differences),
                "differences": [d.to_dict() for d in self.differences],
            }
        }