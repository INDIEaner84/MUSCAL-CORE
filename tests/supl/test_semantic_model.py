import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from features.supl.semantic_model import (
    RiskLevel, ExecutionMode, ApplicationLifecycle, TrustLevel,
    StateSource, InteractionSource, InteractionStatus,
    SemanticApplication, Capability, Parameter, ApplicationState,
    Action, EventDefinition, ActionInvocation,
)


def test_capability_valid():
    cap = Capability(id="add", name="Add", tool_name="math.add")
    errs = cap.validate()
    assert errs == []


def test_capability_missing_id():
    cap = Capability(id="", name="Add")
    errs = cap.validate()
    assert "capability.id is required" in errs


def test_capability_serialization():
    cap = Capability(id="add", name="Add Numbers", description="Adds two numbers",
                     risk_level=RiskLevel.LOW, execution_mode=ExecutionMode.DIRECT,
                     tool_name="math.add")
    d = cap.to_dict()
    assert d["id"] == "add"
    assert d["risk_level"] == "low"
    assert d["execution_mode"] == "direct"
    restored = Capability.from_dict(d)
    assert restored.id == cap.id
    assert restored.risk_level == cap.risk_level
    assert restored.execution_mode == cap.execution_mode


def test_capability_enum_from_string():
    cap = Capability.from_dict({"id": "x", "name": "X", "risk_level": "high", "execution_mode": "simulated"})
    assert cap.risk_level == RiskLevel.HIGH
    assert cap.execution_mode == ExecutionMode.SIMULATED


def test_parameter_valid():
    p = Parameter(id="a", name="First", type="number", required=True)
    errs = p.validate()
    assert errs == []


def test_parameter_missing_id():
    p = Parameter(id="", name="X")
    errs = p.validate()
    assert "parameter.id is required" in errs


def test_parameter_serialization():
    p = Parameter(id="a", name="Alpha", type="number", default=0, constraints={"min": 0}, required=True)
    d = p.to_dict()
    assert d["id"] == "a"
    assert d["required"] is True
    assert d["default"] == 0
    restored = Parameter.from_dict(d)
    assert restored.id == p.id
    assert restored.default == 0
    assert restored.required is True


def test_application_state_valid():
    s = ApplicationState(id="s1", name="State 1", value=42, source=StateSource.RUNTIME)
    errs = s.validate()
    assert errs == []
    d = s.to_dict()
    assert d["source"] == "runtime"
    restored = ApplicationState.from_dict(d)
    assert restored.source == StateSource.RUNTIME


def test_application_state_source_distinction():
    runtime = ApplicationState(id="r", name="R", value=1, source=StateSource.RUNTIME)
    simulated = ApplicationState(id="s", name="S", value=2, source=StateSource.SIMULATED)
    derived = ApplicationState(id="d", name="D", value=3, source=StateSource.DERIVED)
    unknown = ApplicationState(id="u", name="U", value=4, source=StateSource.UNKNOWN)
    assert runtime.to_dict()["source"] == "runtime"
    assert simulated.to_dict()["source"] == "simulated"
    assert derived.to_dict()["source"] == "derived"
    assert unknown.to_dict()["source"] == "unknown"
    assert runtime.source != simulated.source
    assert simulated.source != derived.source


def test_action_valid():
    caps = {"add": Capability(id="add", name="Add", tool_name="math.add")}
    a = Action(id="sum", capability_id="add", name="Calculate Sum")
    errs = a.validate(caps)
    assert errs == []


def test_action_missing_capability():
    caps = {}
    a = Action(id="sum", capability_id="nonexistent")
    errs = a.validate(caps)
    assert any("not found in capabilities" in e for e in errs)


def test_action_serialization():
    a = Action(id="calc", capability_id="add", name="Calc", parameter_ids=["a", "b"], authorization_required=True)
    d = a.to_dict()
    assert d["id"] == "calc"
    assert d["authorization_required"] is True
    restored = Action.from_dict(d)
    assert restored.id == a.id
    assert restored.authorization_required is True


def test_event_definition():
    e = EventDefinition(id="done", name="Completed", schema={"type": "object"})
    errs = e.validate()
    assert errs == []
    d = e.to_dict()
    assert d["id"] == "done"
    restored = EventDefinition.from_dict(d)
    assert restored.id == e.id


def test_event_missing_id():
    e = EventDefinition(id="", name="")
    errs = e.validate()
    assert "event.id is required" in errs


def test_action_invocation_frozen():
    inv = ActionInvocation(application_id="app", capability_id="cap", action_id="act", tool_name="tool", args={"a": 1})
    d = inv.to_dict()
    assert d["application_id"] == "app"
    assert d["tool_name"] == "tool"
    assert d["args"] == {"a": 1}
    restored = ActionInvocation.from_dict(d)
    assert restored.action_id == "act"


def test_action_invocation_no_callable():
    inv = ActionInvocation(application_id="app", capability_id="cap", action_id="act", tool_name="tool")
    assert not hasattr(inv, "__call__")


def test_action_invocation_contains_no_callable():
    inv = ActionInvocation(application_id="app", capability_id="cap", action_id="act", tool_name="tool")
    for item in [lambda: None, object(), "string", 42]:
        assert item not in inv


def test_semantic_application_valid():
    cap = Capability(id="add", name="Add", tool_name="math.add")
    app = SemanticApplication(
        id="test", name="Test App", capabilities={"add": cap},
        actions={"sum": Action(id="sum", capability_id="add")},
    )
    errs = app.validate()
    assert errs == []


def test_semantic_application_serialization():
    cap = Capability(id="add", name="Add", tool_name="math.add")
    app = SemanticApplication(
        id="test", name="Test App", version="1.0.0",
        capabilities={"add": cap},
    )
    d = app.to_dict()
    assert d["id"] == "test"
    assert d["version"] == "1.0.0"
    restored = SemanticApplication.from_dict(d)
    assert restored.id == app.id
    assert restored.version == app.version
    assert "add" in restored.capabilities


def test_enum_values_are_stable():
    assert RiskLevel.LOW.value == "low"
    assert RiskLevel.MEDIUM.value == "medium"
    assert RiskLevel.HIGH.value == "high"
    assert RiskLevel.CRITICAL.value == "critical"
    assert ExecutionMode.DIRECT.value == "direct"
    assert ExecutionMode.CONFIRMED.value == "confirmed"
    assert ExecutionMode.DELEGATED.value == "delegated"
    assert ExecutionMode.SIMULATED.value == "simulated"
    assert StateSource.RUNTIME.value == "runtime"
    assert StateSource.SIMULATED.value == "simulated"
    assert InteractionStatus.REQUESTED.value == "requested"
    assert InteractionStatus.EXECUTED.value == "executed"
    assert InteractionStatus.VERIFIED.value == "verified"


def test_simulated_not_equal_runtime():
    assert StateSource.SIMULATED != StateSource.RUNTIME
    assert StateSource.SIMULATED.value != StateSource.RUNTIME.value
