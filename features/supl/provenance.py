from __future__ import annotations
import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from features.supl.semantic_model import InteractionSource, InteractionStatus


_VALID_TRANSITIONS: Dict[InteractionStatus, List[InteractionStatus]] = {
    InteractionStatus.REQUESTED: [
        InteractionStatus.AUTHORIZED,
        InteractionStatus.REJECTED,
        InteractionStatus.FAILED,
    ],
    InteractionStatus.AUTHORIZED: [
        InteractionStatus.EXECUTING,
        InteractionStatus.REJECTED,
        InteractionStatus.FAILED,
    ],
    InteractionStatus.REJECTED: [],
    InteractionStatus.EXECUTING: [
        InteractionStatus.EXECUTED,
        InteractionStatus.FAILED,
    ],
    InteractionStatus.EXECUTED: [
        InteractionStatus.VERIFIED,
        InteractionStatus.FAILED,
    ],
    InteractionStatus.VERIFIED: [],
    InteractionStatus.FAILED: [],
    InteractionStatus.UNKNOWN: [
        InteractionStatus.REQUESTED,
        InteractionStatus.FAILED,
    ],
}


@dataclass
class UIInteraction:
    interaction_id: str
    ui_session_id: str = ""
    projection_id: str = ""
    application_id: str = ""
    action_id: str = ""
    capability_id: str = ""
    source_mode: InteractionSource = InteractionSource.OVERLAY
    created_at: float = field(default_factory=time.time)
    status: InteractionStatus = InteractionStatus.REQUESTED
    execution_id: Optional[str] = None
    receipt_id: Optional[str] = None
    verification_id: Optional[str] = None

    def validate(self) -> List[str]:
        errors = []
        if not self.interaction_id:
            errors.append("interaction_id is required")
        return errors

    def _transition(self, new_status: InteractionStatus) -> None:
        allowed = _VALID_TRANSITIONS.get(self.status, [])
        if new_status not in allowed:
            raise InvalidInteractionTransition(
                f"cannot transition from {self.status.value} to {new_status.value}"
            )
        self.status = new_status

    def mark_authorized(self) -> None:
        self._transition(InteractionStatus.AUTHORIZED)

    def mark_rejected(self, reason: str = "") -> None:
        self._transition(InteractionStatus.REJECTED)

    def mark_executing(self) -> None:
        self._transition(InteractionStatus.EXECUTING)

    def link_execution(self, execution_id: str) -> None:
        self._transition(InteractionStatus.EXECUTED)
        self.execution_id = execution_id

    def link_receipt(self, receipt_id: str) -> None:
        if self.status not in (InteractionStatus.EXECUTED, InteractionStatus.VERIFIED):
            raise InvalidInteractionTransition(
                f"cannot link receipt in status {self.status.value}"
            )
        self.receipt_id = receipt_id

    def mark_verified(self, verification_id: str) -> None:
        self._transition(InteractionStatus.VERIFIED)
        self.verification_id = verification_id

    def mark_failed(self) -> None:
        self._transition(InteractionStatus.FAILED)

    @staticmethod
    def create(
        application_id: str = "",
        action_id: str = "",
        capability_id: str = "",
        source_mode: InteractionSource = InteractionSource.OVERLAY,
        ui_session_id: str = "",
        projection_id: str = "",
    ) -> "UIInteraction":
        return UIInteraction(
            interaction_id=str(uuid.uuid4()),
            ui_session_id=ui_session_id,
            projection_id=projection_id,
            application_id=application_id,
            action_id=action_id,
            capability_id=capability_id,
            source_mode=source_mode,
            created_at=time.time(),
            status=InteractionStatus.REQUESTED,
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "interaction_id": self.interaction_id,
            "ui_session_id": self.ui_session_id,
            "projection_id": self.projection_id,
            "application_id": self.application_id,
            "action_id": self.action_id,
            "capability_id": self.capability_id,
            "source_mode": self.source_mode.value,
            "created_at": self.created_at,
            "status": self.status.value,
            "execution_id": self.execution_id,
            "receipt_id": self.receipt_id,
            "verification_id": self.verification_id,
        }

    @staticmethod
    def from_dict(d: Dict[str, Any]) -> "UIInteraction":
        return UIInteraction(
            interaction_id=d["interaction_id"],
            ui_session_id=d.get("ui_session_id", ""),
            projection_id=d.get("projection_id", ""),
            application_id=d.get("application_id", ""),
            action_id=d.get("action_id", ""),
            capability_id=d.get("capability_id", ""),
            source_mode=InteractionSource(d.get("source_mode", "overlay")),
            created_at=d.get("created_at", time.time()),
            status=InteractionStatus(d.get("status", "requested")),
            execution_id=d.get("execution_id"),
            receipt_id=d.get("receipt_id"),
            verification_id=d.get("verification_id"),
        )

    def provenance_chain(self) -> Dict[str, Optional[str]]:
        return {
            "interaction_id": self.interaction_id,
            "execution_id": self.execution_id,
            "receipt_id": self.receipt_id,
            "verification_id": self.verification_id,
        }

    def chain_is_complete(self) -> bool:
        return all([self.interaction_id, self.execution_id, self.receipt_id, self.verification_id])


class InvalidInteractionTransition(Exception):
    pass
