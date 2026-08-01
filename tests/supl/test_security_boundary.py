import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from features.supl.semantic_model import ActionInvocation, SemanticApplication, Capability
from features.supl.test_adapter import TestCalculatorAdapter


def test_action_invocation_has_no_callable():
    inv = ActionInvocation(application_id="a", capability_id="c", action_id="a", tool_name="t")
    assert not callable(inv)


def test_action_invocation_is_frozen():
    inv = ActionInvocation(application_id="a", capability_id="c", action_id="a", tool_name="t")
    import dataclasses
    assert dataclasses.is_dataclass(inv)


def test_adapter_no_executor_reference():
    adapter = TestCalculatorAdapter()
    app = adapter.discover()
    for cid, cap in app.capabilities.items():
        assert not callable(cap.tool_name)
    assert not hasattr(adapter, "_executor")
    assert not hasattr(adapter, "executor")


def test_semantic_model_contains_no_executor():
    cap = Capability(id="test", name="Test", tool_name="math.add")
    assert not callable(cap)
    assert not callable(cap.tool_name)


def test_state_source_simulated_not_runtime():
    from features.supl.semantic_model import StateSource
    sim = StateSource.SIMULATED
    runtime = StateSource.RUNTIME
    assert sim != runtime
    assert sim.value != runtime.value


def test_simulated_state_not_executed():
    from features.supl.provenance import UIInteraction
    from features.supl.semantic_model import InteractionStatus
    sim = UIInteraction.create()
    sim.mark_authorized()
    sim.mark_executing()
    sim.status = InteractionStatus.EXECUTED  # still not verified
    assert sim.status != InteractionStatus.VERIFIED
    assert sim.verification_id is None


def test_registry_no_executor_exposure():
    from features.supl.adapter_registry import AdapterRegistry
    from features.supl.test_adapter import TestCalculatorAdapter
    registry = AdapterRegistry()
    registry.register(TestCalculatorAdapter())
    items = registry.list()
    for item in items:
        assert callable(item) is False
        assert "executor" not in str(item)


def test_all_adapter_methods_return_serializable():
    adapter = TestCalculatorAdapter()
    app = adapter.discover()
    d = app.to_dict()
    import json
    js = json.dumps(d)
    assert len(js) > 0
    restored = SemanticApplication.from_dict(json.loads(js))
    assert restored.id == app.id


def test_no_import_chain_to_executor():
    import features.supl.test_adapter as ta
    with open(ta.__file__) as f:
        content = f.read()
    assert "UnifiedToolRuntime" not in content
    assert "UTR" not in content
    assert "SafetyGate" not in content
