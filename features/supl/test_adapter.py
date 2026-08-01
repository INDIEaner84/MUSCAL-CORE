from __future__ import annotations
from typing import Any, Dict, Optional

from features.supl.semantic_model import (
    SemanticApplication,
    Capability,
    Parameter,
    ApplicationState,
    Action,
    EventDefinition,
    ActionInvocation,
    RiskLevel,
    ExecutionMode,
    TrustLevel,
    ApplicationLifecycle,
    StateSource,
)
from features.supl.semantic_adapter import BaseSemanticAdapter


APPLICATION_ID = "test_calculator"
APPLICATION_NAME = "Test Calculator"
APPLICATION_VERSION = "0.1.0"


class TestCalculatorAdapter(BaseSemanticAdapter):
    @property
    def application_id(self) -> str:
        return APPLICATION_ID

    @property
    def application(self) -> SemanticApplication:
        return self._build_application()

    def discover(self) -> SemanticApplication:
        return self._build_application()

    def _build_application(self) -> SemanticApplication:
        cap_add = Capability(
            id="add",
            name="Add Numbers",
            description="Add two numbers and return the sum",
            risk_level=RiskLevel.LOW,
            execution_mode=ExecutionMode.DIRECT,
            tool_name="math.add",
        )
        param_a = Parameter(
            id="a",
            name="First Number",
            type="number",
            schema={"type": "number"},
            required=True,
        )
        param_b = Parameter(
            id="b",
            name="Second Number",
            type="number",
            schema={"type": "number"},
            required=True,
        )
        action = Action(
            id="calculate_sum",
            capability_id="add",
            name="Calculate Sum",
            parameter_ids=["a", "b"],
            authorization_required=False,
        )
        event = EventDefinition(
            id="calculation_completed",
            name="Calculation Completed",
            schema={"type": "object", "properties": {"result": {"type": "number"}}},
        )
        state = ApplicationState(
            id="last_result",
            name="Last Result",
            type="number",
            value=None,
            source=StateSource.UNKNOWN,
        )
        return SemanticApplication(
            id=APPLICATION_ID,
            name=APPLICATION_NAME,
            version=APPLICATION_VERSION,
            source="test_adapter.py",
            lifecycle=ApplicationLifecycle.ACTIVE,
            trust_level=TrustLevel.LOW,
            capabilities={"add": cap_add},
            parameters={"a": param_a, "b": param_b},
            state={"last_result": state},
            actions={"calculate_sum": action},
            events={"calculation_completed": event},
        )

    def introspect_capability(self, capability_id: str) -> Optional[Capability]:
        app = self._build_application()
        return app.capabilities.get(capability_id)

    def get_state(self, state_id: str) -> Optional[ApplicationState]:
        app = self._build_application()
        return app.state.get(state_id)

    def synchronize_state(self) -> Dict[str, ApplicationState]:
        return {"last_result": ApplicationState(
            id="last_result", name="Last Result", type="number",
            value=None, source=StateSource.UNKNOWN,
        )}

    def map_action(self, action_id: str, parameters: Dict[str, Any]) -> ActionInvocation:
        app = self._build_application()
        action = app.actions.get(action_id)
        if action is None:
            raise ValueError(f"unknown action: {action_id}")
        capability = app.capabilities.get(action.capability_id)
        if capability is None:
            raise ValueError(f"unknown capability: {action.capability_id}")
        resolved = {}
        for pid in action.parameter_ids:
            if pid in parameters:
                resolved[pid] = parameters[pid]
            else:
                param_def = app.parameters.get(pid)
                if param_def and param_def.default is not None:
                    resolved[pid] = param_def.default
                elif param_def and param_def.required:
                    raise ValueError(f"missing required parameter: {pid}")
        return ActionInvocation(
            application_id=APPLICATION_ID,
            capability_id=action.capability_id,
            action_id=action_id,
            tool_name=capability.tool_name,
            args=resolved,
        )

    def handle_event(self, event_id: str, payload: Dict[str, Any]) -> None:
        pass
