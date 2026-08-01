import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from features.supl.test_adapter import TestCalculatorAdapter
from features.supl.semantic_model import ActionInvocation


def test_action_invocation_utr_compatible():
    adapter = TestCalculatorAdapter()
    inv = adapter.map_action("calculate_sum", {"a": 7, "b": 5})
    assert isinstance(inv, ActionInvocation)
    assert inv.tool_name == "math.add"
    assert inv.args == {"a": 7, "b": 5}


def test_real_utr_execution():
    from features.tool_runtime.tool_runtime import create_default_utr
    from features.safety.safety_gate import SafetyGate
    adapter = TestCalculatorAdapter()
    inv = adapter.map_action("calculate_sum", {"a": 10, "b": 20})
    sg = SafetyGate()
    sg.permit("math.add")
    utr, _ = create_default_utr(safety_gate=sg)
    result = utr.execute(inv.tool_name, inv.args)
    assert result.success
    assert result.output["result"] == 30
    assert result.execution_time >= 0
    receipt = result.receipt
    assert receipt is not None
    assert receipt.receipt_id is not None
    assert receipt.execution_id is not None
    assert receipt.tool_name == "math.add"
    assert receipt.finalized is True
    assert receipt.verify_integrity() is True
    assert receipt.verification_status in ("pending", "verified", "not_supported")


def test_real_utr_execution_with_correlation():
    from features.tool_runtime.tool_runtime import create_default_utr
    from features.safety.safety_gate import SafetyGate
    from features.supl.provenance import UIInteraction
    adapter = TestCalculatorAdapter()
    inv = adapter.map_action("calculate_sum", {"a": 3, "b": 7})
    interaction = UIInteraction.create(
        application_id="test_calculator",
        action_id="calculate_sum",
        capability_id="add",
    )
    interaction.mark_authorized()
    interaction.mark_executing()
    sg = SafetyGate()
    sg.permit("math.add")
    utr, _ = create_default_utr(safety_gate=sg)
    result = utr.execute(inv.tool_name, inv.args, correlation_id=interaction.interaction_id)
    assert result.success
    assert result.output["result"] == 10
    receipt = result.receipt
    assert receipt is not None
    interaction.link_execution(receipt.execution_id)
    interaction.link_receipt(receipt.receipt_id)
    assert interaction.execution_id == receipt.execution_id
    assert interaction.receipt_id == receipt.receipt_id
    assert receipt.correlation_id == interaction.interaction_id


def test_correlation_semantics_preserved():
    from features.supl.test_adapter import TestCalculatorAdapter
    from features.supl.semantic_model import ActionInvocation
    from features.tool_runtime.tool_runtime import ExecutionReceipt
    receipt = ExecutionReceipt(correlation_id="test_interaction_001")
    assert receipt.correlation_id == "test_interaction_001"


def test_adapter_does_not_fabricate_execution():
    adapter = TestCalculatorAdapter()
    inv = adapter.map_action("calculate_sum", {"a": 1, "b": 2})
    assert not hasattr(inv, "execution_id")
    assert not hasattr(inv, "receipt_id")
    assert not hasattr(inv, "verification_id")


def test_no_fake_receipt_in_adapter():
    adapter = TestCalculatorAdapter()
    inv = adapter.map_action("calculate_sum", {"a": 1, "b": 2})
    import json
    d = json.loads(json.dumps(inv.to_dict()))
    assert "execution_id" not in d
    assert "receipt_id" not in d
    assert "verification_id" not in d
