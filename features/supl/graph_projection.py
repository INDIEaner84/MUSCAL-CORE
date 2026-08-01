from __future__ import annotations
import time
from typing import Any, Dict, List, Optional, Set

from features.supl.semantic_model import (
    SemanticApplication, Capability, Parameter, Action,
    ApplicationState, EventDefinition,
)
from features.supl.adapter_registry import AdapterRegistry
from features.supl.graph_boundary import (
    NODE_TYPE_APPLICATION,
    NODE_TYPE_CAPABILITY,
    NODE_TYPE_PARAMETER,
    NODE_TYPE_ACTION,
    NODE_TYPE_STATE,
    NODE_TYPE_EVENT,
    EDGE_TYPE_HAS_CAPABILITY,
    EDGE_TYPE_HAS_PARAMETER,
    EDGE_TYPE_HAS_ACTION,
    EDGE_TYPE_HAS_STATE,
    EDGE_TYPE_HAS_EVENT,
    EDGE_TYPE_SUPPORTS_ACTION,
    EDGE_TYPE_USES_PARAMETER,
    SUPL_NODE_TYPES,
)

GRAPH_PROJECTION_VERSION = "supl.graph.v1"
SOURCE_AUTHORITY = "SUPL_SEMANTIC_MODEL"

EVIDENCE_DECLARED = "DECLARED"
EVIDENCE_DISCOVERED = "DISCOVERED"
EVIDENCE_PROJECTED = "PROJECTED"
EVIDENCE_SIMULATED = "SIMULATED"
EVIDENCE_EXECUTED = "EXECUTED"
EVIDENCE_VERIFIED = "VERIFIED"

LIFECYCLE_REGISTERED = "REGISTERED"
LIFECYCLE_PROJECTED = "PROJECTED"
LIFECYCLE_UPDATED = "UPDATED"
LIFECYCLE_REPROJECTED = "REPROJECTED"
LIFECYCLE_REMOVED = "REMOVED"


def _supl_node_id(entity_type: str, application_id: str, entity_id: str) -> str:
    return f"supl:{entity_type}:{application_id}:{entity_id}"


def _build_semantic_source(application_id: str, entity_id: str, entity_type: str) -> Dict[str, str]:
    return {
        "application_id": application_id,
        "entity_id": entity_id,
        "entity_type": entity_type,
    }


def _build_projection_metadata(entity_type: str, application_id: str, entity_id: str) -> Dict[str, Any]:
    return {
        "semantic_source": _build_semantic_source(application_id, entity_id, entity_type),
        "projection_id": GRAPH_PROJECTION_VERSION,
        "projection_version": 1,
        "source_authority": SOURCE_AUTHORITY,
    }


class GraphProjectionEngine:
    def __init__(self, registry: AdapterRegistry, store: Any):
        self._registry = registry
        self._store = store
        self._projected_apps: Set[str] = set()
        self._lifecycle: Dict[str, str] = {}

    def project_application(self, application_id: str) -> Dict[str, Any]:
        adapter = self._registry.get(application_id)
        if adapter is None:
            raise ValueError(f"adapter not found: {application_id}")
        app = adapter.discover()
        return self._project(app)

    def project_adapter(self, adapter: Any) -> Dict[str, Any]:
        app = adapter.discover()
        return self._project(app)

    def sync_application(self, application_id: str) -> Dict[str, Any]:
        self.remove_application(application_id)
        return self.project_application(application_id)

    def remove_application(self, application_id: str) -> int:
        removed = 0
        node_ids_to_remove = [
            nid for nid in list(self._store.nodes.keys())
            if self._is_supl_node(nid, application_id)
        ]
        for nid in node_ids_to_remove:
            self._remove_node_with_edges(nid)
            removed += 1
        self._projected_apps.discard(application_id)
        self._lifecycle[application_id] = LIFECYCLE_REMOVED
        return removed

    def get_lifecycle(self, application_id: str) -> str:
        return self._lifecycle.get(application_id, "")

    def get_projected_apps(self) -> Set[str]:
        return set(self._projected_apps)

    def reset(self) -> None:
        supl_node_ids = [
            nid for nid in list(self._store.nodes.keys())
            if nid.startswith("supl:")
        ]
        for nid in supl_node_ids:
            self._remove_node_with_edges(nid)
        self._projected_apps.clear()
        self._lifecycle.clear()

    def _project(self, app: SemanticApplication) -> Dict[str, Any]:
        app_id = app.id
        result = {"nodes": [], "edges": []}

        app_node_id = _supl_node_id("app", app_id, app_id)
        app_metadata = _build_projection_metadata("APPLICATION", app_id, app_id)
        app_metadata["application_name"] = app.name
        app_metadata["application_version"] = app.version
        app_metadata["lifecycle"] = app.lifecycle.value if hasattr(app.lifecycle, "value") else str(app.lifecycle)
        app_metadata["trust_level"] = app.trust_level.value if hasattr(app.trust_level, "value") else str(app.trust_level)

        app_payload = {
            "id": app_id,
            "name": app.name,
            "version": app.version,
            "lifecycle": app.lifecycle.value if hasattr(app.lifecycle, "value") else str(app.lifecycle),
            "trust_level": app.trust_level.value if hasattr(app.trust_level, "value") else str(app.trust_level),
        }

        app_evidence = {
            "semantic_state": str(app.lifecycle.value) if hasattr(app.lifecycle, "value") else str(app.lifecycle),
            "projection_state": "SYNCED",
            "runtime_state": "AVAILABLE" if app.lifecycle.value == "active" else "UNAVAILABLE",
            "execution_state": "NONE",
            "provenance_state": "NONE",
            "evidence_classification": EVIDENCE_PROJECTED,
        }
        app_payload.update(app_evidence)
        app_payload["metadata"] = app_metadata

        self._upsert_node(app_node_id, NODE_TYPE_APPLICATION, app_payload)
        result["nodes"].append({"id": app_node_id, "type": NODE_TYPE_APPLICATION})

        for cap_id, cap in app.capabilities.items():
            cap_node_id = _supl_node_id("cap", app_id, cap_id)
            cap_metadata = _build_projection_metadata("CAPABILITY", app_id, cap_id)
            cap_metadata[app_node_id] = app_node_id

            cap_payload = {
                "id": cap.id,
                "name": cap.name,
                "description": cap.description,
                "risk_level": cap.risk_level.value if hasattr(cap.risk_level, "value") else str(cap.risk_level),
                "execution_mode": cap.execution_mode.value if hasattr(cap.execution_mode, "value") else str(cap.execution_mode),
                "tool_name": cap.tool_name,
                "evidence_classification": EVIDENCE_PROJECTED,
                "metadata": cap_metadata,
            }

            self._upsert_node(cap_node_id, NODE_TYPE_CAPABILITY, cap_payload)
            result["nodes"].append({"id": cap_node_id, "type": NODE_TYPE_CAPABILITY})
            self._upsert_edge(app_node_id, cap_node_id, EDGE_TYPE_HAS_CAPABILITY, {})
            result["edges"].append({"from": app_node_id, "to": cap_node_id, "type": EDGE_TYPE_HAS_CAPABILITY})

            cap_actions = [a for a in app.actions.values() if a.capability_id == cap_id]
            for act in cap_actions:
                act_node_id = _supl_node_id("act", app_id, act.id)
                act_metadata = _build_projection_metadata("ACTION", app_id, act.id)
                act_metadata["capability_id"] = cap_id

                act_payload = {
                    "id": act.id,
                    "capability_id": act.capability_id,
                    "name": act.name or act.id,
                    "parameter_ids": list(act.parameter_ids),
                    "authorization_required": act.authorization_required,
                    "evidence_classification": EVIDENCE_PROJECTED,
                    "metadata": act_metadata,
                }

                self._upsert_node(act_node_id, NODE_TYPE_ACTION, act_payload)
                result["nodes"].append({"id": act_node_id, "type": NODE_TYPE_ACTION})
                self._upsert_edge(cap_node_id, act_node_id, EDGE_TYPE_SUPPORTS_ACTION, {})
                result["edges"].append({"from": cap_node_id, "to": act_node_id, "type": EDGE_TYPE_SUPPORTS_ACTION})

                for pid in act.parameter_ids:
                    param = app.parameters.get(pid)
                    if param is not None:
                        param_node_id = _supl_node_id("param", app_id, param.id)
                        param_metadata = _build_projection_metadata("PARAMETER", app_id, param.id)

                        param_payload = {
                            "id": param.id,
                            "name": param.name,
                            "type": param.type,
                            "required": param.required,
                            "evidence_classification": EVIDENCE_PROJECTED,
                            "metadata": param_metadata,
                        }

                        self._upsert_node(param_node_id, NODE_TYPE_PARAMETER, param_payload)
                        result["nodes"].append({"id": param_node_id, "type": NODE_TYPE_PARAMETER})
                        self._upsert_edge(act_node_id, param_node_id, EDGE_TYPE_USES_PARAMETER, {})
                        result["edges"].append({"from": act_node_id, "to": param_node_id, "type": EDGE_TYPE_USES_PARAMETER})

        for param_id, param in app.parameters.items():
            param_node_id = _supl_node_id("param", app_id, param.id)
            param_metadata = _build_projection_metadata("PARAMETER", app_id, param.id)

            param_payload = {
                "id": param.id,
                "name": param.name,
                "type": param.type,
                "required": param.required,
                "evidence_classification": EVIDENCE_PROJECTED,
                "metadata": param_metadata,
            }

            self._upsert_node(param_node_id, NODE_TYPE_PARAMETER, param_payload)
            result["nodes"].append({"id": param_node_id, "type": NODE_TYPE_PARAMETER})
            self._upsert_edge(app_node_id, param_node_id, EDGE_TYPE_HAS_PARAMETER, {})
            result["edges"].append({"from": app_node_id, "to": param_node_id, "type": EDGE_TYPE_HAS_PARAMETER})

        for state_id, st in app.state.items():
            state_node_id = _supl_node_id("state", app_id, state_id)
            state_metadata = _build_projection_metadata("STATE", app_id, state_id)

            state_payload = {
                "id": st.id,
                "name": st.name,
                "type": st.type,
                "value": st.value,
                "source": st.source.value if hasattr(st.source, "value") else str(st.source),
                "version": st.version,
                "evidence_classification": EVIDENCE_PROJECTED,
                "metadata": state_metadata,
            }

            self._upsert_node(state_node_id, NODE_TYPE_STATE, state_payload)
            result["nodes"].append({"id": state_node_id, "type": NODE_TYPE_STATE})
            self._upsert_edge(app_node_id, state_node_id, EDGE_TYPE_HAS_STATE, {})
            result["edges"].append({"from": app_node_id, "to": state_node_id, "type": EDGE_TYPE_HAS_STATE})

        for evt_id, evt in app.events.items():
            evt_node_id = _supl_node_id("evt", app_id, evt_id)
            evt_metadata = _build_projection_metadata("EVENT", app_id, evt_id)

            evt_payload = {
                "id": evt.id,
                "name": evt.name,
                "evidence_classification": EVIDENCE_PROJECTED,
                "metadata": evt_metadata,
            }

            self._upsert_node(evt_node_id, NODE_TYPE_EVENT, evt_payload)
            result["nodes"].append({"id": evt_node_id, "type": NODE_TYPE_EVENT})
            self._upsert_edge(app_node_id, evt_node_id, EDGE_TYPE_HAS_EVENT, {})
            result["edges"].append({"from": app_node_id, "to": evt_node_id, "type": EDGE_TYPE_HAS_EVENT})

        self._projected_apps.add(app_id)
        was = self._lifecycle.get(app_id, "")
        if was == LIFECYCLE_REMOVED:
            self._lifecycle[app_id] = LIFECYCLE_REPROJECTED
        elif was == LIFECYCLE_PROJECTED:
            self._lifecycle[app_id] = LIFECYCLE_UPDATED
        else:
            self._lifecycle[app_id] = LIFECYCLE_PROJECTED

        return result

    def _upsert_node(self, node_id: str, node_type: str, payload: Dict[str, Any]) -> None:
        existing = self._store.nodes.get(node_id)
        if existing:
            existing["type"] = node_type
            existing["payload"] = payload
        else:
            self._store.nodes[node_id] = {
                "id": node_id,
                "type": node_type,
                "payload": payload,
            }

    def _upsert_edge(self, source_id: str, target_id: str, edge_type: str, payload: Dict[str, Any]) -> None:
        for edge in self._store.edges:
            if (edge.get("source_id") == source_id
                    and edge.get("target_id") == target_id
                    and edge.get("edge_type") == edge_type):
                edge["payload"] = payload
                return
        self._store.edges.append({
            "source_id": source_id,
            "target_id": target_id,
            "edge_type": edge_type,
            "payload": payload,
        })

    def _is_supl_node(self, node_id: str, application_id: str) -> bool:
        if not node_id.startswith("supl:"):
            return False
        parts = node_id.split(":")
        if len(parts) < 3:
            return False
        if application_id is not None:
            return parts[2] == application_id
        return True

    def _remove_node_with_edges(self, node_id: str) -> None:
        if node_id in self._store.nodes:
            del self._store.nodes[node_id]
        self._store.edges[:] = [
            e for e in self._store.edges
            if e.get("source_id") != node_id and e.get("target_id") != node_id
        ]
