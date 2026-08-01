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


@dataclass
class ToolCapability:
    name: str
    description: str

    def to_dict(self) -> dict:
        return {"tool_capability": {"name": self.name, "description": self.description}}


@dataclass
class ToolDefinition:
    tool_id: str
    name: str
    category: str
    capabilities: list[ToolCapability]
    risk_level: str
    required_autonomy: str
    requires_confirmation: bool
    provider: str

    def to_dict(self) -> dict:
        return {
            "tool_definition": {
                "tool_id": self.tool_id,
                "name": self.name,
                "category": self.category,
                "capabilities": [c.to_dict() for c in self.capabilities],
                "risk_level": self.risk_level,
                "required_autonomy": self.required_autonomy,
                "requires_confirmation": self.requires_confirmation,
                "provider": self.provider,
            }
        }


@dataclass
class ApprovalRequest:
    request_id: str
    tool_id: str
    action: str
    risk: str
    reason: str
    requested_by: str
    state: ApprovalState = ApprovalState.PENDING
    created_at: str = ""
    decided_at: str = ""

    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now(timezone.utc).isoformat()

    def to_dict(self) -> dict:
        return {
            "approval_request": {
                "request_id": self.request_id,
                "tool_id": self.tool_id,
                "action": self.action,
                "risk": self.risk,
                "reason": self.reason,
                "requested_by": self.requested_by,
                "state": self.state.value,
                "created_at": self.created_at,
                "decided_at": self.decided_at,
            }
        }


@dataclass
class ToolResult:
    tool_id: str
    action: str
    success: bool
    output: Any = None
    error: str = ""
    duration: float = 0.0

    def to_dict(self) -> dict:
        return {
            "tool_result": {
                "tool_id": self.tool_id,
                "action": self.action,
                "success": self.success,
                "output": self.output,
                "error": self.error,
                "duration": self.duration,
            }
        }
