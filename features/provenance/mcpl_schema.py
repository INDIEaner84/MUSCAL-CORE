from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

from features.identity.uuid7 import uuid7

MCPL_SCHEMA_VERSION = "1.0.0"


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class DecisionType(str, Enum):
    MODEL_OUTPUT = "model_output"
    AGENT_DECISION = "agent_decision"
    POLICY_DECISION = "policy_decision"
    HUMAN_DECISION = "human_decision"


class HumanAction(str, Enum):
    APPROVE = "approve"
    REJECT = "reject"
    OVERRIDE = "override"
    MODIFY = "modify"


class ExecutionStatus(str, Enum):
    REQUESTED = "requested"
    AUTHORIZED = "authorized"
    STARTED = "started"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    RETRYING = "retrying"


class AttemptStatus(str, Enum):
    STARTED = "started"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    TIMED_OUT = "timed_out"


class VerificationStatus(str, Enum):
    REQUESTED = "requested"
    RUNNING = "running"
    PASSED = "passed"
    FAILED = "failed"
    INCONCLUSIVE = "inconclusive"
    OVERRIDDEN = "overridden"


class VerifierType(str, Enum):
    DETERMINISTIC = "deterministic"
    SCHEMA = "schema"
    INVARIANT = "invariant"
    RULE_ENGINE = "rule_engine"
    CRYPTOGRAPHIC = "cryptographic"
    SIMULATION = "simulation"
    MODEL_CRITIC = "model_critic"
    INDEPENDENT_MODEL = "independent_model"
    HUMAN = "human"


class VerificationTarget(str, Enum):
    EXECUTION = "execution"
    ATTEMPT = "attempt"
    ARTIFACT = "artifact"
    STATE = "state"


class JoinCondition(str, Enum):
    ALL = "all"
    ANY = "any"
    QUORUM = "quorum"
    THRESHOLD = "threshold"
    TIMEOUT = "timeout"
    BEST_EFFORT = "best_effort"


class ReplayClassification(str, Enum):
    REPLAYABLE = "replayable"
    PARTIALLY_REPLAYABLE = "partially_replayable"
    NON_REPLAYABLE = "non_replayable"


class ArtifactType(str, Enum):
    FILE = "file"
    MEMORY = "memory"
    DB_ROW = "db_row"
    API_RESPONSE = "api_response"
    SCREENSHOT = "screenshot"


class StateType(str, Enum):
    CREATED = "created"
    MODIFIED = "modified"
    DELETED = "deleted"


class IntentStatus(str, Enum):
    CREATED = "created"
    DECOMPOSED = "decomposed"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TaskStatus(str, Enum):
    CREATED = "created"
    ASSIGNED = "assigned"
    EXECUTING = "executing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class AgentType(str, Enum):
    LLM = "llm"
    RULE_BASED = "rule_based"
    HUMAN = "human"
    HYBRID = "hybrid"


# ---------------------------------------------------------------------------
# Execution status transitions
# ---------------------------------------------------------------------------

_VALID_EXECUTION_STATUS_TRANSITIONS: Dict[str, frozenset] = {
    ExecutionStatus.REQUESTED.value: frozenset({ExecutionStatus.AUTHORIZED.value}),
    ExecutionStatus.AUTHORIZED.value: frozenset({ExecutionStatus.STARTED.value, ExecutionStatus.CANCELLED.value}),
    ExecutionStatus.STARTED.value: frozenset({ExecutionStatus.RUNNING.value, ExecutionStatus.FAILED.value, ExecutionStatus.CANCELLED.value}),
    ExecutionStatus.RUNNING.value: frozenset({ExecutionStatus.COMPLETED.value, ExecutionStatus.FAILED.value, ExecutionStatus.RETRYING.value}),
    ExecutionStatus.RETRYING.value: frozenset({ExecutionStatus.RUNNING.value, ExecutionStatus.FAILED.value}),
    ExecutionStatus.COMPLETED.value: frozenset(),
    ExecutionStatus.FAILED.value: frozenset({ExecutionStatus.RETRYING.value}),
    ExecutionStatus.CANCELLED.value: frozenset(),
}

_VALID_ATTEMPT_STATUS_TRANSITIONS: Dict[str, frozenset] = {
    AttemptStatus.STARTED.value: frozenset({AttemptStatus.RUNNING.value}),
    AttemptStatus.RUNNING.value: frozenset({AttemptStatus.COMPLETED.value, AttemptStatus.FAILED.value, AttemptStatus.TIMED_OUT.value}),
    AttemptStatus.COMPLETED.value: frozenset(),
    AttemptStatus.FAILED.value: frozenset(),
    AttemptStatus.TIMED_OUT.value: frozenset(),
}

_VALID_VERIFICATION_STATUS_TRANSITIONS: Dict[str, frozenset] = {
    VerificationStatus.REQUESTED.value: frozenset({VerificationStatus.RUNNING.value}),
    VerificationStatus.RUNNING.value: frozenset({VerificationStatus.PASSED.value, VerificationStatus.FAILED.value, VerificationStatus.INCONCLUSIVE.value}),
    VerificationStatus.PASSED.value: frozenset({VerificationStatus.OVERRIDDEN.value}),
    VerificationStatus.FAILED.value: frozenset({VerificationStatus.OVERRIDDEN.value}),
    VerificationStatus.INCONCLUSIVE.value: frozenset({VerificationStatus.RUNNING.value}),
    VerificationStatus.OVERRIDDEN.value: frozenset(),
}


def validate_execution_status_transition(current: str, target: str) -> bool:
    allowed = _VALID_EXECUTION_STATUS_TRANSITIONS.get(current)
    if allowed is None:
        return False
    return target in allowed


def validate_attempt_status_transition(current: str, target: str) -> bool:
    allowed = _VALID_ATTEMPT_STATUS_TRANSITIONS.get(current)
    if allowed is None:
        return False
    return target in allowed


def validate_verification_status_transition(current: str, target: str) -> bool:
    allowed = _VALID_VERIFICATION_STATUS_TRANSITIONS.get(current)
    if allowed is None:
        return False
    return target in allowed


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


# ---------------------------------------------------------------------------
# Entity dataclasses
# ---------------------------------------------------------------------------

@dataclass
class Intent:
    intent_id: str = field(default_factory=uuid7)
    description: str = ""
    created_at: str = field(default_factory=_now_iso)
    correlation_id: str = ""
    causation_id: str = ""
    tenant_id: str = ""
    status: str = IntentStatus.CREATED.value
    metadata: Dict[str, Any] = field(default_factory=dict)
    task_ids: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "intent_id": self.intent_id,
            "description": self.description,
            "created_at": self.created_at,
            "correlation_id": self.correlation_id,
            "causation_id": self.causation_id,
            "tenant_id": self.tenant_id,
            "status": self.status,
            "metadata": self.metadata,
            "task_ids": self.task_ids,
        }


@dataclass
class Task:
    task_id: str = field(default_factory=uuid7)
    intent_id: str = ""
    description: str = ""
    created_at: str = field(default_factory=_now_iso)
    correlation_id: str = ""
    causation_id: str = ""
    tenant_id: str = ""
    status: str = TaskStatus.CREATED.value
    priority: int = 100
    metadata: Dict[str, Any] = field(default_factory=dict)
    agent_id: str = ""
    execution_ids: List[str] = field(default_factory=list)
    join_id: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "task_id": self.task_id,
            "intent_id": self.intent_id,
            "description": self.description,
            "created_at": self.created_at,
            "correlation_id": self.correlation_id,
            "causation_id": self.causation_id,
            "tenant_id": self.tenant_id,
            "status": self.status,
            "priority": self.priority,
            "metadata": self.metadata,
            "agent_id": self.agent_id,
            "execution_ids": self.execution_ids,
            "join_id": self.join_id,
        }


@dataclass
class Agent:
    agent_id: str = field(default_factory=uuid7)
    name: str = ""
    version: str = "1.0.0"
    agent_type: str = AgentType.LLM.value
    created_at: str = field(default_factory=_now_iso)
    tenant_id: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "agent_id": self.agent_id,
            "name": self.name,
            "version": self.version,
            "agent_type": self.agent_type,
            "created_at": self.created_at,
            "tenant_id": self.tenant_id,
        }


@dataclass
class Model:
    model_id: str = field(default_factory=uuid7)
    provider: str = ""
    model_name: str = ""
    model_version: str = ""
    created_at: str = field(default_factory=_now_iso)
    temperature: float = 0.0
    top_p: float = 1.0
    seed: Optional[int] = None
    sampling_parameters: Dict[str, Any] = field(default_factory=dict)
    system_prompt_hash: str = ""
    runtime_environment: Dict[str, Any] = field(default_factory=dict)
    tool_versions: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "model_id": self.model_id,
            "provider": self.provider,
            "model_name": self.model_name,
            "model_version": self.model_version,
            "created_at": self.created_at,
            "temperature": self.temperature,
            "top_p": self.top_p,
            "seed": self.seed,
            "sampling_parameters": self.sampling_parameters,
            "system_prompt_hash": self.system_prompt_hash,
            "runtime_environment": self.runtime_environment,
            "tool_versions": self.tool_versions,
        }


@dataclass
class ModelOutput:
    output_id: str = field(default_factory=uuid7)
    model_id: str = ""
    agent_id: str = ""
    prompt_hash: str = ""
    input_artifact_hashes: List[str] = field(default_factory=list)
    retrieved_context_refs: List[str] = field(default_factory=list)
    knowledge_snapshot: str = ""
    candidates: List[str] = field(default_factory=list)
    raw_output: str = ""
    output_hash: str = ""
    created_at: str = field(default_factory=_now_iso)
    correlation_id: str = ""
    causation_id: str = ""
    tenant_id: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "output_id": self.output_id,
            "model_id": self.model_id,
            "agent_id": self.agent_id,
            "prompt_hash": self.prompt_hash,
            "input_artifact_hashes": self.input_artifact_hashes,
            "retrieved_context_refs": self.retrieved_context_refs,
            "knowledge_snapshot": self.knowledge_snapshot,
            "candidates": self.candidates,
            "raw_output": self.raw_output,
            "output_hash": self.output_hash,
            "created_at": self.created_at,
            "correlation_id": self.correlation_id,
            "causation_id": self.causation_id,
            "tenant_id": self.tenant_id,
            "metadata": self.metadata,
        }


@dataclass
class Decision:
    decision_id: str = field(default_factory=uuid7)
    decision_type: str = DecisionType.AGENT_DECISION.value
    task_id: str = ""
    agent_id: str = ""
    created_at: str = field(default_factory=_now_iso)
    correlation_id: str = ""
    causation_id: str = ""
    tenant_id: str = ""
    status: str = "active"
    reasoning: str = ""
    confidence: float = 0.0
    model_output_id: str = ""
    parent_decision_id: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "decision_id": self.decision_id,
            "decision_type": self.decision_type,
            "task_id": self.task_id,
            "agent_id": self.agent_id,
            "created_at": self.created_at,
            "correlation_id": self.correlation_id,
            "causation_id": self.causation_id,
            "tenant_id": self.tenant_id,
            "status": self.status,
            "reasoning": self.reasoning,
            "confidence": self.confidence,
            "model_output_id": self.model_output_id,
            "parent_decision_id": self.parent_decision_id,
        }


@dataclass
class AgentDecision(Decision):
    decision_type: str = field(default=DecisionType.AGENT_DECISION.value, init=False)
    candidates: List[str] = field(default_factory=list)
    selected: str = ""
    selection_rationale: str = ""

    def to_dict(self) -> Dict[str, Any]:
        d = super().to_dict()
        d["candidates"] = self.candidates
        d["selected"] = self.selected
        d["selection_rationale"] = self.selection_rationale
        return d


@dataclass
class PolicyDecision(Decision):
    decision_type: str = field(default=DecisionType.POLICY_DECISION.value, init=False)
    policy_id: str = ""
    policy_version: str = ""
    input_snapshot: Dict[str, Any] = field(default_factory=dict)
    match_result: str = ""
    rule_trace: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        d = super().to_dict()
        d["policy_id"] = self.policy_id
        d["policy_version"] = self.policy_version
        d["input_snapshot"] = self.input_snapshot
        d["match_result"] = self.match_result
        d["rule_trace"] = self.rule_trace
        return d


@dataclass
class HumanDecision(Decision):
    decision_type: str = field(default=DecisionType.HUMAN_DECISION.value, init=False)
    human_action: str = HumanAction.APPROVE.value
    human_id: str = ""
    auth_context: Dict[str, Any] = field(default_factory=dict)
    automated_decision_id: str = ""
    previous_state: str = ""
    resulting_state: str = ""
    rationale: str = ""

    def to_dict(self) -> Dict[str, Any]:
        d = super().to_dict()
        d["human_action"] = self.human_action
        d["human_id"] = self.human_id
        d["auth_context"] = self.auth_context
        d["automated_decision_id"] = self.automated_decision_id
        d["previous_state"] = self.previous_state
        d["resulting_state"] = self.resulting_state
        d["rationale"] = self.rationale
        return d


@dataclass
class ExecutionAuthorization:
    authorization_id: str = field(default_factory=uuid7)
    decision_id: str = ""
    execution_id: str = ""
    created_at: str = field(default_factory=_now_iso)
    correlation_id: str = ""
    causation_id: str = ""
    tenant_id: str = ""
    authorization_type: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "authorization_id": self.authorization_id,
            "decision_id": self.decision_id,
            "execution_id": self.execution_id,
            "created_at": self.created_at,
            "correlation_id": self.correlation_id,
            "causation_id": self.causation_id,
            "tenant_id": self.tenant_id,
            "authorization_type": self.authorization_type,
            "metadata": self.metadata,
        }


@dataclass
class Execution:
    execution_id: str = field(default_factory=uuid7)
    task_id: str = ""
    tool_name: str = ""
    created_at: str = field(default_factory=_now_iso)
    correlation_id: str = ""
    causation_id: str = ""
    tenant_id: str = ""
    status: str = ExecutionStatus.REQUESTED.value
    authorization_id: str = ""
    decision_id: str = ""
    attempt_count: int = 0
    retry_policy: Dict[str, Any] = field(default_factory=dict)
    model_output_id: str = ""
    replay_of: str = ""
    replay_classification: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "execution_id": self.execution_id,
            "task_id": self.task_id,
            "tool_name": self.tool_name,
            "created_at": self.created_at,
            "correlation_id": self.correlation_id,
            "causation_id": self.causation_id,
            "tenant_id": self.tenant_id,
            "status": self.status,
            "authorization_id": self.authorization_id,
            "decision_id": self.decision_id,
            "attempt_count": self.attempt_count,
            "retry_policy": self.retry_policy,
            "model_output_id": self.model_output_id,
            "replay_of": self.replay_of,
            "replay_classification": self.replay_classification,
            "metadata": self.metadata,
        }


@dataclass
class Attempt:
    attempt_id: str = field(default_factory=uuid7)
    execution_id: str = ""
    attempt_number: int = 1
    created_at: str = field(default_factory=_now_iso)
    started_at: str = ""
    completed_at: str = ""
    status: str = AttemptStatus.STARTED.value
    error: str = ""
    error_type: str = ""
    duration_ms: float = 0.0
    result_hash: str = ""
    receipt_id: str = ""
    tenant_id: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "attempt_id": self.attempt_id,
            "execution_id": self.execution_id,
            "attempt_number": self.attempt_number,
            "created_at": self.created_at,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "status": self.status,
            "error": self.error,
            "error_type": self.error_type,
            "duration_ms": self.duration_ms,
            "result_hash": self.result_hash,
            "receipt_id": self.receipt_id,
            "tenant_id": self.tenant_id,
        }


@dataclass
class ToolCall:
    tool_call_id: str = field(default_factory=uuid7)
    execution_id: str = ""
    attempt_id: str = ""
    tool_name: str = ""
    args_hash: str = ""
    result_hash: str = ""
    success: bool = False
    duration_ms: float = 0.0
    created_at: str = field(default_factory=_now_iso)
    correlation_id: str = ""
    causation_id: str = ""
    tenant_id: str = ""
    receipt_id: str = ""
    integrity_hash: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "tool_call_id": self.tool_call_id,
            "execution_id": self.execution_id,
            "attempt_id": self.attempt_id,
            "tool_name": self.tool_name,
            "args_hash": self.args_hash,
            "result_hash": self.result_hash,
            "success": self.success,
            "duration_ms": self.duration_ms,
            "created_at": self.created_at,
            "correlation_id": self.correlation_id,
            "causation_id": self.causation_id,
            "tenant_id": self.tenant_id,
            "receipt_id": self.receipt_id,
            "integrity_hash": self.integrity_hash,
        }


@dataclass
class Artifact:
    artifact_id: str = field(default_factory=uuid7)
    name: str = ""
    artifact_type: str = ArtifactType.FILE.value
    content_hash: str = ""
    content_ref: str = ""
    mime_type: str = ""
    size_bytes: int = 0
    created_at: str = field(default_factory=_now_iso)
    tool_call_id: str = ""
    execution_id: str = ""
    tenant_id: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "artifact_id": self.artifact_id,
            "name": self.name,
            "artifact_type": self.artifact_type,
            "content_hash": self.content_hash,
            "content_ref": self.content_ref,
            "mime_type": self.mime_type,
            "size_bytes": self.size_bytes,
            "created_at": self.created_at,
            "tool_call_id": self.tool_call_id,
            "execution_id": self.execution_id,
            "tenant_id": self.tenant_id,
            "metadata": self.metadata,
        }


@dataclass
class State:
    state_id: str = field(default_factory=uuid7)
    artifact_id: str = ""
    state_type: str = StateType.CREATED.value
    previous_hash: str = ""
    current_hash: str = ""
    scope: str = ""
    created_at: str = field(default_factory=_now_iso)
    execution_id: str = ""
    tenant_id: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "state_id": self.state_id,
            "artifact_id": self.artifact_id,
            "state_type": self.state_type,
            "previous_hash": self.previous_hash,
            "current_hash": self.current_hash,
            "scope": self.scope,
            "created_at": self.created_at,
            "execution_id": self.execution_id,
            "tenant_id": self.tenant_id,
            "metadata": self.metadata,
        }


@dataclass
class Verification:
    verification_id: str = field(default_factory=uuid7)
    subject_id: str = ""
    subject_type: str = VerificationTarget.EXECUTION.value
    verifier_type: str = VerifierType.DETERMINISTIC.value
    verifier_id: str = ""
    method: str = ""
    input_snapshot: Dict[str, Any] = field(default_factory=dict)
    expected_condition: Dict[str, Any] = field(default_factory=dict)
    observed_result: Dict[str, Any] = field(default_factory=dict)
    status: str = VerificationStatus.REQUESTED.value
    confidence: float = 0.0
    evidence_ref: str = ""
    created_at: str = field(default_factory=_now_iso)
    verified_at: str = ""
    correlation_id: str = ""
    causation_id: str = ""
    tenant_id: str = ""
    decision_id: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "verification_id": self.verification_id,
            "subject_id": self.subject_id,
            "subject_type": self.subject_type,
            "verifier_type": self.verifier_type,
            "verifier_id": self.verifier_id,
            "method": self.method,
            "input_snapshot": self.input_snapshot,
            "expected_condition": self.expected_condition,
            "observed_result": self.observed_result,
            "status": self.status,
            "confidence": self.confidence,
            "evidence_ref": self.evidence_ref,
            "created_at": self.created_at,
            "verified_at": self.verified_at,
            "correlation_id": self.correlation_id,
            "causation_id": self.causation_id,
            "tenant_id": self.tenant_id,
            "decision_id": self.decision_id,
            "metadata": self.metadata,
        }


@dataclass
class Join:
    join_id: str = field(default_factory=uuid7)
    intent_id: str = ""
    condition: str = JoinCondition.ALL.value
    required_count: int = 0
    timeout_ms: int = 0
    branch_ids: List[str] = field(default_factory=list)
    completed_branches: List[str] = field(default_factory=list)
    status: str = "pending"
    created_at: str = field(default_factory=_now_iso)
    tenant_id: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "join_id": self.join_id,
            "intent_id": self.intent_id,
            "condition": self.condition,
            "required_count": self.required_count,
            "timeout_ms": self.timeout_ms,
            "branch_ids": self.branch_ids,
            "completed_branches": self.completed_branches,
            "status": self.status,
            "created_at": self.created_at,
            "tenant_id": self.tenant_id,
            "metadata": self.metadata,
        }


@dataclass
class ProvenanceRecord:
    schema_version: str = MCPL_SCHEMA_VERSION
    event_id: str = field(default_factory=uuid7)
    parent_id: str = ""
    causation_id: str = ""
    correlation_id: str = ""
    event_type: str = ""
    timestamp: str = field(default_factory=_now_iso)
    tenant_id: str = ""
    actor: Dict[str, Any] = field(default_factory=dict)
    subject: Dict[str, Any] = field(default_factory=dict)
    causal_links: List[Dict[str, Any]] = field(default_factory=list)
    payload: Dict[str, Any] = field(default_factory=dict)
    integrity: Dict[str, Any] = field(default_factory=dict)
    retention: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "event_id": self.event_id,
            "parent_id": self.parent_id,
            "causation_id": self.causation_id,
            "correlation_id": self.correlation_id,
            "event_type": self.event_type,
            "timestamp": self.timestamp,
            "tenant_id": self.tenant_id,
            "actor": self.actor,
            "subject": self.subject,
            "causal_links": self.causal_links,
            "payload": self.payload,
            "integrity": self.integrity,
            "retention": self.retention,
        }
