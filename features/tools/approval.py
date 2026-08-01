from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Optional

from .models import ApprovalRequest, ApprovalState


class ApprovalManager:

    def __init__(self):
        self._requests: dict[str, ApprovalRequest] = {}

    def create_request(self, tool_id: str, action: str, risk: str,
                       reason: str, requested_by: str) -> ApprovalRequest:
        req = ApprovalRequest(
            request_id=str(uuid.uuid4()),
            tool_id=tool_id,
            action=action,
            risk=risk,
            reason=reason,
            requested_by=requested_by,
        )
        self._requests[req.request_id] = req
        return req

    def approve(self, request_id: str) -> Optional[ApprovalRequest]:
        req = self._requests.get(request_id)
        if req is None or req.state != ApprovalState.PENDING:
            return None
        req.state = ApprovalState.APPROVED
        req.decided_at = datetime.now(timezone.utc).isoformat()
        return req

    def deny(self, request_id: str) -> Optional[ApprovalRequest]:
        req = self._requests.get(request_id)
        if req is None or req.state != ApprovalState.PENDING:
            return None
        req.state = ApprovalState.DENIED
        req.decided_at = datetime.now(timezone.utc).isoformat()
        return req

    def expire(self, request_id: str) -> Optional[ApprovalRequest]:
        req = self._requests.get(request_id)
        if req is None or req.state != ApprovalState.PENDING:
            return None
        req.state = ApprovalState.EXPIRED
        req.decided_at = datetime.now(timezone.utc).isoformat()
        return req

    def get_request(self, request_id: str) -> Optional[ApprovalRequest]:
        return self._requests.get(request_id)

    def list_pending(self) -> list[ApprovalRequest]:
        return [r for r in self._requests.values() if r.state == ApprovalState.PENDING]
