from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Optional

from .models import InterfaceRequest, InterfaceResponse, VerificationState


class InterfaceAudit:

    def __init__(self):
        self._events: list[dict] = []

    def record_requested(self, request: InterfaceRequest) -> None:
        self._events.append({
            "event": "interface.requested",
            "interface": request.interface,
            "action": request.action,
            "request_id": request.request_id,
            "session_id": request.session_id,
            "execution_id": request.execution_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })

    def record_approved(self, request: InterfaceRequest) -> None:
        self._events.append({
            "event": "interface.approved",
            "interface": request.interface,
            "action": request.action,
            "request_id": request.request_id,
            "session_id": request.session_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })

    def record_denied(self, request: InterfaceRequest, reason: str) -> None:
        self._events.append({
            "event": "interface.denied",
            "interface": request.interface,
            "action": request.action,
            "request_id": request.request_id,
            "reason": reason,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })

    def record_executed(self, request: InterfaceRequest, response: InterfaceResponse) -> None:
        self._events.append({
            "event": "interface.executed",
            "interface": request.interface,
            "action": request.action,
            "request_id": request.request_id,
            "success": response.success,
            "duration": response.duration,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })

    def record_failed(self, request: InterfaceRequest, error: str, duration: float = 0.0) -> None:
        self._events.append({
            "event": "interface.failed",
            "interface": request.interface,
            "action": request.action,
            "request_id": request.request_id,
            "error": error,
            "duration": duration,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })

    def record_verified(self, request: InterfaceRequest, response: InterfaceResponse) -> None:
        self._events.append({
            "event": "interface.verified",
            "interface": request.interface,
            "action": request.action,
            "request_id": request.request_id,
            "verification_state": response.verification_state.value if hasattr(response.verification_state, 'value') else str(response.verification_state),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })

    def get_history(self, interface: Optional[str] = None) -> list[dict]:
        if interface:
            return [e for e in self._events if e.get("interface") == interface]
        return list(self._events)

    def clear(self) -> None:
        self._events.clear()
