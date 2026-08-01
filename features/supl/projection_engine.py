from __future__ import annotations
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Set

from features.supl.semantic_model import (
    SemanticApplication, Capability, Action, ApplicationState,
    Parameter, RiskLevel, ExecutionMode,
)
from features.supl.adapter_registry import AdapterRegistry


class UIMode(Enum):
    NATIVE = "native"
    OVERLAY = "overlay"
    GRAPH_NATIVE = "graph_native"


class ProjectionState(Enum):
    SYNCED = "synced"
    STALE = "stale"
    LOADING = "loading"
    ERROR = "error"


@dataclass
class ProjectionContext:
    user: str = ""
    role: str = ""
    task: str = ""
    permissions: Set[str] = field(default_factory=set)
    current_state: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "user": self.user,
            "role": self.role,
            "task": self.task,
            "permissions": list(self.permissions),
            "current_state": dict(self.current_state),
        }

    @staticmethod
    def from_dict(d: Dict[str, Any]) -> "ProjectionContext":
        return ProjectionContext(
            user=d.get("user", ""),
            role=d.get("role", ""),
            task=d.get("task", ""),
            permissions=set(d.get("permissions", [])),
            current_state=d.get("current_state", {}),
        )


@dataclass
class UIProjection:
    mode: UIMode
    application_id: str
    application_name: str = ""
    application_version: str = ""
    lifecycle: str = ""
    trust_level: str = ""
    capabilities: List[Dict[str, Any]] = field(default_factory=list)
    parameters: List[Dict[str, Any]] = field(default_factory=list)
    state: Dict[str, Any] = field(default_factory=dict)
    actions: List[Dict[str, Any]] = field(default_factory=list)
    events: List[Dict[str, Any]] = field(default_factory=list)
    projection_state: ProjectionState = ProjectionState.SYNCED
    last_sync_timestamp: float = 0.0
    filtered: bool = False
    filter_reason: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "mode": self.mode.value,
            "application_id": self.application_id,
            "application_name": self.application_name,
            "application_version": self.application_version,
            "lifecycle": self.lifecycle,
            "trust_level": self.trust_level,
            "capabilities": self.capabilities,
            "parameters": self.parameters,
            "state": self.state,
            "actions": self.actions,
            "events": self.events,
            "projection_state": self.projection_state.value,
            "last_sync_timestamp": self.last_sync_timestamp,
            "filtered": self.filtered,
            "filter_reason": self.filter_reason,
        }

    @staticmethod
    def from_dict(d: Dict[str, Any]) -> "UIProjection":
        return UIProjection(
            mode=UIMode(d.get("mode", "overlay")),
            application_id=d["application_id"],
            application_name=d.get("application_name", ""),
            application_version=d.get("application_version", ""),
            lifecycle=d.get("lifecycle", ""),
            trust_level=d.get("trust_level", ""),
            capabilities=d.get("capabilities", []),
            parameters=d.get("parameters", []),
            state=d.get("state", {}),
            actions=d.get("actions", []),
            events=d.get("events", []),
            projection_state=ProjectionState(d.get("projection_state", "synced")),
            last_sync_timestamp=d.get("last_sync_timestamp", 0.0),
            filtered=d.get("filtered", False),
            filter_reason=d.get("filter_reason", ""),
        )

    def mark_stale(self) -> None:
        self.projection_state = ProjectionState.STALE

    def mark_synced(self) -> None:
        self.projection_state = ProjectionState.SYNCED
        self.last_sync_timestamp = time.time()


class ProjectionEngine:
    def __init__(self, registry: AdapterRegistry):
        self._registry = registry
        self._cache: Dict[str, Dict[str, Any]] = {}

    def project(
        self,
        application_id: str,
        context: Optional[ProjectionContext] = None,
        mode: UIMode = UIMode.OVERLAY,
    ) -> UIProjection:
        context = context or ProjectionContext()
        adapter = self._registry.get(application_id)
        if adapter is None:
            return UIProjection(
                mode=mode,
                application_id=application_id,
                projection_state=ProjectionState.ERROR,
                filter_reason=f"adapter not found: {application_id}",
            )
        app = adapter.discover()
        return self._generate_projection(app, context, mode)

    def _generate_projection(
        self,
        app: SemanticApplication,
        context: ProjectionContext,
        mode: UIMode,
    ) -> UIProjection:
        has_permission = self._check_permissions(context)
        relevant_caps = self._filter_capabilities(app, context)
        relevant_params = self._filter_parameters(app, context)
        relevant_actions = self._filter_actions(app, context, relevant_caps)
        relevant_events = self._filter_events(app, context)

        state_dict: Dict[str, Any] = {}
        for sid, st in app.state.items():
            state_dict[sid] = {
                "id": st.id,
                "name": st.name,
                "type": st.type,
                "value": st.value,
                "source": st.source.value if hasattr(st.source, "value") else str(st.source),
                "version": st.version,
            }

        projection = UIProjection(
            mode=mode,
            application_id=app.id,
            application_name=app.name,
            application_version=app.version,
            lifecycle=app.lifecycle.value if hasattr(app.lifecycle, "value") else str(app.lifecycle),
            trust_level=app.trust_level.value if hasattr(app.trust_level, "value") else str(app.trust_level),
            capabilities=[c.to_dict() for c in relevant_caps.values()],
            parameters=[p.to_dict() for p in relevant_params.values()],
            state=state_dict,
            actions=[a.to_dict() for a in relevant_actions.values()],
            events=[e.to_dict() for e in relevant_events.values()],
            projection_state=ProjectionState.SYNCED,
            last_sync_timestamp=time.time(),
            filtered=len(relevant_caps) < len(app.capabilities),
            filter_reason="context-aware filtering applied" if len(relevant_caps) < len(app.capabilities) else "",
        )

        if mode == UIMode.NATIVE:
            projection.capabilities = []
            projection.parameters = []
            projection.actions = []
            projection.events = []
            projection.filtered = True
            projection.filter_reason = "native mode: minimal metadata only"

        return projection

    def _check_permissions(self, context: ProjectionContext) -> bool:
        return True

    def _filter_capabilities(
        self,
        app: SemanticApplication,
        context: ProjectionContext,
    ) -> Dict[str, Capability]:
        if not context.task:
            return app.capabilities
        if context.task.lower() in ["add", "calculate", "sum"]:
            return {k: v for k, v in app.capabilities.items() if "add" in k.lower()}
        return app.capabilities

    def _filter_parameters(
        self,
        app: SemanticApplication,
        context: ProjectionContext,
    ) -> Dict[str, Parameter]:
        if not context.task:
            return app.parameters
        relevant = {}
        for pid, param in app.parameters.items():
            relevant[pid] = param
        return relevant

    def _filter_actions(
        self,
        app: SemanticApplication,
        context: ProjectionContext,
        relevant_caps: Dict[str, Capability],
    ) -> Dict[str, Action]:
        cap_ids = set(relevant_caps.keys())
        return {k: v for k, v in app.actions.items() if v.capability_id in cap_ids}

    def _filter_events(
        self,
        app: SemanticApplication,
        context: ProjectionContext,
    ) -> Dict[str, Any]:
        return app.events

    def list_available_applications(self) -> List[Dict[str, Any]]:
        return self._registry.list()

    def invalidate_cache(self, application_id: Optional[str] = None) -> None:
        if application_id:
            self._cache.pop(application_id, None)
        else:
            self._cache.clear()
