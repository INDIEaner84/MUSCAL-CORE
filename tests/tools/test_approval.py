from __future__ import annotations

from features.tools.approval import ApprovalManager
from features.tools.models import ApprovalState


class TestApprovalManager:

    def test_create_request(self):
        mgr = ApprovalManager()
        req = mgr.create_request("filesystem.write", "write", "medium",
                                  "need to update config", "agent1")
        assert req.state == ApprovalState.PENDING
        assert req.tool_id == "filesystem.write"

    def test_approve(self):
        mgr = ApprovalManager()
        req = mgr.create_request("t1", "write", "low", "test", "user")
        approved = mgr.approve(req.request_id)
        assert approved is not None
        assert approved.state == ApprovalState.APPROVED

    def test_approve_not_found(self):
        mgr = ApprovalManager()
        assert mgr.approve("nonexistent") is None

    def test_deny(self):
        mgr = ApprovalManager()
        req = mgr.create_request("t1", "write", "low", "test", "user")
        denied = mgr.deny(req.request_id)
        assert denied is not None
        assert denied.state == ApprovalState.DENIED

    def test_deny_not_found(self):
        mgr = ApprovalManager()
        assert mgr.deny("nonexistent") is None

    def test_expire(self):
        mgr = ApprovalManager()
        req = mgr.create_request("t1", "write", "low", "test", "user")
        expired = mgr.expire(req.request_id)
        assert expired is not None
        assert expired.state == ApprovalState.EXPIRED

    def test_cannot_approve_twice(self):
        mgr = ApprovalManager()
        req = mgr.create_request("t1", "write", "low", "test", "user")
        mgr.approve(req.request_id)
        assert mgr.approve(req.request_id) is None

    def test_cannot_deny_after_approve(self):
        mgr = ApprovalManager()
        req = mgr.create_request("t1", "write", "low", "test", "user")
        mgr.approve(req.request_id)
        assert mgr.deny(req.request_id) is None

    def test_list_pending(self):
        mgr = ApprovalManager()
        mgr.create_request("t1", "write", "low", "a", "u1")
        mgr.create_request("t2", "read", "low", "b", "u2")
        assert len(mgr.list_pending()) == 2

    def test_list_pending_after_approve(self):
        mgr = ApprovalManager()
        r1 = mgr.create_request("t1", "write", "low", "a", "u1")
        mgr.create_request("t2", "read", "low", "b", "u2")
        mgr.approve(r1.request_id)
        assert len(mgr.list_pending()) == 1

    def test_get_request(self):
        mgr = ApprovalManager()
        req = mgr.create_request("t1", "write", "low", "test", "u1")
        assert mgr.get_request(req.request_id) is req

    def test_get_request_not_found(self):
        mgr = ApprovalManager()
        assert mgr.get_request("nonexistent") is None
