import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from features.supl.test_adapter import TestCalculatorAdapter
from features.supl.semantic_model import (
    SemanticApplication, Capability, ActionInvocation, RiskLevel, ExecutionMode,
)


def test_adapter_discover():
    adapter = TestCalculatorAdapter()
    app = adapter.discover()
    assert isinstance(app, SemanticApplication)
    assert app.id == "test_calculator"
    assert app.name == "Test Calculator"


def test_adapter_application_id():
    adapter = TestCalculatorAdapter()
    assert adapter.application_id == "test_calculator"


def test_adapter_application():
    adapter = TestCalculatorAdapter()
    app = adapter.application
    assert isinstance(app, SemanticApplication)


def test_capability_introspection():
    adapter = TestCalculatorAdapter()
    cap = adapter.introspect_capability("add")
    assert cap is not None
    assert cap.id == "add"
    assert cap.tool_name == "math.add"
    assert cap.risk_level == RiskLevel.LOW
    assert cap.execution_mode == ExecutionMode.DIRECT


def test_capability_introspection_missing():
    adapter = TestCalculatorAdapter()
    cap = adapter.introspect_capability("nonexistent")
    assert cap is None


def test_get_state():
    adapter = TestCalculatorAdapter()
    state = adapter.get_state("last_result")
    assert state is not None
    assert state.id == "last_result"


def test_synchronize_state():
    adapter = TestCalculatorAdapter()
    states = adapter.synchronize_state()
    assert "last_result" in states


def test_map_action():
    adapter = TestCalculatorAdapter()
    inv = adapter.map_action("calculate_sum", {"a": 3, "b": 4})
    assert isinstance(inv, ActionInvocation)
    assert inv.application_id == "test_calculator"
    assert inv.capability_id == "add"
    assert inv.action_id == "calculate_sum"
    assert inv.tool_name == "math.add"
    assert inv.args == {"a": 3, "b": 4}


def test_map_action_missing_required():
    adapter = TestCalculatorAdapter()
    try:
        adapter.map_action("calculate_sum", {"a": 3})
    except ValueError as e:
        assert "required" in str(e)


def test_map_action_unknown():
    adapter = TestCalculatorAdapter()
    try:
        adapter.map_action("unknown_action", {})
    except ValueError as e:
        assert "unknown action" in str(e)


def test_action_invocation_contains_no_callable():
    adapter = TestCalculatorAdapter()
    inv = adapter.map_action("calculate_sum", {"a": 1, "b": 2})
    assert not hasattr(inv, "__call__")


def test_adapter_cannot_execute():
    adapter = TestCalculatorAdapter()
    assert not hasattr(adapter, "execute")
    assert not hasattr(adapter, "executor")
    inv = adapter.map_action("calculate_sum", {"a": 1, "b": 2})
    assert not callable(inv)


def test_tool_name_is_reference_not_executor():
    adapter = TestCalculatorAdapter()
    cap = adapter.introspect_capability("add")
    assert cap.tool_name == "math.add"
    import features.tool_runtime.tool_runtime as tr
    utr = tr.UnifiedToolRuntime()
    fn = utr.resolve(cap.tool_name)
    assert fn is None
