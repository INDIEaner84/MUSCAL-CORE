from features.tool_runtime.tool_runtime import ExecutionReceipt, ToolResult


class TestExecutionReceiptSerialization:
    def test_to_dict_includes_all_identity_fields(self):
        receipt = ExecutionReceipt(
            tool_name="console.print",
            args={"message": "hello"},
            execution_time=0.5,
            result_data={"status": "success"},
            success=True,
            execution_id="ex-001",
            correlation_id="corr-001",
            causation_id="caus-001",
            trace_id="trace-001",
            span_id="span-001",
            decision_id="dec-001",
            request_id="req-001",
            plan_id="plan-001",
            step_id="step-001",
            agent_id="agent-001",
            model_id="model-001",
            cognitive_unit_id="cu-001",
            retry_count=1,
            attempt_number=2,
        )
        d = receipt.to_dict()
        assert d["receipt_id"] == receipt.receipt_id
        assert d["tool"] == "console.print"
        assert d["execution_id"] == "ex-001"
        assert d["correlation_id"] == "corr-001"
        assert d["causation_id"] == "caus-001"
        assert d["trace_id"] == "trace-001"
        assert d["span_id"] == "span-001"
        assert d["decision_id"] == "dec-001"
        assert d["request_id"] == "req-001"
        assert d["plan_id"] == "plan-001"
        assert d["step_id"] == "step-001"
        assert d["agent_id"] == "agent-001"
        assert d["model_id"] == "model-001"
        assert d["cognitive_unit_id"] == "cu-001"
        assert d["retry_count"] == 1
        assert d["attempt_number"] == 2

    def test_from_dict_roundtrip_preserves_all_fields(self):
        receipt = ExecutionReceipt(
            tool_name="console.print",
            args={"message": "hello"},
            execution_time=0.5,
            result_data={"status": "success"},
            success=True,
            execution_id="ex-001",
            correlation_id="corr-001",
            causation_id="caus-001",
            trace_id="trace-001",
            span_id="span-001",
            decision_id="dec-001",
            request_id="req-001",
            plan_id="plan-001",
            step_id="step-001",
            agent_id="agent-001",
            model_id="model-001",
            cognitive_unit_id="cu-001",
            retry_count=1,
            attempt_number=2,
        )
        receipt.finalize()
        d = receipt.to_dict()
        restored = ExecutionReceipt.from_dict(d)
        assert restored.receipt_id == receipt.receipt_id
        assert restored.tool_name == "console.print"
        assert restored.execution_id == "ex-001"
        assert restored.correlation_id == "corr-001"
        assert restored.causation_id == "caus-001"
        assert restored.request_id == "req-001"
        assert restored.plan_id == "plan-001"
        assert restored.step_id == "step-001"
        assert restored.retry_count == 1
        assert restored.attempt_number == 2
        assert restored.cognitive_unit_id == "cu-001"
        assert restored.integrity_hash == receipt.integrity_hash
        assert restored.finalized == receipt.finalized

    def test_tool_result_from_dict_uses_execution_receipt_from_dict(self):
        receipt = ExecutionReceipt(
            tool_name="console.print",
            args={"message": "hello"},
            execution_time=0.5,
            result_data={"status": "success"},
            success=True,
            execution_id="ex-002",
            correlation_id="corr-002",
            causation_id="caus-002",
            request_id="req-002",
            plan_id="plan-002",
            step_id="step-002",
            cognitive_unit_id="cu-002",
            retry_count=2,
            attempt_number=1,
        )
        result = ToolResult(
            tool_name="console.print",
            success=True,
            output={"status": "success"},
            execution_time=0.5,
            receipt=receipt,
        )
        d = result.to_dict()
        restored = ToolResult.from_dict(d)
        assert restored.receipt is not None
        assert restored.receipt.execution_id == "ex-002"
        assert restored.receipt.causation_id == "caus-002"
        assert restored.receipt.request_id == "req-002"
        assert restored.receipt.plan_id == "plan-002"
        assert restored.receipt.step_id == "step-002"
        assert restored.receipt.cognitive_unit_id == "cu-002"
        assert restored.receipt.retry_count == 2
        assert restored.receipt.attempt_number == 1
