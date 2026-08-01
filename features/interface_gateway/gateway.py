from __future__ import annotations

import time
import uuid
from typing import Any, Optional

from ..runtime.models import ApprovalPolicy

from .models import InterfaceRequest, InterfaceResponse, InterfaceSession, ApprovalState, VerificationState
from .adapter_registry import AdapterRegistry
from .policy_adapter import InterfacePolicyAdapter
from .audit import InterfaceAudit


class InterfaceGateway:

    def __init__(
        self,
        registry: Optional[AdapterRegistry] = None,
        policy: Optional[InterfacePolicyAdapter] = None,
        audit: Optional[InterfaceAudit] = None,
        autonomy_level: str = "A3",
    ):
        self._registry = registry or AdapterRegistry()
        self._policy = policy or InterfacePolicyAdapter()
        self._audit = audit or InterfaceAudit()
        self._autonomy_level = autonomy_level
        self._sessions: dict[str, InterfaceSession] = {}

    @property
    def registry(self) -> AdapterRegistry:
        return self._registry

    @property
    def audit(self) -> InterfaceAudit:
        return self._audit

    def execute(self, interface: str, action: str, params: Optional[dict] = None,
                session_id: str = "", execution_id: str = "",
                correlation_id: str = "") -> InterfaceResponse:
        request = InterfaceRequest(
            interface=interface,
            action=action,
            params=params or {},
            session_id=session_id or str(uuid.uuid4()),
            execution_id=execution_id,
            correlation_id=correlation_id or str(uuid.uuid4()),
        )
        self._audit.record_requested(request)

        allowed, reason = self._policy.check(f"{interface}.{action}", self._autonomy_level)
        if not allowed:
            self._audit.record_denied(request, reason)
            return InterfaceResponse(
                request_id=request.request_id,
                success=False,
                error=reason,
            )

        adapter = self._registry.get(interface)
        if adapter is None:
            err = f"No adapter registered for interface '{interface}'"
            self._audit.record_failed(request, err)
            return InterfaceResponse(
                request_id=request.request_id,
                success=False,
                error=err,
            )

        if not hasattr(adapter, action):
            err = f"Adapter '{interface}' has no action '{action}'"
            self._audit.record_failed(request, err)
            return InterfaceResponse(
                request_id=request.request_id,
                success=False,
                error=err,
            )

        self._audit.record_approved(request)
        start = time.time()
        try:
            method = getattr(adapter, action)
            result = method(**request.params)
            duration = time.time() - start
            response = InterfaceResponse(
                request_id=request.request_id,
                success=True,
                output=result,
                duration=duration,
                verification_state=VerificationState.VERIFIED,
            )
            self._audit.record_executed(request, response)
            self._audit.record_verified(request, response)
            return response
        except Exception as e:
            duration = time.time() - start
            err = str(e)
            self._audit.record_failed(request, err, duration)
            return InterfaceResponse(
                request_id=request.request_id,
                success=False,
                error=err,
                duration=duration,
            )

    def create_session(self, interface: str, metadata: Optional[dict] = None) -> InterfaceSession:
        session = InterfaceSession(
            session_id=f"if_ses_{uuid.uuid4().hex[:12]}",
            interface=interface,
            approval_state=ApprovalState.APPROVED,
            provenance={"created_by": "interface_gateway"},
            metadata=metadata or {},
        )
        self._sessions[session.session_id] = session
        return session

    def get_session(self, session_id: str) -> Optional[InterfaceSession]:
        return self._sessions.get(session_id)

    def list_sessions(self, interface: Optional[str] = None) -> list[InterfaceSession]:
        if interface:
            return [s for s in self._sessions.values() if s.interface == interface]
        return list(self._sessions.values())
