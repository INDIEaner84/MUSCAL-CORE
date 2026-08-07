"""Evidence for a single change.

„Jede Änderung benötigt: Quelle, Timestamp, Event-Referenz, Hash,
Vergleichsergebnis."
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional


@dataclass
class ChangeEvidence:
    """Vollständiger Nachweis für eine Drift-Änderung."""

    source: str = "runtime"
    timestamp: Optional[float] = None
    event_reference: str = ""
    event_hash: str = ""
    comparison_result: Optional[dict] = None
    details: Optional[Dict] = None

    def is_complete(self) -> bool:
        """Evidence-Level: alle Pflichtfelder gefüllt."""
        if not self.source:
            return False
        if not self.timestamp:
            return False
        if not self.event_reference and not self.event_hash:
            return False
        return True

    def to_dict(self) -> Dict[str, Any]:
        row = {
            "source": self.source,
            "timestamp": self.timestamp,
            "event_reference": self.event_reference,
            "event_hash": self.event_hash,
            "comparison_result": self.comparison_result or {},
        }
        if self.details:
            row["details"] = self.details
        return {"change_evidence": row}


__all__ = ["ChangeEvidence"]