from __future__ import annotations

import pytest

from features.interface_gateway.models import (
    InterfaceRequest, InterfaceResponse, InterfaceCapability,
    InterfaceSession, ApprovalState, VerificationState,
)
from features.interface_gateway.adapter_registry import AdapterRegistry
from features.interface_gateway.policy_adapter import InterfacePolicyAdapter
from features.interface_gateway.audit import InterfaceAudit
from features.interface_gateway.gateway import InterfaceGateway
from features.interface_gateway.browser_adapter import BrowserAdapter
from features.interface_gateway.desktop_adapter import DesktopAdapter
from features.interface_gateway.mcp_gateway import MCPGateway
from features.interface_gateway.benchmark_hooks import InterfaceBenchmarkHooks
from features.runtime.models import INTERFACE_EVENTS, ALL_RUNTIME_EVENTS


# ── Model Tests ─────────────────────────────────────────────────────────

class TestInterfaceCapability:
    def test_default_risk(self):
        cap = InterfaceCapability("test", "desc")
        assert cap.risk_level == "low"

    def test_to_dict(self):
        cap = InterfaceCapability("navigate", "desc", "medium")
        d = cap.to_dict()
        assert d["interface_capability"]["name"] == "navigate"

    def test_requires_confirmation_default(self):
        cap = InterfaceCapability("test", "desc")
        assert cap.requires_confirmation is False

    def test_requires_confirmation_true(self):
        cap = InterfaceCapability("test", "desc", requires_confirmation=True)
        assert cap.requires_confirmation is True


class TestInterfaceRequest:
    def test_defaults(self):
        req = InterfaceRequest(interface="browser", action="navigate", params={})
        assert req.session_id == ""
        assert req.request_id.startswith("if_req_")

    def test_to_dict(self):
        req = InterfaceRequest(interface="desktop", action="click", params={"x": 10},
                               session_id="s1", execution_id="e1")
        d = req.to_dict()
        assert d["interface_request"]["interface"] == "desktop"
        assert d["interface_request"]["action"] == "click"

    def test_custom_request_id(self):
        req = InterfaceRequest(interface="browser", action="read", params={},
                               request_id="my_id")
        assert req.request_id == "my_id"


class TestInterfaceResponse:
    def test_default_timestamp(self):
        resp = InterfaceResponse(request_id="r1", success=True)
        assert resp.timestamp != ""

    def test_verification_default(self):
        resp = InterfaceResponse(request_id="r1", success=True)
        assert resp.verification_state == VerificationState.UNVERIFIED

    def test_to_dict(self):
        resp = InterfaceResponse(request_id="r1", success=True, output="ok",
                                  verification_state=VerificationState.VERIFIED)
        d = resp.to_dict()
        assert d["interface_response"]["verification_state"] == "VERIFIED"

    def test_error_response(self):
        resp = InterfaceResponse(request_id="r1", success=False, error="fail")
        assert resp.success is False
        assert resp.error == "fail"


class TestInterfaceSession:
    def test_default_created_at(self):
        ses = InterfaceSession(session_id="s1", interface="browser")
        assert ses.created_at != ""

    def test_approval_default(self):
        ses = InterfaceSession(session_id="s1", interface="desktop")
        assert ses.approval_state == ApprovalState.PENDING

    def test_to_dict(self):
        ses = InterfaceSession(session_id="s1", interface="browser",
                                approval_state=ApprovalState.APPROVED)
        d = ses.to_dict()
        assert d["interface_session"]["approval_state"] == "APPROVED"

    def test_provenance(self):
        ses = InterfaceSession(session_id="s1", interface="mcp",
                                provenance={"user": "alice"})
        assert ses.provenance["user"] == "alice"

    def test_metadata(self):
        ses = InterfaceSession(session_id="s1", interface="browser",
                                metadata={"env": "test"})
        assert ses.metadata["env"] == "test"

    def test_enum_values(self):
        assert ApprovalState.PENDING.value == "PENDING"
        assert ApprovalState.APPROVED.value == "APPROVED"
        assert ApprovalState.DENIED.value == "DENIED"
        assert ApprovalState.EXPIRED.value == "EXPIRED"
        assert VerificationState.UNVERIFIED.value == "UNVERIFIED"
        assert VerificationState.VERIFIED.value == "VERIFIED"
        assert VerificationState.FAILED.value == "FAILED"


# ── Adapter Registry Tests ──────────────────────────────────────────────

class TestAdapterRegistry:
    def setup_method(self):
        self.registry = AdapterRegistry()

    def test_register_and_get(self):
        adapter = BrowserAdapter()
        self.registry.register("browser", adapter)
        assert self.registry.get("browser") is adapter

    def test_get_nonexistent(self):
        assert self.registry.get("nonexistent") is None

    def test_has_interface(self):
        self.registry.register("browser", BrowserAdapter())
        assert self.registry.has_interface("browser") is True
        assert self.registry.has_interface("desktop") is False

    def test_list_interfaces(self):
        self.registry.register("browser", BrowserAdapter())
        self.registry.register("desktop", DesktopAdapter())
        assert "browser" in self.registry.list_interfaces()
        assert "desktop" in self.registry.list_interfaces()

    def test_unregister(self):
        self.registry.register("browser", BrowserAdapter())
        assert self.registry.unregister("browser") is True
        assert self.registry.has_interface("browser") is False

    def test_unregister_nonexistent(self):
        assert self.registry.unregister("nonexistent") is False

    def test_clear(self):
        self.registry.register("a", BrowserAdapter())
        self.registry.register("b", DesktopAdapter())
        self.registry.clear()
        assert len(self.registry.list_interfaces()) == 0

    def test_register_replaces(self):
        a1 = BrowserAdapter()
        a2 = BrowserAdapter()
        self.registry.register("browser", a1)
        self.registry.register("browser", a2)
        assert self.registry.get("browser") is a2


# ── Policy Adapter Tests ────────────────────────────────────────────────

class TestInterfacePolicyAdapter:
    def setup_method(self):
        self.policy = InterfacePolicyAdapter()

    def test_browser_allowed_at_a3(self):
        ok, _ = self.policy.check("browser.navigate", "A3")
        assert ok is True

    def test_browser_allowed_at_a1(self):
        ok, _ = self.policy.check("browser.navigate", "A1")
        assert ok is True

    def test_desktop_click_requires_a3(self):
        ok, _ = self.policy.check("desktop.mouse_click", "A3")
        assert ok is False

    def test_desktop_click_confirmation_a4(self):
        ok, _ = self.policy.check("desktop.mouse_click", "A4")
        assert ok is False

    def test_desktop_click_confirmation_a5(self):
        ok, _ = self.policy.check("desktop.mouse_click", "A5")
        assert ok is False

    def test_desktop_mouse_move_allowed_at_a3(self):
        ok, _ = self.policy.check("desktop.mouse_move", "A3")
        assert ok is True

    def test_unknown_action_defaults_read_only(self):
        ok, _ = self.policy.check("unknown.action", "A1")
        assert ok is True

    def test_mcp_discover_allowed(self):
        ok, _ = self.policy.check("mcp.discover", "A3")
        assert ok is True

    def test_mcp_execute_requires_confirmation(self):
        ok, _ = self.policy.check("mcp.execute", "A3")
        assert ok is False

    def test_mcp_execute_a5_still_confirmation(self):
        ok, _ = self.policy.check("mcp.execute", "A5")
        assert ok is False

    def test_is_action_allowed_false_for_low_autonomy(self):
        assert self.policy.is_action_allowed("desktop.keyboard_type", "A1") is False

    def test_is_action_allowed_true_for_high(self):
        assert self.policy.is_action_allowed("desktop.mouse_move", "A3") is True


# ── Interface Audit Tests ────────────────────────────────────────────────

class TestInterfaceAudit:
    def setup_method(self):
        self.audit = InterfaceAudit()
        self.req = InterfaceRequest(interface="browser", action="navigate", params={},
                                     request_id="test_req")

    def test_record_requested(self):
        self.audit.record_requested(self.req)
        assert len(self.audit.get_history()) == 1
        assert self.audit.get_history()[0]["event"] == "interface.requested"

    def test_record_approved(self):
        self.audit.record_approved(self.req)
        assert self.audit.get_history()[0]["event"] == "interface.approved"

    def test_record_denied(self):
        self.audit.record_denied(self.req, "not allowed")
        assert self.audit.get_history()[0]["reason"] == "not allowed"

    def test_record_executed(self):
        resp = InterfaceResponse(request_id="test_req", success=True, output="ok", duration=0.5)
        self.audit.record_executed(self.req, resp)
        assert self.audit.get_history()[0]["success"] is True

    def test_record_failed(self):
        self.audit.record_failed(self.req, "error occurred", 1.0)
        assert self.audit.get_history()[0]["error"] == "error occurred"

    def test_record_verified(self):
        resp = InterfaceResponse(request_id="test_req", success=True,
                                  verification_state=VerificationState.VERIFIED)
        self.audit.record_verified(self.req, resp)
        assert self.audit.get_history()[0]["verification_state"] == "VERIFIED"

    def test_get_history_filtered(self):
        req2 = InterfaceRequest(interface="desktop", action="click", params={})
        self.audit.record_requested(self.req)
        self.audit.record_requested(req2)
        browser_events = self.audit.get_history(interface="browser")
        assert len(browser_events) == 1

    def test_clear(self):
        self.audit.record_requested(self.req)
        self.audit.clear()
        assert len(self.audit.get_history()) == 0


# ── Browser Adapter Tests ───────────────────────────────────────────────

class TestBrowserAdapter:
    def setup_method(self):
        self.adapter = BrowserAdapter()

    def test_navigate(self):
        result = self.adapter.navigate("https://example.com")
        assert result["status"] == "navigated"

    def test_navigate_invalid_scheme(self):
        with pytest.raises(ValueError):
            self.adapter.navigate("ftp://bad.com")

    def test_read_page(self):
        result = self.adapter.read_page("https://example.com")
        assert "content" in result

    def test_read_page_bad_scheme(self):
        with pytest.raises(ValueError):
            self.adapter.read_page("file:///etc/passwd")

    def test_extract_content(self):
        result = self.adapter.extract_content("https://example.com")
        assert "extracted" in result

    def test_extract_content_bad_scheme(self):
        with pytest.raises(ValueError):
            self.adapter.extract_content("javascript:alert(1)")

    def test_screenshot(self):
        result = self.adapter.screenshot("https://example.com")
        assert "screenshot_path" in result

    def test_screenshot_bad_scheme(self):
        with pytest.raises(ValueError):
            self.adapter.screenshot("data:text/html,<script>")

    def test_navigate_https(self):
        result = self.adapter.navigate("https://secure.com")
        assert result["url"] == "https://secure.com"


# ── Desktop Adapter Tests ───────────────────────────────────────────────

class TestDesktopAdapter:
    def setup_method(self):
        self.adapter = DesktopAdapter()

    def test_mouse_move(self):
        result = self.adapter.mouse_move(100, 200)
        assert result["status"] == "ok"

    def test_mouse_move_negative(self):
        with pytest.raises(ValueError):
            self.adapter.mouse_move(-1, 0)

    def test_mouse_click(self):
        result = self.adapter.mouse_click(10, 20)
        assert result["button"] == "left"

    def test_mouse_click_invalid_button(self):
        with pytest.raises(ValueError):
            self.adapter.mouse_click(0, 0, button="unknown")

    def test_mouse_click_negative(self):
        with pytest.raises(ValueError):
            self.adapter.mouse_click(-5, 0)

    def test_mouse_click_right(self):
        result = self.adapter.mouse_click(0, 0, button="right")
        assert result["button"] == "right"

    def test_mouse_click_middle(self):
        result = self.adapter.mouse_click(0, 0, button="middle")
        assert result["button"] == "middle"

    def test_keyboard_type(self):
        result = self.adapter.keyboard_type("hello world")
        assert result["length"] == 11

    def test_keyboard_type_non_string(self):
        with pytest.raises(ValueError):
            self.adapter.keyboard_type(123)

    def test_window_manage_focus(self):
        result = self.adapter.window_manage("focus", "Terminal")
        assert result["status"] == "ok"

    def test_window_manage_invalid_action(self):
        with pytest.raises(ValueError):
            self.adapter.window_manage("destroy")

    def test_window_manage_minimize(self):
        result = self.adapter.window_manage("minimize")
        assert result["window_action"] == "minimize"

    def test_window_manage_maximize(self):
        result = self.adapter.window_manage("maximize")
        assert result["window_action"] == "maximize"

    def test_window_manage_close(self):
        result = self.adapter.window_manage("close")
        assert result["window_action"] == "close"

    def test_window_manage_resize(self):
        result = self.adapter.window_manage("resize")
        assert result["window_action"] == "resize"

    def test_window_manage_move(self):
        result = self.adapter.window_manage("move")
        assert result["window_action"] == "move"

    def test_filesystem_read(self):
        import tempfile, os
        f = tempfile.NamedTemporaryFile(delete=False)
        f.close()
        try:
            result = self.adapter.filesystem_read(f.name)
            assert result["status"] == "ok"
        finally:
            os.unlink(f.name)

    def test_filesystem_read_nonexistent(self):
        with pytest.raises(FileNotFoundError):
            self.adapter.filesystem_read("/nonexistent/path")

    def test_filesystem_write(self):
        result = self.adapter.filesystem_write("/tmp/test.txt", "content")
        assert result["status"] == "ok"

    def test_filesystem_write_non_string(self):
        with pytest.raises(ValueError):
            self.adapter.filesystem_write("/tmp/test.txt", 123)


# ── MCP Gateway Tests ───────────────────────────────────────────────────

class TestMCPGateway:
    def setup_method(self):
        self.gateway = MCPGateway()

    def test_discover_tools(self):
        tools = self.gateway.discover_tools()
        assert len(tools) >= 10

    def test_validate_schema_valid(self):
        schema = {"tool_id": "t1", "name": "n", "category": "c", "capabilities": []}
        result = self.gateway.validate_schema(schema)
        assert result["valid"] is True

    def test_validate_schema_missing_id(self):
        result = self.gateway.validate_schema({"name": "n", "category": "c"})
        assert result["valid"] is False

    def test_validate_schema_missing_name(self):
        result = self.gateway.validate_schema({"tool_id": "t1", "category": "c"})
        assert result["valid"] is False

    def test_validate_schema_missing_category(self):
        result = self.gateway.validate_schema({"tool_id": "t1", "name": "n"})
        assert result["valid"] is False

    def test_validate_schema_capability_missing_name(self):
        schema = {"tool_id": "t1", "name": "n", "category": "c",
                  "capabilities": [{"description": "no name"}]}
        result = self.gateway.validate_schema(schema)
        assert result["valid"] is False

    def test_register_tool(self):
        schema = {"tool_id": "mcp_test", "name": "MCP Test", "category": "mcp",
                  "capabilities": [{"name": "test_cap", "description": "a cap"}],
                  "risk_level": "low", "required_autonomy": "A3"}
        result = self.gateway.register_tool(schema)
        assert result["status"] == "registered"

    def test_register_tool_duplicate(self):
        schema = {"tool_id": "dup", "name": "Dup", "category": "mcp", "capabilities": []}
        self.gateway.register_tool(schema)
        with pytest.raises(ValueError):
            self.gateway.register_tool(schema)

    def test_register_tool_missing_id(self):
        with pytest.raises(ValueError):
            self.gateway.register_tool({"name": "n"})

    def test_register_tool_missing_fields(self):
        with pytest.raises(ValueError):
            self.gateway.register_tool({"tool_id": "t1"})

    def test_register_adds_to_registry(self):
        schema = {"tool_id": "mcp_r", "name": "MCP R", "category": "mcp",
                  "capabilities": [{"name": "c1", "description": "d1"}],
                  "risk_level": "medium", "required_autonomy": "A3",
                  "requires_confirmation": True}
        self.gateway.register_tool(schema)
        tool = self.gateway._tool_registry.get_tool("mcp_r")
        assert tool is not None
        assert tool.risk_level == "medium"

    def test_route_request(self):
        schema = {"tool_id": "route_test", "name": "Route", "category": "mcp",
                  "capabilities": []}
        self.gateway.register_tool(schema)
        result = self.gateway.route_request("route_test", "execute", {"key": "val"})
        assert result["routed"] is True

    def test_route_request_unregistered(self):
        with pytest.raises(ValueError):
            self.gateway.route_request("unknown", "execute")

    def test_list_mcp_tools(self):
        schema = {"tool_id": "lst", "name": "Lst", "category": "mcp", "capabilities": []}
        self.gateway.register_tool(schema)
        tools = self.gateway.list_mcp_tools()
        assert len(tools) == 1


# ── Gateway Tests ───────────────────────────────────────────────────────

class TestInterfaceGateway:
    def setup_method(self):
        self.gateway = InterfaceGateway(autonomy_level="A4")
        self.gateway.registry.register("browser", BrowserAdapter())
        self.gateway.registry.register("desktop", DesktopAdapter())

    def test_execute_browser_navigate(self):
        resp = self.gateway.execute("browser", "navigate", {"url": "https://example.com"})
        assert resp.success is True

    def test_execute_desktop_mouse_move(self):
        resp = self.gateway.execute("desktop", "mouse_move", {"x": 100, "y": 200})
        assert resp.success is True

    def test_execute_unregistered_interface(self):
        resp = self.gateway.execute("unknown", "action", {})
        assert resp.success is False

    def test_execute_missing_action(self):
        resp = self.gateway.execute("browser", "nonexistent", {})
        assert resp.success is False

    def test_execute_policy_denied(self):
        gateway = InterfaceGateway(autonomy_level="A1")
        gateway.registry.register("desktop", DesktopAdapter())
        resp = gateway.execute("desktop", "mouse_click", {"x": 0, "y": 0})
        assert resp.success is False

    def test_execute_exception_handling(self):
        resp = self.gateway.execute("desktop", "mouse_move", {"x": -1, "y": 0})
        assert resp.success is False

    def test_audit_records(self):
        self.gateway.execute("browser", "navigate", {"url": "https://example.com"})
        history = self.gateway.audit.get_history()
        assert len(history) >= 3

    def test_create_session(self):
        session = self.gateway.create_session("browser")
        assert session.interface == "browser"
        assert session.approval_state == ApprovalState.APPROVED

    def test_get_session(self):
        session = self.gateway.create_session("browser")
        retrieved = self.gateway.get_session(session.session_id)
        assert retrieved is session

    def test_get_session_nonexistent(self):
        assert self.gateway.get_session("nonexistent") is None

    def test_list_sessions(self):
        self.gateway.create_session("browser", {"env": "test"})
        self.gateway.create_session("desktop", {"env": "prod"})
        sessions = self.gateway.list_sessions()
        assert len(sessions) == 2

    def test_list_sessions_filtered(self):
        self.gateway.create_session("browser")
        self.gateway.create_session("desktop")
        browser_sessions = self.gateway.list_sessions(interface="browser")
        assert len(browser_sessions) == 1
        assert browser_sessions[0].interface == "browser"


# ── Benchmark Hooks Tests ───────────────────────────────────────────────

class TestBenchmarkHooks:
    def setup_method(self):
        self.hooks = InterfaceBenchmarkHooks()

    def test_record(self):
        self.hooks.record("browser.navigate", 1.5, True)
        assert len(self.hooks.get_all()) == 1

    def test_summary_empty(self):
        s = self.hooks.summary()
        assert s["count"] == 0

    def test_summary_with_data(self):
        self.hooks.record("browser.navigate", 1.0, True, 0.1, 0.05)
        self.hooks.record("desktop.click", 2.0, False, 0.2, 0.1)
        s = self.hooks.summary()
        assert s["count"] == 2
        assert s["success_rate"] == 0.5
        assert s["avg_latency"] == 1.5
        assert abs(s["avg_approval_overhead"] - 0.15) < 1e-10
        assert abs(s["avg_verification_cost"] - 0.075) < 1e-10

    def test_record_with_resource_usage(self):
        self.hooks.record("browser.navigate", 1.0, True,
                           resource_usage={"cpu": 0.5, "memory": 100})
        s = self.hooks.summary()
        assert s["total_resource_usage"]["cpu"] == 0.5
        assert s["total_resource_usage"]["memory"] == 100

    def test_clear(self):
        self.hooks.record("browser.navigate", 1.0, True)
        self.hooks.clear()
        assert len(self.hooks.get_all()) == 0

    def test_to_dict(self):
        from features.interface_gateway.benchmark_hooks import BenchmarkMeasurement
        m = BenchmarkMeasurement(operation="test", latency=0.5, success=True,
                                  approval_overhead=0.1, verification_cost=0.05)
        d = m.to_dict()
        assert d["benchmark"]["operation"] == "test"


# ── Runtime Events Tests ────────────────────────────────────────────────

class TestInterfaceRuntimeEvents:
    def test_interface_events_in_all(self):
        for e in INTERFACE_EVENTS:
            assert e in ALL_RUNTIME_EVENTS, f"{e} not in ALL_RUNTIME_EVENTS"

    def test_interface_events_count(self):
        assert len(INTERFACE_EVENTS) == 5

    def test_interface_requested_present(self):
        assert "interface.requested" in INTERFACE_EVENTS

    def test_interface_approved_present(self):
        assert "interface.approved" in INTERFACE_EVENTS

    def test_interface_executed_present(self):
        assert "interface.executed" in INTERFACE_EVENTS

    def test_interface_failed_present(self):
        assert "interface.failed" in INTERFACE_EVENTS

    def test_interface_verified_present(self):
        assert "interface.verified" in INTERFACE_EVENTS


# ── Gateway + MCP Integration Tests ─────────────────────────────────────

class TestGatewayMCPIntegration:
    def setup_method(self):
        self.gateway = InterfaceGateway(autonomy_level="A3")
        self.mcp = MCPGateway()
        self.gateway.registry.register("mcp", self.mcp)

    def test_discover_through_gateway(self):
        resp = self.gateway.execute("mcp", "discover_tools")
        assert resp.success is True
        assert len(resp.output) >= 10

    def test_validate_schema_through_gateway(self):
        resp = self.gateway.execute("mcp", "validate_schema",
                                     {"schema": {"tool_id": "t1", "name": "n", "category": "c"}})
        assert resp.success is True
        assert resp.output["valid"] is True

    def test_register_through_gateway(self):
        resp = self.gateway.execute("mcp", "register_tool",
                                     {"schema": {"tool_id": "gw_test", "name": "GW",
                                                 "category": "mcp", "capabilities": []}})
        assert resp.success is True
        assert resp.output["status"] == "registered"

    def test_route_through_gateway(self):
        self.mcp.register_tool({"tool_id": "rt", "name": "RT", "category": "mcp", "capabilities": []})
        resp = self.gateway.execute("mcp", "route_request",
                                     {"tool_id": "rt", "action": "execute", "params": {}})
        assert resp.success is True
        assert resp.output["routed"] is True
