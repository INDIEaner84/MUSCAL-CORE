from __future__ import annotations
from typing import Dict, Any

NODE_TYPE_APPLICATION = "APPLICATION"
NODE_TYPE_CAPABILITY = "CAPABILITY"
NODE_TYPE_PARAMETER = "PARAMETER"
NODE_TYPE_ACTION = "ACTION"
NODE_TYPE_STATE = "STATE"
NODE_TYPE_EVENT = "EVENT"
NODE_TYPE_UI_INTERACTION = "UI_INTERACTION"
NODE_TYPE_EXECUTION = "EXECUTION"
NODE_TYPE_PROVENANCE = "PROVENANCE"

EDGE_TYPE_PROJECTS_TO = "PROJECTS_TO"
EDGE_TYPE_HAS_CAPABILITY = "HAS_CAPABILITY"
EDGE_TYPE_HAS_PARAMETER = "HAS_PARAMETER"
EDGE_TYPE_HAS_ACTION = "HAS_ACTION"
EDGE_TYPE_HAS_STATE = "HAS_STATE"
EDGE_TYPE_HAS_EVENT = "HAS_EVENT"
EDGE_TYPE_TRIGGERED_BY = "TRIGGERED_BY"
EDGE_TYPE_SUPPORTS_ACTION = "SUPPORTS_ACTION"
EDGE_TYPE_USES_PARAMETER = "USES_PARAMETER"
EDGE_TYPE_HAS_EXECUTION = "HAS_EXECUTION"
EDGE_TYPE_HAS_PROVENANCE = "HAS_PROVENANCE"

SUPL_NODE_TYPES = frozenset({
    NODE_TYPE_APPLICATION,
    NODE_TYPE_CAPABILITY,
    NODE_TYPE_PARAMETER,
    NODE_TYPE_ACTION,
    NODE_TYPE_STATE,
    NODE_TYPE_EVENT,
    NODE_TYPE_UI_INTERACTION,
    NODE_TYPE_EXECUTION,
    NODE_TYPE_PROVENANCE,
})

SUPL_EDGE_TYPES = frozenset({
    EDGE_TYPE_PROJECTS_TO,
    EDGE_TYPE_HAS_CAPABILITY,
    EDGE_TYPE_HAS_PARAMETER,
    EDGE_TYPE_HAS_ACTION,
    EDGE_TYPE_HAS_STATE,
    EDGE_TYPE_HAS_EVENT,
    EDGE_TYPE_TRIGGERED_BY,
    EDGE_TYPE_SUPPORTS_ACTION,
    EDGE_TYPE_USES_PARAMETER,
    EDGE_TYPE_HAS_EXECUTION,
    EDGE_TYPE_HAS_PROVENANCE,
})

GRAPH_PROJECTION_NOTE = (
    "GraphState Node Types for Semantic UI Projection Layer (MSUPL-001). "
    "These node types represent a PROJECTION of the Semantic Application Model "
    "into the GraphState graph. GraphState is NOT the authoritative source of "
    "semantic application truth. "
    "Architecture: SemanticApplication (features/supl/semantic_model.py) "
    "-> Graph Projection (graph.py nodes/edges), Overlay Projection, Graph-Native. "
    "All projections derive from the same canonical SemanticApplication model. "
    "GraphState must never become the authoritative source."
)

APPLICATION_TO_GRAPH_MAPPING: Dict[str, str] = {
    "application": NODE_TYPE_APPLICATION,
    "capability": NODE_TYPE_CAPABILITY,
    "parameter": NODE_TYPE_PARAMETER,
    "action": NODE_TYPE_ACTION,
    "state": NODE_TYPE_STATE,
    "event": NODE_TYPE_EVENT,
}

GRAPH_TO_APPLICATION_MAPPING: Dict[str, str] = {
    v: k for k, v in APPLICATION_TO_GRAPH_MAPPING.items()
}
