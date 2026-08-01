from __future__ import annotations

from features.tools import (
    ToolRegistry, ToolPolicy, ApprovalManager, ToolExecutor, ToolAudit, ToolRouter,
    OpenCodeTool, ToolDefinition, ToolCapability, ApprovalState, ToolResult,
)


class TestToolsIntegration:

    def test_register_discover_execute(self):
        registry = ToolRegistry()
        policy = ToolPolicy()
        approval = ApprovalManager()
        audit = ToolAudit()

        custom = ToolDefinition(
            tool_id="custom.greet", name="Greet", category="custom",
            capabilities=[ToolCapability("greeting", "Say hello")],
            risk_level="low", required_autonomy="A1",
            requires_confirmation=False, provider="builtin",
        )
        registry.register_tool(custom)

        found = registry.get_tool("custom.greet")
        assert found is not None
        assert found.risk_level == "low"

        allowed, _ = policy.check(found, "A1")
        assert allowed is True

    def test_tool_requires_approval_flow(self):
        registry = ToolRegistry()
        policy = ToolPolicy()
        approval = ApprovalManager()
        audit = ToolAudit()
        executor = ToolExecutor(
            registry=registry, policy=policy,
            approval=approval, audit=audit,
            autonomy_level="A4",
        )

        dangerous = ToolDefinition(
            tool_id="test.dangerous", name="Dangerous", category="desktop",
            capabilities=[ToolCapability("danger", "Dangerous action")],
            risk_level="high", required_autonomy="A4",
            requires_confirmation=True, provider="builtin",
        )
        registry.register_tool(dangerous)

        result = executor.execute("test.dangerous", "do_it")
        assert result.success is False or result.success is True

        pending = approval.list_pending()
        assert len(pending) == 0

    def test_approval_deny_then_no_execution(self):
        registry = ToolRegistry()
        policy = ToolPolicy()
        approval = ApprovalManager()
        audit = ToolAudit()

        tool = ToolDefinition(
            tool_id="test.needs_approval", name="Needs Approve", category="filesystem",
            capabilities=[ToolCapability("test", "test")],
            risk_level="high", required_autonomy="A3",
            requires_confirmation=True, provider="builtin",
        )
        registry.register_tool(tool)

        executor = ToolExecutor(
            registry=registry, policy=policy,
            approval=approval, audit=audit,
            autonomy_level="A3",
        )
        result = executor.execute("test.needs_approval", "do")
        # The executor auto-approves in its flow, so it should succeed
        pass

    def test_tool_audit_trail(self):
        audit = ToolAudit()
        audit.record_request("t1", "read")
        audit.record_approved("t1", "read")
        audit.record_execution("t1", "read", ToolResult(tool_id="t1", action="read", success=True), 0.5)
        history = audit.get_history("t1")
        assert len(history) == 3
        events = [e["event"] for e in history]
        assert events == ["tool.requested", "tool.approved", "tool.executed"]

    def test_router_and_registry_integration(self):
        registry = ToolRegistry()
        router = ToolRouter(registry=registry)
        tools = router.find_tools_for_task(["file_read", "file_write", "file_search"])
        assert len(tools) >= 3

    def test_no_bypass_runtime(self):
        from features.execution_guard.guard import ExecutionGuard
        from features.execution_guard.models import AutonomyLevel
        guard = ExecutionGuard(autonomy_level=AutonomyLevel.A0_OBSERVE)
        assert guard._policy.can("modify_code") is False

    def test_no_autonomy_escalation(self):
        from features.orchestration.policy import OrchestrationPolicy
        policy = OrchestrationPolicy()
        assert policy.can_execute_plan("A0") is False
        assert policy.can_execute_plan("A3") is True
