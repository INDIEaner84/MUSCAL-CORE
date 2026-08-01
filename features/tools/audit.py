from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Optional

from .models import ApprovalRequest, ApprovalState, ToolResult


class ToolAudit:

    def __init__(self):
        self._events: list[dict] = []

    def record_request(self, tool_id: str, action: str) -> None:
        self._events.append({
            "event": "tool.requested",
            "tool_id": tool_id,
            "action": action,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })

    def record_approved(self, tool_id: str, action: str) -> None:
        self._events.append({
            "event": "tool.approved",
            "tool_id": tool_id,
            "action": action,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })

    def record_denied(self, tool_id: str, action: str, reason: str) -> None:
        self._events.append({
            "event": "tool.denied",
            "tool_id": tool_id,
            "action": action,
            "reason": reason,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })

    def record_execution(self, tool_id: str, action: str, result: ToolResult, duration: float) -> None:
        self._events.append({
            "event": "tool.executed",
            "tool_id": tool_id,
            "action": action,
            "success": result.success,
            "duration": duration,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })

    def record_failure(self, tool_id: str, action: str, error: str, duration: float) -> None:
        self._events.append({
            "event": "tool.failed",
            "tool_id": tool_id,
            "action": action,
            "error": error,
            "duration": duration,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })

    def record_approval_created(self, req: ApprovalRequest) -> None:
        self._events.append({
            "event": "tool.approval_created",
            "request_id": req.request_id,
            "tool_id": req.tool_id,
            "action": req.action,
            "state": req.state.value,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })

    def get_history(self, tool_id: Optional[str] = None) -> list[dict]:
        if tool_id:
            return [e for e in self._events if e.get("tool_id") == tool_id]
        return list(self._events)

    def clear(self) -> None:
        self._events.clear()
