from __future__ import annotations
import json
import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional


class RiskLevel(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ExecutionMode(Enum):
    DIRECT = "direct"
    CONFIRMED = "confirmed"
    DELEGATED = "delegated"
    SIMULATED = "simulated"


class ApplicationLifecycle(Enum):
    ACTIVE = "active"
    PAUSED = "paused"
    UNAVAILABLE = "unavailable"
    ERROR = "error"


class TrustLevel(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    SYSTEM = "system"


class StateSource(Enum):
    RUNTIME = "runtime"
    SIMULATED = "simulated"
    USER = "user"
    DERIVED = "derived"
    UNKNOWN = "unknown"


class InteractionSource(Enum):
    NATIVE = "native"
    OVERLAY = "overlay"
    GRAPH_NATIVE = "graph_native"


class InteractionStatus(Enum):
    REQUESTED = "requested"
    AUTHORIZED = "authorized"
    REJECTED = "rejected"
    EXECUTING = "executing"
    EXECUTED = "executed"
    VERIFIED = "verified"
    FAILED = "failed"
    UNKNOWN = "unknown"


@dataclass
class Capability:
    id: str
    name: str
    description: str = ""
    risk_level: RiskLevel = RiskLevel.LOW
    execution_mode: ExecutionMode = ExecutionMode.DIRECT
    tool_name: str = ""

    def validate(self) -> List[str]:
        errors = []
        if not self.id:
            errors.append("capability.id is required")
        if not self.name:
            errors.append("capability.name is required")
        if isinstance(self.risk_level, str):
            try:
                self.risk_level = RiskLevel(self.risk_level)
            except ValueError:
                errors.append(f"invalid risk_level: {self.risk_level}")
        if isinstance(self.execution_mode, str):
            try:
                self.execution_mode = ExecutionMode(self.execution_mode)
            except ValueError:
                errors.append(f"invalid execution_mode: {self.execution_mode}")
        return errors

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "risk_level": self.risk_level.value,
            "execution_mode": self.execution_mode.value,
            "tool_name": self.tool_name,
        }

    @staticmethod
    def from_dict(d: Dict[str, Any]) -> "Capability":
        return Capability(
            id=d["id"],
            name=d["name"],
            description=d.get("description", ""),
            risk_level=RiskLevel(d.get("risk_level", "low")),
            execution_mode=ExecutionMode(d.get("execution_mode", "direct")),
            tool_name=d.get("tool_name", ""),
        )


@dataclass
class Parameter:
    id: str
    name: str
    type: str = "string"
    schema: Dict[str, Any] = field(default_factory=dict)
    default: Any = None
    constraints: Dict[str, Any] = field(default_factory=dict)
    required: bool = False

    def validate(self) -> List[str]:
        errors = []
        if not self.id:
            errors.append("parameter.id is required")
        if not self.name:
            errors.append("parameter.name is required")
        return errors

    def to_dict(self) -> Dict[str, Any]:
        d: Dict[str, Any] = {
            "id": self.id,
            "name": self.name,
            "type": self.type,
            "schema": self.schema,
            "required": self.required,
        }
        if self.default is not None:
            d["default"] = self.default
        if self.constraints:
            d["constraints"] = self.constraints
        return d

    @staticmethod
    def from_dict(d: Dict[str, Any]) -> "Parameter":
        return Parameter(
            id=d["id"],
            name=d["name"],
            type=d.get("type", "string"),
            schema=d.get("schema", {}),
            default=d.get("default"),
            constraints=d.get("constraints", {}),
            required=d.get("required", False),
        )


@dataclass
class ApplicationState:
    id: str
    name: str
    type: str = "string"
    value: Any = None
    source: StateSource = StateSource.UNKNOWN
    observed_at: Optional[float] = None
    version: str = "0.1.0"

    def validate(self) -> List[str]:
        errors = []
        if not self.id:
            errors.append("state.id is required")
        if isinstance(self.source, str):
            try:
                self.source = StateSource(self.source)
            except ValueError:
                errors.append(f"invalid state source: {self.source}")
        return errors

    def to_dict(self) -> Dict[str, Any]:
        d: Dict[str, Any] = {
            "id": self.id,
            "name": self.name,
            "type": self.type,
            "value": self.value,
            "source": self.source.value,
            "version": self.version,
        }
        if self.observed_at is not None:
            d["observed_at"] = self.observed_at
        return d

    @staticmethod
    def from_dict(d: Dict[str, Any]) -> "ApplicationState":
        return ApplicationState(
            id=d["id"],
            name=d["name"],
            type=d.get("type", "string"),
            value=d.get("value"),
            source=StateSource(d.get("source", "unknown")),
            observed_at=d.get("observed_at"),
            version=d.get("version", "0.1.0"),
        )


@dataclass
class Action:
    id: str
    capability_id: str
    name: str = ""
    parameter_ids: List[str] = field(default_factory=list)
    authorization_required: bool = False

    def validate(self, capabilities: Dict[str, Capability]) -> List[str]:
        errors = []
        if not self.id:
            errors.append("action.id is required")
        if not self.capability_id:
            errors.append("action.capability_id is required")
        elif self.capability_id not in capabilities:
            errors.append(f"action.capability_id '{self.capability_id}' not found in capabilities")
        return errors

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "capability_id": self.capability_id,
            "name": self.name,
            "parameter_ids": list(self.parameter_ids),
            "authorization_required": self.authorization_required,
        }

    @staticmethod
    def from_dict(d: Dict[str, Any]) -> "Action":
        return Action(
            id=d["id"],
            capability_id=d["capability_id"],
            name=d.get("name", ""),
            parameter_ids=d.get("parameter_ids", []),
            authorization_required=d.get("authorization_required", False),
        )


@dataclass
class EventDefinition:
    id: str
    name: str
    schema: Dict[str, Any] = field(default_factory=dict)

    def validate(self) -> List[str]:
        errors = []
        if not self.id:
            errors.append("event.id is required")
        if not self.name:
            errors.append("event.name is required")
        return errors

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "schema": self.schema,
        }

    @staticmethod
    def from_dict(d: Dict[str, Any]) -> "EventDefinition":
        return EventDefinition(
            id=d["id"],
            name=d["name"],
            schema=d.get("schema", {}),
        )


@dataclass(frozen=True)
class ActionInvocation:
    application_id: str
    capability_id: str
    action_id: str
    tool_name: str
    args: Dict[str, Any] = field(default_factory=dict)

    def validate(self) -> List[str]:
        errors = []
        if not self.application_id:
            errors.append("application_id is required")
        if not self.capability_id:
            errors.append("capability_id is required")
        if not self.action_id:
            errors.append("action_id is required")
        if not self.tool_name:
            errors.append("tool_name is required")
        return errors

    def to_dict(self) -> Dict[str, Any]:
        return {
            "application_id": self.application_id,
            "capability_id": self.capability_id,
            "action_id": self.action_id,
            "tool_name": self.tool_name,
            "args": dict(self.args),
        }

    @staticmethod
    def from_dict(d: Dict[str, Any]) -> "ActionInvocation":
        return ActionInvocation(
            application_id=d["application_id"],
            capability_id=d["capability_id"],
            action_id=d["action_id"],
            tool_name=d["tool_name"],
            args=d.get("args", {}),
        )

    def __contains__(self, item: Any) -> bool:
        return False


_APPLICATION_MANDATORY = ["id", "name", "version"]


@dataclass
class SemanticApplication:
    id: str
    name: str
    version: str = "0.1.0"
    source: str = ""
    lifecycle: ApplicationLifecycle = ApplicationLifecycle.ACTIVE
    trust_level: TrustLevel = TrustLevel.LOW
    capabilities: Dict[str, Capability] = field(default_factory=dict)
    parameters: Dict[str, Parameter] = field(default_factory=dict)
    state: Dict[str, ApplicationState] = field(default_factory=dict)
    actions: Dict[str, Action] = field(default_factory=dict)
    events: Dict[str, EventDefinition] = field(default_factory=dict)

    def validate(self) -> List[str]:
        errors = []
        if not self.id:
            errors.append("application.id is required")
        if not self.name:
            errors.append("application.name is required")
        if isinstance(self.lifecycle, str):
            try:
                self.lifecycle = ApplicationLifecycle(self.lifecycle)
            except ValueError:
                errors.append(f"invalid lifecycle: {self.lifecycle}")
        if isinstance(self.trust_level, str):
            try:
                self.trust_level = TrustLevel(self.trust_level)
            except ValueError:
                errors.append(f"invalid trust_level: {self.trust_level}")
        cap_map = self.capabilities
        for aid, action in self.actions.items():
            errors.extend(action.validate(cap_map))
        for cid, cap in self.capabilities.items():
            errors.extend(cap.validate())
        for pid, param in self.parameters.items():
            errors.extend(param.validate())
        for sid, st in self.state.items():
            errors.extend(st.validate())
        for eid, ev in self.events.items():
            errors.extend(ev.validate())
        return errors

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "version": self.version,
            "source": self.source,
            "lifecycle": self.lifecycle.value,
            "trust_level": self.trust_level.value,
            "capabilities": {k: v.to_dict() for k, v in self.capabilities.items()},
            "parameters": {k: v.to_dict() for k, v in self.parameters.items()},
            "state": {k: v.to_dict() for k, v in self.state.items()},
            "actions": {k: v.to_dict() for k, v in self.actions.items()},
            "events": {k: v.to_dict() for k, v in self.events.items()},
        }

    @staticmethod
    def from_dict(d: Dict[str, Any]) -> "SemanticApplication":
        return SemanticApplication(
            id=d["id"],
            name=d["name"],
            version=d.get("version", "0.1.0"),
            source=d.get("source", ""),
            lifecycle=ApplicationLifecycle(d.get("lifecycle", "active")),
            trust_level=TrustLevel(d.get("trust_level", "low")),
            capabilities={k: Capability.from_dict(v) for k, v in d.get("capabilities", {}).items()},
            parameters={k: Parameter.from_dict(v) for k, v in d.get("parameters", {}).items()},
            state={k: ApplicationState.from_dict(v) for k, v in d.get("state", {}).items()},
            actions={k: Action.from_dict(v) for k, v in d.get("actions", {}).items()},
            events={k: EventDefinition.from_dict(v) for k, v in d.get("events", {}).items()},
        )


def semantic_application_to_json(app: SemanticApplication, indent: int = 2) -> str:
    return json.dumps(app.to_dict(), indent=indent, ensure_ascii=False)


def semantic_application_from_json(text: str) -> SemanticApplication:
    return SemanticApplication.from_dict(json.loads(text))
