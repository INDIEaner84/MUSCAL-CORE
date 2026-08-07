"""Canonical update proposal — nur Vorschlag, KEIN automatisches Schreiben.

Proposal trägt die geforderten Felder: proposal_id, change_type,
affected_objects, evidence, approval_required.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from .drift import RiskLevel
from .evidence import ChangeEvidence


@dataclass
class UpdateProposal:
    proposal_id: str = ""
    change_type: str = ""            # z. B. "state_propagation", "knowledge_update"
    affected_objects: List[str] = field(default_factory=list)
    evidence: List[ChangeEvidence] = field(default_factory=list)
    approval_required: bool = False
    risk_level: RiskLevel = RiskLevel.LOW
    status: str = "PENDING"
    reason: str = ""

    def __post_init__(self):
        if not self.proposal_id:
            self.proposal_id = str(uuid.uuid4())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "update_proposal": {
                "proposal_id": self.proposal_id,
                "change_type": self.change_type,
                "affected_objects": list(self.affected_objects),
                "approval_required": self.approval_required,
                "risk_level": self.risk_level.value,
                "status": self.status,
                "reason": self.reason,
                "evidence": [e.to_dict() for e in self.evidence],
            }
        }


__all__ = ["UpdateProposal"]