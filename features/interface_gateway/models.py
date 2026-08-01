from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional


class ApprovalState(str, Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    DENIED = "DENIED"
    EXPIRED = "EXPIRED"


class VerificationState(str, Enum):
    UNVERIFIED = "UNVERIFIED"
    VERIFIED = "VERIFIED"
    FAILED = "FAILED"


@dataclass
class InterfaceCapability:
    name: str
    description: str
    risk_level: str = "low"
    requires_confirmation: bool = False

    def to_dict(self) -> dict:
        return {
            "interface_capability": {
                "name": self.name,
                "description": self.description,
                "risk_level": self.risk_level,
                "requires_confirmation": self.requires_confirmation,
            }
        }


@dataclass
class InterfaceRequest:
    interface: str
    action: str
    params: dict[str, Any]
    session_id: str = ""
    execution_id: str = ""
    correlation_id: str = ""
    request_id: str = ""

    def __post_init__(self):
        if not self.request_id:
            import uuid
            self.request_id = f"if_req_{uuid.uuid4().hex[:12]}"

    def to_dict(self) -> dict:
        return {
            "interface_request": {
                "interface": self.interface,
                "action": self.action,
                "params": self.params,
                "session_id": self.session_id,
                "execution_id": self.execution_id,
                "correlation_id": self.correlation_id,
                "request_id": self.request_id,
            }
        }


@dataclass
class InterfaceResponse:
    request_id: str
    success: bool
    output: Any = None
    error: str = ""
    duration: float = 0.0
    verification_state: VerificationState = VerificationState.UNVERIFIED
    timestamp: str = ""

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now(timezone.utc).isoformat()

    def to_dict(self) -> dict:
        return {
            "interface_response": {
                "request_id": self.request_id,
                "success": self.success,
                "output": self.output,
                "error": self.error,
                "duration": self.duration,
                "verification_state": self.verification_state.value,
                "timestamp": self.timestamp,
            }
        }


@dataclass
class InterfaceSession:
    session_id: str
    interface: str
    created_at: str = ""
    approval_state: ApprovalState = ApprovalState.PENDING
    provenance: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now(timezone.utc).isoformat()

    def to_dict(self) -> dict:
        return {
            "interface_session": {
                "session_id": self.session_id,
                "interface": self.interface,
                "created_at": self.created_at,
                "approval_state": self.approval_state.value,
                "provenance": self.provenance,
                "metadata": self.metadata,
            }
        }
