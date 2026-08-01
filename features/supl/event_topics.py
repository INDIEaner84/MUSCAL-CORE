from __future__ import annotations
from typing import Dict, Any

SUPL_APPLICATION_REGISTERED = "supl.application.registered"
SUPL_APPLICATION_UPDATED = "supl.application.updated"
SUPL_APPLICATION_REMOVED = "supl.application.removed"

SUPL_ACTION_REQUESTED = "supl.action.requested"
SUPL_ACTION_AUTHORIZED = "supl.action.authorized"
SUPL_ACTION_REJECTED = "supl.action.rejected"

SUPL_INTERACTION_CREATED = "supl.interaction.created"
SUPL_INTERACTION_UPDATED = "supl.interaction.updated"

SUPL_EXECUTION_LINKED = "supl.execution.linked"
SUPL_EXECUTION_COMPLETED = "supl.execution.completed"
SUPL_EXECUTION_FAILED = "supl.execution.failed"

SUPL_PROVENANCE_LINKED = "supl.provenance.linked"

SUPL_TOPICS: Dict[str, Dict[str, Any]] = {
    SUPL_APPLICATION_REGISTERED: {
        "producer": "adapter_registry",
        "consumer": "projection_engine",
        "authoritative_source": "registry",
        "payload_schema": {"application_id": "str", "name": "str", "version": "str"},
        "persist": True,
    },
    SUPL_APPLICATION_UPDATED: {
        "producer": "adapter_registry",
        "consumer": "projection_engine",
        "authoritative_source": "registry",
        "payload_schema": {"application_id": "str", "name": "str", "version": "str"},
        "persist": True,
    },
    SUPL_APPLICATION_REMOVED: {
        "producer": "adapter_registry",
        "consumer": "graph_projection_engine",
        "authoritative_source": "registry",
        "payload_schema": {"application_id": "str"},
        "persist": True,
    },
    SUPL_ACTION_REQUESTED: {
        "producer": "ui_projection",
        "consumer": "safety_gate",
        "authoritative_source": "ui",
        "payload_schema": {"interaction_id": "str", "application_id": "str", "capability_id": "str", "action_id": "str"},
        "persist": True,
    },
    SUPL_ACTION_AUTHORIZED: {
        "producer": "safety_gate",
        "consumer": "execution_router",
        "authoritative_source": "safety",
        "payload_schema": {"interaction_id": "str", "allowed": "bool"},
        "persist": True,
    },
    SUPL_ACTION_REJECTED: {
        "producer": "safety_gate",
        "consumer": "ui_projection",
        "authoritative_source": "safety",
        "payload_schema": {"interaction_id": "str", "reason": "str"},
        "persist": True,
    },
    SUPL_INTERACTION_CREATED: {
        "producer": "ui_projection",
        "consumer": "provenance_store",
        "authoritative_source": "ui",
        "payload_schema": {"interaction_id": "str"},
        "persist": True,
    },
    SUPL_INTERACTION_UPDATED: {
        "producer": "provenance_store",
        "consumer": "ui_projection",
        "authoritative_source": "provenance",
        "payload_schema": {"interaction_id": "str", "status": "str"},
        "persist": True,
    },
    SUPL_EXECUTION_LINKED: {
        "producer": "execution_router",
        "consumer": "provenance_store",
        "authoritative_source": "runtime",
        "payload_schema": {"interaction_id": "str", "execution_id": "str"},
        "persist": True,
    },
    SUPL_EXECUTION_COMPLETED: {
        "producer": "unified_tool_runtime",
        "consumer": "provenance_store",
        "authoritative_source": "runtime",
        "payload_schema": {"execution_id": "str", "success": "bool", "receipt_id": "str"},
        "persist": True,
    },
    SUPL_EXECUTION_FAILED: {
        "producer": "unified_tool_runtime",
        "consumer": "provenance_store",
        "authoritative_source": "runtime",
        "payload_schema": {"execution_id": "str", "error": "str"},
        "persist": True,
    },
    SUPL_PROVENANCE_LINKED: {
        "producer": "provenance_store",
        "consumer": "projection_engine",
        "authoritative_source": "provenance",
        "payload_schema": {"interaction_id": "str", "execution_id": "str", "receipt_id": "str"},
        "persist": True,
    },
}
