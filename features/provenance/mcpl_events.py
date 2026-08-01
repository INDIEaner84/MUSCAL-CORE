from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

from features.identity.uuid7 import uuid7
from features.provenance.mcpl_schema import (
    MCPL_SCHEMA_VERSION,
    ProvenanceRecord,
    _now_iso,
)


# ---------------------------------------------------------------------------
# Event Type Registry
# ---------------------------------------------------------------------------

class MCPLEventType(str, Enum):
    INTENT_CREATED = "intent.created"
    INTENT_COMPLETED = "intent.completed"
    INTENT_FAILED = "intent.failed"
    INTENT_CANCELLED = "intent.cancelled"

    TASK_CREATED = "task.created"
    TASK_ASSIGNED = "task.assigned"
    TASK_COMPLETED = "task.completed"
    TASK_FAILED = "task.failed"
    TASK_CANCELLED = "task.cancelled"

    MODEL_INVOKED = "model.invoked"
    MODEL_OUTPUT = "model.output"

    DECISION_AGENT = "decision.agent"
    DECISION_POLICY = "decision.policy"
    DECISION_HUMAN = "decision.human"

    EXECUTION_AUTHORIZED = "execution.authorized"
    EXECUTION_STARTED = "execution.started"
    EXECUTION_COMPLETED = "execution.completed"
    EXECUTION_FAILED = "execution.failed"
    EXECUTION_RETRY = "execution.retry"
    EXECUTION_CANCELLED = "execution.cancelled"

    TOOL_CALL = "tool.call"
    TOOL_CALL_RESULT = "tool.call.result"

    ARTIFACT_CREATED = "artifact.created"
    ARTIFACT_MODIFIED = "artifact.modified"

    STATE_CHANGED = "state.changed"

    VERIFICATION_REQUESTED = "verification.requested"
    VERIFICATION_STARTED = "verification.started"
    VERIFICATION_RESULT = "verification.result"

    EXECUTION_JOIN = "execution.join"

    EXECUTION_REPLAY = "execution.replay"


# ---------------------------------------------------------------------------
# Event Type → Entity Mapping
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class EventMapping:
    event_type: MCPLEventType
    entity_type: str
    required_causal_parent: bool = False
    required_correlation_id: bool = True
    required_causation_id: bool = False
    payload_fields: Tuple[str, ...] = ()


_EVENT_MAPPINGS: Dict[MCPLEventType, EventMapping] = {
    MCPLEventType.INTENT_CREATED: EventMapping(
        event_type=MCPLEventType.INTENT_CREATED,
        entity_type="Intent",
        payload_fields=("description",),
    ),
    MCPLEventType.INTENT_COMPLETED: EventMapping(
        event_type=MCPLEventType.INTENT_COMPLETED,
        entity_type="Intent",
        required_causal_parent=True,
    ),
    MCPLEventType.INTENT_FAILED: EventMapping(
        event_type=MCPLEventType.INTENT_FAILED,
        entity_type="Intent",
        required_causal_parent=True,
        payload_fields=("error", "error_type"),
    ),
    MCPLEventType.INTENT_CANCELLED: EventMapping(
        event_type=MCPLEventType.INTENT_CANCELLED,
        entity_type="Intent",
        required_causal_parent=True,
    ),
    MCPLEventType.TASK_CREATED: EventMapping(
        event_type=MCPLEventType.TASK_CREATED,
        entity_type="Task",
        required_causal_parent=True,
        payload_fields=("description", "agent_id", "priority"),
    ),
    MCPLEventType.TASK_ASSIGNED: EventMapping(
        event_type=MCPLEventType.TASK_ASSIGNED,
        entity_type="Task",
        required_causal_parent=True,
        payload_fields=("agent_id",),
    ),
    MCPLEventType.TASK_COMPLETED: EventMapping(
        event_type=MCPLEventType.TASK_COMPLETED,
        entity_type="Task",
        required_causal_parent=True,
    ),
    MCPLEventType.TASK_FAILED: EventMapping(
        event_type=MCPLEventType.TASK_FAILED,
        entity_type="Task",
        required_causal_parent=True,
        payload_fields=("error", "error_type"),
    ),
    MCPLEventType.TASK_CANCELLED: EventMapping(
        event_type=MCPLEventType.TASK_CANCELLED,
        entity_type="Task",
        required_causal_parent=True,
    ),
    MCPLEventType.MODEL_INVOKED: EventMapping(
        event_type=MCPLEventType.MODEL_INVOKED,
        entity_type="Model",
        required_causal_parent=True,
        payload_fields=("model_id", "provider", "model_name", "temperature", "prompt_hash"),
    ),
    MCPLEventType.MODEL_OUTPUT: EventMapping(
        event_type=MCPLEventType.MODEL_OUTPUT,
        entity_type="ModelOutput",
        required_causal_parent=True,
        required_causation_id=True,
        payload_fields=("output_id", "candidates", "output_hash"),
    ),
    MCPLEventType.DECISION_AGENT: EventMapping(
        event_type=MCPLEventType.DECISION_AGENT,
        entity_type="AgentDecision",
        required_causal_parent=True,
        required_causation_id=True,
        payload_fields=("decision_id", "candidates", "selected", "selection_rationale"),
    ),
    MCPLEventType.DECISION_POLICY: EventMapping(
        event_type=MCPLEventType.DECISION_POLICY,
        entity_type="PolicyDecision",
        required_causal_parent=True,
        required_causation_id=True,
        payload_fields=("decision_id", "policy_id", "match_result", "rule_trace"),
    ),
    MCPLEventType.DECISION_HUMAN: EventMapping(
        event_type=MCPLEventType.DECISION_HUMAN,
        entity_type="HumanDecision",
        required_causal_parent=True,
        required_causation_id=True,
        payload_fields=("decision_id", "human_action", "human_id", "rationale"),
    ),
    MCPLEventType.EXECUTION_AUTHORIZED: EventMapping(
        event_type=MCPLEventType.EXECUTION_AUTHORIZED,
        entity_type="ExecutionAuthorization",
        required_causal_parent=True,
        payload_fields=("authorization_id", "authorization_type"),
    ),
    MCPLEventType.EXECUTION_STARTED: EventMapping(
        event_type=MCPLEventType.EXECUTION_STARTED,
        entity_type="Execution",
        required_causal_parent=True,
        payload_fields=("execution_id", "tool_name"),
    ),
    MCPLEventType.EXECUTION_COMPLETED: EventMapping(
        event_type=MCPLEventType.EXECUTION_COMPLETED,
        entity_type="Execution",
        required_causal_parent=True,
        payload_fields=("execution_id", "duration_ms", "success"),
    ),
    MCPLEventType.EXECUTION_FAILED: EventMapping(
        event_type=MCPLEventType.EXECUTION_FAILED,
        entity_type="Execution",
        required_causal_parent=True,
        payload_fields=("execution_id", "error", "error_type"),
    ),
    MCPLEventType.EXECUTION_RETRY: EventMapping(
        event_type=MCPLEventType.EXECUTION_RETRY,
        entity_type="Execution",
        required_causal_parent=True,
        payload_fields=("execution_id", "attempt_number", "retry_policy"),
    ),
    MCPLEventType.EXECUTION_CANCELLED: EventMapping(
        event_type=MCPLEventType.EXECUTION_CANCELLED,
        entity_type="Execution",
        required_causal_parent=True,
        payload_fields=("execution_id",),
    ),
    MCPLEventType.TOOL_CALL: EventMapping(
        event_type=MCPLEventType.TOOL_CALL,
        entity_type="ToolCall",
        required_causal_parent=True,
        payload_fields=("tool_call_id", "tool_name", "args_hash"),
    ),
    MCPLEventType.TOOL_CALL_RESULT: EventMapping(
        event_type=MCPLEventType.TOOL_CALL_RESULT,
        entity_type="ToolCall",
        required_causal_parent=True,
        required_causation_id=True,
        payload_fields=("tool_call_id", "result_hash", "success", "duration_ms"),
    ),
    MCPLEventType.ARTIFACT_CREATED: EventMapping(
        event_type=MCPLEventType.ARTIFACT_CREATED,
        entity_type="Artifact",
        required_causal_parent=True,
        payload_fields=("artifact_id", "name", "content_hash", "mime_type"),
    ),
    MCPLEventType.ARTIFACT_MODIFIED: EventMapping(
        event_type=MCPLEventType.ARTIFACT_MODIFIED,
        entity_type="Artifact",
        required_causal_parent=True,
        required_causation_id=True,
        payload_fields=("artifact_id", "previous_hash", "current_hash"),
    ),
    MCPLEventType.STATE_CHANGED: EventMapping(
        event_type=MCPLEventType.STATE_CHANGED,
        entity_type="State",
        required_causal_parent=True,
        payload_fields=("state_id", "artifact_id", "previous_hash", "current_hash", "scope"),
    ),
    MCPLEventType.VERIFICATION_REQUESTED: EventMapping(
        event_type=MCPLEventType.VERIFICATION_REQUESTED,
        entity_type="Verification",
        required_causal_parent=True,
        payload_fields=("verification_id", "subject_id", "subject_type", "verifier_type"),
    ),
    MCPLEventType.VERIFICATION_STARTED: EventMapping(
        event_type=MCPLEventType.VERIFICATION_STARTED,
        entity_type="Verification",
        required_causal_parent=True,
        required_causation_id=True,
        payload_fields=("verification_id", "method"),
    ),
    MCPLEventType.VERIFICATION_RESULT: EventMapping(
        event_type=MCPLEventType.VERIFICATION_RESULT,
        entity_type="Verification",
        required_causal_parent=True,
        required_causation_id=True,
        payload_fields=("verification_id", "status", "confidence", "evidence_ref"),
    ),
    MCPLEventType.EXECUTION_JOIN: EventMapping(
        event_type=MCPLEventType.EXECUTION_JOIN,
        entity_type="Join",
        required_causal_parent=True,
        payload_fields=("join_id", "condition", "branch_ids", "completed_branches"),
    ),
    MCPLEventType.EXECUTION_REPLAY: EventMapping(
        event_type=MCPLEventType.EXECUTION_REPLAY,
        entity_type="Execution",
        required_correlation_id=True,
        required_causation_id=True,
        payload_fields=("execution_id", "replay_of", "replay_classification"),
    ),
}


def get_event_mapping(event_type: MCPLEventType) -> Optional[EventMapping]:
    return _EVENT_MAPPINGS.get(event_type)


def validate_event_mapping(record: ProvenanceRecord) -> List[str]:
    errors: List[str] = []
    try:
        event_type = MCPLEventType(record.event_type)
    except ValueError:
        errors.append(f"Unknown event_type: {record.event_type}")
        return errors

    mapping = _EVENT_MAPPINGS[event_type]
    if mapping.required_causal_parent and not record.parent_id:
        errors.append(f"Event {record.event_type} requires parent_id")
    if mapping.required_correlation_id and not record.correlation_id:
        errors.append(f"Event {record.event_type} requires correlation_id")
    if mapping.required_causation_id and not record.causation_id:
        errors.append(f"Event {record.event_type} requires causation_id")
    return errors


# ---------------------------------------------------------------------------
# Event Factory
# ---------------------------------------------------------------------------

def create_provenance_event(
    event_type: MCPLEventType,
    *,
    parent_id: str = "",
    causation_id: str = "",
    correlation_id: str = "",
    tenant_id: str = "",
    actor: Optional[Dict[str, Any]] = None,
    subject: Optional[Dict[str, Any]] = None,
    causal_links: Optional[List[Dict[str, Any]]] = None,
    payload: Optional[Dict[str, Any]] = None,
    integrity: Optional[Dict[str, Any]] = None,
    retention: Optional[Dict[str, Any]] = None,
) -> ProvenanceRecord:
    record = ProvenanceRecord(
        event_type=event_type.value,
        parent_id=parent_id,
        causation_id=causation_id,
        correlation_id=correlation_id,
        tenant_id=tenant_id,
        actor=actor or {},
        subject=subject or {},
        causal_links=causal_links or [],
        payload=payload or {},
        integrity=integrity or {},
        retention=retention or {},
    )
    return record


# ---------------------------------------------------------------------------
# Pre-defined retention policies
# ---------------------------------------------------------------------------

RETENTION_7_DAYS = {"ttl_days": 7, "legal_hold": False, "crypto_shreddable": True}
RETENTION_30_DAYS = {"ttl_days": 30, "legal_hold": False, "crypto_shreddable": True}
RETENTION_90_DAYS = {"ttl_days": 90, "legal_hold": False, "crypto_shreddable": True}
RETENTION_1_YEAR = {"ttl_days": 365, "legal_hold": False, "crypto_shreddable": True}
RETENTION_LEGAL_HOLD = {"ttl_days": 3650, "legal_hold": True, "crypto_shreddable": False}
