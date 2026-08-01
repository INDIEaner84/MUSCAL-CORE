from __future__ import annotations
import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

from event_bus import EventBus
from features.safety.safety_gate import SafetyGate
from features.tool_runtime.tool_runtime import UnifiedToolRuntime, create_default_utr
from features.supl.adapter_registry import AdapterRegistry
from features.supl.semantic_adapter import BaseSemanticAdapter
from features.supl.semantic_model import (
    SemanticApplication, ActionInvocation, Capability, Parameter,
    ApplicationState, Action, EventDefinition,
    RiskLevel, ExecutionMode, TrustLevel, ApplicationLifecycle, StateSource,
)
from features.supl.projection_engine import ProjectionEngine
from features.supl.event_integration import EventBusBridge
from features.supl.provenance_linker import ProvenanceLinker


def _build_calc_application():
    cap = Capability(id="calc", name="Calculator", description="Basic arithmetic",
                     risk_level=RiskLevel.LOW, execution_mode=ExecutionMode.DIRECT,
                     tool_name="math.add")
    p_a = Parameter(id="a", name="A", type="number", schema={"type": "number"}, required=True)
    p_b = Parameter(id="b", name="B", type="number", schema={"type": "number"}, required=True)
    act = Action(id="add", capability_id="calc", name="Add", parameter_ids=["a", "b"])
    evt = EventDefinition(id="added", name="Added", schema={})
    st = ApplicationState(id="last", name="Last", type="number", value=None, source=StateSource.UNKNOWN)
    return SemanticApplication(
        id="test_calc", name="Test Calc", version="1.0.0",
        source="test", lifecycle=ApplicationLifecycle.ACTIVE,
        trust_level=TrustLevel.LOW,
        capabilities={"calc": cap},
        parameters={"a": p_a, "b": p_b},
        state={"last": st},
        actions={"add": act},
        events={"added": evt},
    )


def _build_failing_application():
    cap = Capability(id="faulty", name="Faulty", description="Always fails",
                     risk_level=RiskLevel.LOW, execution_mode=ExecutionMode.DIRECT)
    return SemanticApplication(
        id="failing_app", name="Failing App", version="1.0.0",
        source="test", lifecycle=ApplicationLifecycle.ACTIVE,
        trust_level=TrustLevel.LOW,
        capabilities={"faulty": cap},
        parameters={}, state={}, actions={}, events={},
    )


def _build_no_utr_application():
    cap = Capability(id="tools", name="Tools", description="Non-UTR tools",
                     risk_level=RiskLevel.LOW, execution_mode=ExecutionMode.DIRECT,
                     tool_name="nonexistent.tool")
    p_x = Parameter(id="x", name="X", type="number", schema={"type": "number"}, required=True)
    act = Action(id="custom_op", capability_id="tools", name="Custom Op", parameter_ids=["x"])
    return SemanticApplication(
        id="no_utr_tool", name="No UTR Tool", version="1.0.0",
        source="test", lifecycle=ApplicationLifecycle.ACTIVE,
        trust_level=TrustLevel.LOW,
        capabilities={"tools": cap},
        parameters={"x": p_x},
        state={}, actions={"custom_op": act}, events={},
    )


def _build_rejecting_application():
    cap = Capability(id="unsafe", name="Unsafe", description="Gets rejected",
                     risk_level=RiskLevel.HIGH, execution_mode=ExecutionMode.DIRECT,
                     tool_name="shell.exec")
    p_cmd = Parameter(id="cmd", name="Cmd", type="string", schema={"type": "string"}, required=True)
    act = Action(id="danger", capability_id="unsafe", name="Danger", parameter_ids=["cmd"])
    return SemanticApplication(
        id="rejecting_app", name="Rejecting App", version="1.0.0",
        source="test", lifecycle=ApplicationLifecycle.ACTIVE,
        trust_level=TrustLevel.LOW,
        capabilities={"unsafe": cap},
        parameters={"cmd": p_cmd},
        state={}, actions={"danger": act}, events={},
    )


class CalcTestAdapter(BaseSemanticAdapter):
    application_id = "test_calc"
    application_version = "1.0.0"

    @property
    def application(self) -> SemanticApplication:
        return _build_calc_application()

    def discover(self) -> SemanticApplication:
        return _build_calc_application()

    def introspect_capability(self, capability_id: str):
        return _build_calc_application().capabilities.get(capability_id)

    def get_state(self, state_id: str):
        return _build_calc_application().state.get(state_id)

    def synchronize_state(self):
        app = _build_calc_application()
        return dict(app.state)

    def map_action(self, action_id: str, parameters: dict) -> ActionInvocation:
        app = _build_calc_application()
        action = app.actions.get(action_id)
        if action is None:
            raise ValueError(f"unknown action: {action_id}")
        cap = app.capabilities.get(action.capability_id)
        tool = cap.tool_name if cap else "math.add"
        resolved = {}
        for pid in action.parameter_ids:
            if pid in parameters:
                resolved[pid] = parameters[pid]
            else:
                param_def = app.parameters.get(pid)
                if param_def and param_def.required:
                    raise ValueError(f"missing required parameter: {pid}")
        return ActionInvocation(application_id="test_calc", capability_id=action.capability_id,
                                action_id=action_id, tool_name=tool, args=resolved)

    def handle_event(self, event_id: str, payload: dict) -> None:
        pass


class FailingTestAdapter(BaseSemanticAdapter):
    application_id = "failing_app"
    application_version = "1.0.0"

    @property
    def application(self) -> SemanticApplication:
        return _build_failing_application()

    def discover(self) -> SemanticApplication:
        return _build_failing_application()

    def introspect_capability(self, capability_id: str):
        return _build_failing_application().capabilities.get(capability_id)

    def get_state(self, state_id: str):
        return None

    def synchronize_state(self):
        return {}

    def map_action(self, action_id: str, parameters: dict) -> ActionInvocation:
        if action_id == "crash":
            raise ValueError("simulated mapping failure")
        raise ValueError(f"unknown action: {action_id}")

    def handle_event(self, event_id: str, payload: dict) -> None:
        pass


class NoUTRToolAdapter(BaseSemanticAdapter):
    application_id = "no_utr_tool"
    application_version = "1.0.0"

    @property
    def application(self) -> SemanticApplication:
        return _build_no_utr_application()

    def discover(self) -> SemanticApplication:
        return _build_no_utr_application()

    def introspect_capability(self, capability_id: str):
        return _build_no_utr_application().capabilities.get(capability_id)

    def get_state(self, state_id: str):
        return None

    def synchronize_state(self):
        return {}

    def map_action(self, action_id: str, parameters: dict) -> ActionInvocation:
        if action_id == "custom_op":
            return ActionInvocation(application_id="no_utr_tool", capability_id="tools",
                                    action_id=action_id, tool_name="nonexistent.tool", args=parameters)
        raise ValueError(f"unknown action: {action_id}")

    def handle_event(self, event_id: str, payload: dict) -> None:
        pass


class RejectingTestAdapter(BaseSemanticAdapter):
    application_id = "rejecting_app"
    application_version = "1.0.0"

    @property
    def application(self) -> SemanticApplication:
        return _build_rejecting_application()

    def discover(self) -> SemanticApplication:
        return _build_rejecting_application()

    def introspect_capability(self, capability_id: str):
        return _build_rejecting_application().capabilities.get(capability_id)

    def get_state(self, state_id: str):
        return None

    def synchronize_state(self):
        return {}

    def map_action(self, action_id: str, parameters: dict) -> ActionInvocation:
        if action_id == "danger":
            return ActionInvocation(application_id="rejecting_app", capability_id="unsafe",
                                    action_id=action_id, tool_name="shell.exec",
                                    args={"command": parameters.get("cmd", "ls")})
        raise ValueError(f"unknown action: {action_id}")

    def handle_event(self, event_id: str, payload: dict) -> None:
        pass


@pytest.fixture
def event_bus():
    bus = EventBus()
    yield bus


@pytest.fixture
def safety_gate():
    return SafetyGate()


@pytest.fixture
def utr(safety_gate):
    rt, _ = create_default_utr(safety_gate=safety_gate)
    return rt


@pytest.fixture
def registry():
    reg = AdapterRegistry()
    reg.register(CalcTestAdapter())
    reg.register(FailingTestAdapter())
    reg.register(NoUTRToolAdapter())
    reg.register(RejectingTestAdapter())
    return reg


@pytest.fixture
def projection_engine(registry):
    return ProjectionEngine(registry)


@pytest.fixture
def bridge(event_bus):
    return EventBusBridge(event_bus)


@pytest.fixture
def linker():
    return ProvenanceLinker()


@pytest.fixture
def calc_adapter():
    return CalcTestAdapter()
