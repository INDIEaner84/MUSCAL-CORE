# MC-006 — MUSCAL COGNITIVE PROVENANCE LAYER
## Technical Specification & Implementation Contract v1.0

**Date:** 2026-07-24
**Status:** SPECIFICATION COMPLETE — READY FOR IMPLEMENTATION
**Supersedes:** MC-005 Architecture Review Board Decision
**Prerequisite:** MC-005 (architecture decisions)

---

## TABLE OF CONTENTS

1. [Reconciliation Matrix](#1-reconciliation-matrix)
2. [MCPL Schema Definition](#2-mcpl-schema-definition)
3. [Event Type Registry](#3-event-type-registry)
4. [Identifier Semantics](#4-identifier-semantics)
5. [Causal Graph](#5-causal-graph)
6. [Decision Model](#6-decision-model)
7. [Execution Model](#7-execution-model)
8. [Simulation/Execution Boundary](#8-simulationexecution-boundary)
9. [Verification Engine Contract](#9-verification-engine-contract)
10. [Retry Accounting](#10-retry-accounting)
11. [Replay Model](#11-replay-model)
12. [Non-Determinism Metadata](#12-non-determinism-metadata)
13. [OTel Mapping](#13-otel-mapping)
14. [W3C PROV Mapping](#14-w3c-prov-mapping)
15. [Storage Architecture](#15-storage-architecture)
16. [Repository Integration Map](#16-repository-integration-map)
17. [Migration/Reconciliation Plan](#17-migrationreconciliation-plan)
18. [Test Strategy](#18-test-strategy)
19. [Security/Adversarial Test Plan](#19-securityadversarial-test-plan)
20. [Implementation Sequence](#20-implementation-sequence)
21. [Status Summary](#21-status-summary)

---

## 1. RECONCILIATION MATRIX

MC-005 assumed components that may not exist. This matrix maps MC-005 concepts against the actual codebase.

### 1.1 Component Reconciliation

| MC-005 Concept | Actual File | Status | Action Required |
|---------------|-------------|--------|-----------------|
| **Intent** | `schema.py:NODE_TYPE_INTENT` | EXISTS — graph node type only | Extend with MCPL schema |
| **Task** | `schema.py:NODE_TYPE_EXECUTION_PLAN` | EXISTS — as execution plan | Map to MCPL Task |
| **Agent** | No dedicated class | MISSING — agents referenced by name only | Create MCPL Agent concept |
| **Model** | Referenced in `config.py` (model names) | EXISTS — as config strings | Create MCPL Model entity |
| **Decision** | `runtime/database.py:decisions` table | EXISTS — single type, no decomposition | **DECOMPOSE** per P0-4 |
| **Execution** | `features/tool_runtime:ExecutionReceipt` | EXISTS — with integrity hash | Extend with attempt tracking |
| **ToolCall** | `features/tool_runtime:UnifiedToolRuntime.execute()` | EXISTS — via UTR | Map receipt to MCPL ToolCall |
| **Artifact** | No dedicated class | MISSING — artifacts implicit in tool results | Create MCPL Artifact entity |
| **State** | `graph.py:GraphState` | EXISTS — mutable, in-memory | Create MCPL immutable State snapshots |
| **Verification** | `features/tool_runtime:VerificationResult` | EXISTS — with status enum | Extend with verifier_type taxonomy |
| **ProvenanceRecord** | `features/provenance:ReconstructionReport` | EXISTS — post-hoc reconstruction | Add real-time emission |
| **Join** | `execution_governor.py` loops over tasks | EXISTS — implicit sequential join | Create explicit Join entity |
| **Replay** | `features/replay:replay_service.py` | EXISTS — basic replay | Add replay_of metadata |

### 1.2 ID System Reconciliation

| MC-005 ID | Actual Location | Status | Action |
|-----------|----------------|--------|--------|
| `correlation_id` | `ExecutionContext`, `EventStore`, `ExecutionReceipt` | EXISTS | No change |
| `causation_id` | `ExecutionContext`, `EventStore`, `ExecutionReceipt` | EXISTS | No change |
| `execution_id` | `ExecutionContext`, `ExecutionReceipt`, `EventStore` | EXISTS | Add attempt tracking |
| `attempt_id` | **NOWHERE** | **MISSING** | **CREATE** — new concept |
| `decision_id` | `features/provenance:DecisionWriter`, `decisions` table | EXISTS | Extend with decomposition |
| `verification_id` | `VerificationResult.verification_id` | EXISTS | No change |
| `trace_id` | `ProvenanceContext`, `ExecutionReceipt` | EXISTS | Map to OTel TraceID |
| `span_id` | `ProvenanceContext`, `ExecutionReceipt` | EXISTS | Map to OTel SpanID |
| `artifact_id` | **NOWHERE** | **MISSING** | **CREATE** — new concept |
| `state_id` | **NOWHERE** | **MISSING** | **CREATE** — new concept |
| `join_id` | **NOWHERE** | **MISSING** | **CREATE** — new concept |
| `replay_of` | **NOWHERE** | **MISSING** | **CREATE** — new field |

### 1.3 Event System Reconciliation

| System | Location | Scope | Conflict? |
|--------|----------|-------|-----------|
| EventBus (in-memory) | `event_bus.py` | OS-lifecycle, plugin comms | No — keep as transport |
| EventStore (SQLite) | `runtime/event_store.py` | Persistent event log | **Extend** with MCPL schema |
| Graph events | `graph.py` | Pipeline internal | No — internal only |
| Audit log | `muscal.db:audit_log` | Plugin persistence | No — separate concern |
| `stored_events` table | `runtime/event_store.py` | CQRS event log | **Extend** with MCPL columns |

**Authoritative event store:** `runtime/event_store.py:stored_events` — this is where MCPL events will be persisted.

---

## 2. MCPL SCHEMA DEFINITION

All types use Python `dataclasses` with `__slots__` for memory efficiency. IDs are UUIDv7 strings generated via `features/identity/uuid7.py:uuid7()`.

### 2.1 Base Types

```python
# features/provenance/mcpl_schema.py

from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional
from features.identity.uuid7 import uuid7

class MCPLVersion:
    SCHEMA = "1.0.0"
```

### 2.2 Entity: Intent

```python
@dataclass
class Intent:
    intent_id: str = field(default_factory=uuid7)
    description: str = ""
    created_at: str = ""           # ISO-8601
    correlation_id: str = ""       # OTel trace ID
    causation_id: str = ""         # root causal chain
    tenant_id: str = ""
    status: str = "created"        # created | decomposed | completed | failed | cancelled
    metadata: dict = field(default_factory=dict)

    # Relationships
    task_ids: list[str] = field(default_factory=list)

    # Immutability: intent_id, created_at, correlation_id, causation_id, tenant_id
    # Mutable: status, description, metadata, task_ids
```

### 2.3 Entity: Task

```python
@dataclass
class Task:
    task_id: str = field(default_factory=uuid7)
    intent_id: str = ""
    description: str = ""
    created_at: str = ""
    correlation_id: str = ""
    causation_id: str = ""
    tenant_id: str = ""
    status: str = "created"        # created | assigned | executing | completed | failed | cancelled
    priority: int = 100
    metadata: dict = field(default_factory=dict)

    # Relationships
    agent_id: str = ""
    execution_ids: list[str] = field(default_factory=list)
    join_id: str = ""              # if part of parallel execution

    # Immutability: task_id, intent_id, created_at, correlation_id, causation_id, tenant_id
    # Mutable: status, agent_id, execution_ids, join_id, metadata
```

### 2.4 Entity: Agent

```python
@dataclass
class Agent:
    agent_id: str = field(default_factory=uuid7)
    name: str = ""                 # e.g. "planner_v2", "executor"
    version: str = "1.0.0"
    agent_type: str = "llm"        # llm | rule_based | human | hybrid
    created_at: str = ""
    tenant_id: str = ""

    # Immutability: agent_id, name, version, agent_type, created_at, tenant_id
```

### 2.5 Entity: Model

```python
@dataclass
class Model:
    model_id: str = field(default_factory=uuid7)
    provider: str = ""             # openai, anthropic, ollama
    model_name: str = ""           # gpt-4o, claude-3-opus
    model_version: str = ""
    created_at: str = ""

    # Non-determinism metadata
    temperature: float = 0.0
    top_p: float = 1.0
    seed: Optional[int] = None
    sampling_parameters: dict = field(default_factory=dict)
    system_prompt_hash: str = ""   # sha256
    runtime_environment: dict = field(default_factory=dict)  # OS, Python version
    tool_versions: dict = field(default_factory=dict)

    # Immutability: all fields (model config is immutable per invocation)
```

### 2.6 Entity: ModelOutput

```python
@dataclass
class ModelOutput:
    output_id: str = field(default_factory=uuid7)
    model_id: str = ""
    agent_id: str = ""
    prompt_hash: str = ""          # sha256 of user prompt
    input_artifact_hashes: list[str] = field(default_factory=list)
    retrieved_context_refs: list[str] = field(default_factory=list)
    knowledge_snapshot: str = ""   # version of knowledge base used
    candidates: list[str] = field(default_factory=list)  # proposed actions
    raw_output: str = ""           # raw LLM response (may be empty for structured)
    output_hash: str = ""          # sha256 of output content
    created_at: str = ""
    correlation_id: str = ""
    causation_id: str = ""
    tenant_id: str = ""
    metadata: dict = field(default_factory=dict)

    # Immutability: all fields (output is immutable once produced)
    # NOTE: raw_output may be empty if only hashes are stored (GDPR)
```

### 2.7 Entity: Decision (supertype)

```python
class DecisionType(str, Enum):
    MODEL_OUTPUT = "model_output"
    AGENT_DECISION = "agent_decision"
    POLICY_DECISION = "policy_decision"
    HUMAN_DECISION = "human_decision"

@dataclass
class Decision:
    decision_id: str = field(default_factory=uuid7)
    decision_type: DecisionType = DecisionType.AGENT_DECISION
    task_id: str = ""
    agent_id: str = ""
    created_at: str = ""
    correlation_id: str = ""
    causation_id: str = ""
    tenant_id: str = ""
    status: str = "active"         # active | executed | superseded | revoked
    reasoning: str = ""            # may be empty for privacy
    confidence: float = 0.0
    model_output_id: str = ""      # links to ModelOutput if applicable
    parent_decision_id: str = ""   # causal parent (e.g. MODEL_OUTPUT → AGENT_DECISION)

    # Immutability: decision_id, decision_type, task_id, agent_id, created_at,
    #               correlation_id, causation_id, tenant_id
    # Mutable: status
```

### 2.8 Entity: AgentDecision (extends Decision)

```python
@dataclass
class AgentDecision(Decision):
    """Agent selected an action from candidates."""
    decision_type: DecisionType = field(default=DecisionType.AGENT_DECISION, init=False)
    candidates: list[str] = field(default_factory=list)
    selected: str = ""
    selection_rationale: str = ""  # policy or rule name that guided selection

    # Immutability: all inherited + candidates, selected, selection_rationale
```

### 2.9 Entity: PolicyDecision (extends Decision)

```python
@dataclass
class PolicyDecision(Decision):
    """Deterministic policy rule evaluated against execution request."""
    decision_type: DecisionType = field(default=DecisionType.POLICY_DECISION, init=False)
    policy_id: str = ""            # rule/policy identifier
    policy_version: str = ""
    input_snapshot: dict = field(default_factory=dict)
    match_result: str = ""         # ALLOW | DENY | DEFER
    rule_trace: list[str] = field(default_factory=list)

    # Immutability: all inherited + policy_id, policy_version, input_snapshot,
    #               match_result, rule_trace
```

### 2.10 Entity: HumanDecision (extends Decision)

```python
class HumanAction(str, Enum):
    APPROVE = "approve"
    REJECT = "reject"
    OVERRIDE = "override"
    MODIFY = "modify"

@dataclass
class HumanDecision(Decision):
    """Human operator approved, rejected, overrode, or modified."""
    decision_type: DecisionType = field(default=DecisionType.HUMAN_DECISION, init=False)
    human_action: HumanAction = HumanAction.APPROVE
    human_id: str = ""             # operator identity
    auth_context: dict = field(default_factory=dict)  # MFA, role, etc.
    automated_decision_id: str = ""  # the decision being reviewed
    previous_state: str = ""       # state before human intervention
    resulting_state: str = ""      # state after human intervention
    rationale: str = ""            # legally required in some contexts

    # Immutability: all inherited + human_action, human_id, auth_context,
    #               automated_decision_id, previous_state, resulting_state, rationale
```

### 2.11 Entity: ExecutionAuthorization

```python
@dataclass
class ExecutionAuthorization:
    authorization_id: str = field(default_factory=uuid7)
    decision_id: str = ""          # the decision that authorized execution
    execution_id: str = ""         # the execution being authorized
    created_at: str = ""
    correlation_id: str = ""
    causation_id: str = ""
    tenant_id: str = ""
    authorization_type: str = ""   # policy | human | agent | system
    metadata: dict = field(default_factory=dict)

    # Immutability: all fields
```

### 2.12 Entity: Execution

```python
class ExecutionStatus(str, Enum):
    REQUESTED = "requested"
    AUTHORIZED = "authorized"
    STARTED = "started"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    RETRYING = "retrying"

@dataclass
class Execution:
    execution_id: str = field(default_factory=uuid7)
    task_id: str = ""
    tool_name: str = ""
    created_at: str = ""
    correlation_id: str = ""
    causation_id: str = ""
    tenant_id: str = ""
    status: ExecutionStatus = ExecutionStatus.REQUESTED
    authorization_id: str = ""
    decision_id: str = ""          # AGENT_DECISION that led here

    # Retry tracking
    attempt_count: int = 0
    retry_policy: dict = field(default_factory=dict)  # max_attempts, backoff

    # Non-determinism
    model_output_id: str = ""      # if execution is model-driven

    # Replay tracking
    replay_of: str = ""            # original execution_id if this is a replay
    replay_classification: str = ""  # REPLAYABLE | PARTIALLY_REPLAYABLE | NON_REPLAYABLE

    metadata: dict = field(default_factory=dict)

    # Immutability: execution_id, task_id, tool_name, created_at,
    #               correlation_id, causation_id, tenant_id, replay_of
    # Mutable: status, attempt_count, metadata
```

### 2.13 Entity: Attempt

```python
class AttemptStatus(str, Enum):
    STARTED = "started"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    TIMED_OUT = "timed_out"

@dataclass
class Attempt:
    attempt_id: str = field(default_factory=uuid7)
    execution_id: str = ""         # logical execution this belongs to
    attempt_number: int = 1        # 1-based
    created_at: str = ""
    started_at: str = ""
    completed_at: str = ""
    status: AttemptStatus = AttemptStatus.STARTED
    error: str = ""
    error_type: str = ""
    duration_ms: float = 0.0
    result_hash: str = ""          # sha256 of result data
    receipt_id: str = ""           # link to ExecutionReceipt
    tenant_id: str = ""

    # Immutability: attempt_id, execution_id, attempt_number, created_at, tenant_id
    # Mutable: status, started_at, completed_at, error, error_type, duration_ms, result_hash
```

### 2.14 Entity: ToolCall

```python
@dataclass
class ToolCall:
    tool_call_id: str = field(default_factory=uuid7)
    execution_id: str = ""
    attempt_id: str = ""
    tool_name: str = ""
    args_hash: str = ""            # sha256 of args
    result_hash: str = ""          # sha256 of result
    success: bool = False
    duration_ms: float = 0.0
    created_at: str = ""
    correlation_id: str = ""
    causation_id: str = ""
    tenant_id: str = ""
    receipt_id: str = ""           # link to ExecutionReceipt
    integrity_hash: str = ""       # receipt integrity hash

    # Immutability: all fields
```

### 2.15 Entity: Artifact

```python
@dataclass
class Artifact:
    artifact_id: str = field(default_factory=uuid7)
    name: str = ""
    artifact_type: str = ""        # file | memory | db_row | api_response | screenshot
    content_hash: str = ""         # sha256 of content
    content_ref: str = ""          # path, URI, or reference
    mime_type: str = ""
    size_bytes: int = 0
    created_at: str = ""
    tool_call_id: str = ""         # which tool call produced this
    execution_id: str = ""
    tenant_id: str = ""
    metadata: dict = field(default_factory=dict)

    # Immutability: artifact_id, content_hash, created_at, tool_call_id, execution_id, tenant_id
    # Mutable: metadata
```

### 2.16 Entity: State

```python
@dataclass
class State:
    state_id: str = field(default_factory=uuid7)
    artifact_id: str = ""          # the artifact that changed state
    state_type: str = ""           # created | modified | deleted
    previous_hash: str = ""        # hash before change
    current_hash: str = ""         # hash after change
    scope: str = ""                # filesystem | memory | database | external
    created_at: str = ""
    execution_id: str = ""
    tenant_id: str = ""
    metadata: dict = field(default_factory=dict)

    # Immutability: all fields
```

### 2.17 Entity: Verification

```python
class VerificationStatus(str, Enum):
    REQUESTED = "requested"
    RUNNING = "running"
    PASSED = "passed"
    FAILED = "failed"
    INCONCLUSIVE = "inconclusive"
    OVERRIDDEN = "overridden"

class VerifierType(str, Enum):
    DETERMINISTIC = "deterministic"       # exact match, recomputation
    SCHEMA = "schema"                     # JSON Schema, type validation
    INVARIANT = "invariant"               # constraint holds
    RULE_ENGINE = "rule_engine"           # deterministic policy rules
    CRYPTOGRAPHIC = "cryptographic"       # signature, hash chain
    SIMULATION = "simulation"             # model-based (Phase 2)
    MODEL_CRITIC = "model_critic"         # LLM-as-judge (Phase 2)
    INDEPENDENT_MODEL = "independent_model"  # second model (Phase 2)
    HUMAN = "human"                       # human review (Phase 2)

class VerificationTarget(str, Enum):
    EXECUTION = "execution"               # logical execution completion
    ATTEMPT = "attempt"                   # physical attempt success
    ARTIFACT = "artifact"                 # artifact correctness
    STATE = "state"                       # state correctness

@dataclass
class Verification:
    verification_id: str = field(default_factory=uuid7)
    subject_id: str = ""                 # what is being verified
    subject_type: VerificationTarget = VerificationTarget.EXECUTION
    verifier_type: VerifierType = VerifierType.DETERMINISTIC
    verifier_id: str = ""                # specific verifier instance
    method: str = ""                     # how verification was performed
    input_snapshot: dict = field(default_factory=dict)  # hash of input state
    expected_condition: dict = field(default_factory=dict)  # what was expected
    observed_result: dict = field(default_factory=dict)    # what was observed
    status: VerificationStatus = VerificationStatus.REQUESTED
    confidence: float = 0.0              # [0.0, 1.0]
    evidence_ref: str = ""               # pointer to evidence
    created_at: str = ""
    verified_at: str = ""
    correlation_id: str = ""
    causation_id: str = ""
    tenant_id: str = ""
    decision_id: str = ""                # link to the decision this verifies
    metadata: dict = field(default_factory=dict)

    # Immutability: verification_id, subject_id, subject_type, verifier_type,
    #               verifier_id, method, created_at, correlation_id, causation_id, tenant_id
    # Mutable: status, observed_result, verified_at, confidence, evidence_ref
```

### 2.18 Entity: Join

```python
class JoinCondition(str, Enum):
    ALL = "all"                 # wait for all branches
    ANY = "any"                 # first branch triggers join
    QUORUM = "quorum"           # N of M branches
    THRESHOLD = "threshold"     # branches meeting criteria
    TIMEOUT = "timeout"         # deadline-based
    BEST_EFFORT = "best_effort" # whatever is available

@dataclass
class Join:
    join_id: str = field(default_factory=uuid7)
    intent_id: str = ""
    condition: JoinCondition = JoinCondition.ALL
    required_count: int = 0     # for QUORUM/THRESHOLD
    timeout_ms: int = 0         # for TIMEOUT
    branch_ids: list[str] = field(default_factory=list)  # task_ids
    completed_branches: list[str] = field(default_factory=list)
    status: str = "pending"     # pending | joined | timed_out | partial
    created_at: str = ""
    tenant_id: str = ""
    metadata: dict = field(default_factory=dict)

    # Immutability: join_id, intent_id, condition, created_at, tenant_id
    # Mutable: completed_branches, status
```

### 2.19 Entity: ProvenanceRecord

```python
@dataclass
class ProvenanceRecord:
    """Canonical provenance event — the fundamental unit of MCPL."""
    schema_version: str = "1.0.0"
    event_id: str = field(default_factory=uuid7)
    parent_id: str = ""           # direct causal parent (may be null)
    causation_id: str = ""        # root causal chain identifier
    correlation_id: str = ""      # OTel trace ID

    event_type: str = ""          # from MCPL event type registry
    timestamp: str = ""           # ISO-8601

    tenant_id: str = ""

    actor: dict = field(default_factory=dict)     # {type, id, version, identity_hash}
    subject: dict = field(default_factory=dict)   # {type, id}
    causal_links: list[dict] = field(default_factory=list)  # [{type, target_id}]
    payload: dict = field(default_factory=dict)   # type-specific data

    integrity: dict = field(default_factory=dict)  # {hash, previous_hash, signature}
    retention: dict = field(default_factory=dict)  # {ttl_days, legal_hold, crypto_shreddable}

    def __post_init__(self):
        if not self.timestamp:
            from datetime import datetime, timezone
            self.timestamp = datetime.now(timezone.utc).isoformat()
```

---

## 3. EVENT TYPE REGISTRY

### 3.1 MCPL Event Types

```python
class MCPLEventType(str, Enum):
    # Intent lifecycle
    INTENT_CREATED = "intent.created"
    INTENT_COMPLETED = "intent.completed"
    INTENT_FAILED = "intent.failed"
    INTENT_CANCELLED = "intent.cancelled"

    # Task lifecycle
    TASK_CREATED = "task.created"
    TASK_ASSIGNED = "task.assigned"
    TASK_COMPLETED = "task.completed"
    TASK_FAILED = "task.failed"
    TASK_CANCELLED = "task.cancelled"

    # Model invocation
    MODEL_INVOKED = "model.invoked"
    MODEL_OUTPUT = "model.output"

    # Decision lifecycle
    DECISION_AGENT = "decision.agent"
    DECISION_POLICY = "decision.policy"
    DECISION_HUMAN = "decision.human"

    # Execution lifecycle
    EXECUTION_AUTHORIZED = "execution.authorized"
    EXECUTION_STARTED = "execution.started"
    EXECUTION_COMPLETED = "execution.completed"
    EXECUTION_FAILED = "execution.failed"
    EXECUTION_RETRY = "execution.retry"
    EXECUTION_CANCELLED = "execution.cancelled"

    # Tool call
    TOOL_CALL = "tool.call"
    TOOL_CALL_RESULT = "tool.call.result"

    # Artifact lifecycle
    ARTIFACT_CREATED = "artifact.created"
    ARTIFACT_MODIFIED = "artifact.modified"

    # State change
    STATE_CHANGED = "state.changed"

    # Verification lifecycle
    VERIFICATION_REQUESTED = "verification.requested"
    VERIFICATION_STARTED = "verification.started"
    VERIFICATION_RESULT = "verification.result"

    # Parallel execution
    EXECUTION_JOIN = "execution.join"

    # Replay
    EXECUTION_REPLAY = "execution.replay"
```

### 3.2 Event Type → Entity Mapping

| Event Type | Primary Entity | Causal Parent | Payload |
|-----------|---------------|---------------|---------|
| `intent.created` | Intent | — | intent description, correlation_id |
| `task.created` | Task | intent | task description, agent_id |
| `task.assigned` | Task | task.created | agent_id |
| `model.invoked` | Model | task | model config, prompt_hash |
| `model.output` | ModelOutput | model.invoked | candidates, output_hash |
| `decision.agent` | AgentDecision | model.output | selected, candidates, rationale |
| `decision.policy` | PolicyDecision | decision.agent | policy_id, match_result, rule_trace |
| `decision.human` | HumanDecision | decision.agent or decision.policy | human_action, rationale |
| `execution.authorized` | ExecutionAuthorization | decision.* | authorization_type |
| `execution.started` | Execution | execution.authorized | tool_name |
| `execution.completed` | Execution | tool.call.result | duration_ms, success |
| `execution.failed` | Execution | tool.call.result | error, error_type |
| `execution.retry` | Execution | execution.failed | attempt_number, retry_policy |
| `tool.call` | ToolCall | execution.started | tool_name, args_hash |
| `tool.call.result` | ToolCall | tool.call | result_hash, success |
| `artifact.created` | Artifact | tool.call.result | name, content_hash, mime_type |
| `state.changed` | State | artifact.created | previous_hash, current_hash, scope |
| `verification.requested` | Verification | tool.call.result | subject_id, verifier_type |
| `verification.started` | Verification | verification.requested | method |
| `verification.result` | Verification | verification.started | status, confidence, evidence_ref |
| `execution.join` | Join | task.* | condition, branch_ids |
| `execution.replay` | Execution | — | replay_of, replay_classification |

---

## 4. IDENTIFIER SEMANTICS

### 4.1 Identifier Definitions

| Identifier | Uniqueness | Immutable? | Lifecycle | Propagation |
|-----------|-----------|-----------|-----------|-------------|
| `correlation_id` | Global — shared across entire workflow | Yes | Created at workflow start, propagated to all children | OTel TraceID → all events in workflow |
| `causation_id` | Per causal chain — root of a causal sequence | Yes | Created at first event, propagated to all downstream | Root event ID → all causally linked events |
| `intent_id` | Per intent | Yes | Created at intent creation, propagated to tasks | Intent → Tasks → Executions |
| `task_id` | Per task | Yes | Created at task creation, propagated to executions | Task → Execution → Attempts |
| `execution_id` | Per logical execution | Yes | Created at execution request, shared across retries | Execution → Attempts → Receipts |
| `attempt_id` | Per physical attempt | Yes | Created at each retry, unique per attempt | Attempt → Receipt, never shared |
| `decision_id` | Per decision event | Yes | Created at decision time | Decision → Authorization → Execution |
| `verification_id` | Per verification | Yes | Created at verification request | Verification → Evidence |
| `artifact_id` | Per artifact | Yes | Created at artifact production | Artifact → State |
| `state_id` | Per state change | Yes | Created at each state mutation | State → Verification |
| `join_id` | Per join | Yes | Created at join initiation | Join → Completed branches |
| `replay_of` | Reference to original | N/A | Set only on replay executions | Replay → Original |

### 4.2 Propagation Rules

```
correlation_id:  Intent → Task → Execution → Attempt → ToolCall → Artifact → Verification
causation_id:    First event in chain → all downstream events
intent_id:       Intent → Task → Execution
task_id:         Task → Execution → Attempt → ToolCall
execution_id:    Execution → Attempt → ToolCall → Receipt
attempt_id:      Attempt → ToolCall (specific attempt only)
decision_id:     Decision → Authorization → Execution
```

### 4.3 Critical Invariants

1. **`execution_id` ≠ `attempt_id`**: An execution with 3 retries has 1 `execution_id` and 3 `attempt_id` values. Never conflate them.

2. **`attempt_id` is attempt-specific**: A verification of `attempt_id=att_002` must NOT be interpreted as verification of `attempt_id=att_003`.

3. **`correlation_id` = `trace_id`**: The MCPL `correlation_id` is the OTel TraceID. They must be identical.

4. **`causation_id` is immutable**: Once set, never changed. The causation chain is append-only.

5. **`replay_of` is one-directional**: A replay references the original. The original never references the replay.

---

## 5. CAUSAL GRAPH

### 5.1 Valid Relationships

| Source | Edge | Target | Required? | Notes |
|--------|------|--------|-----------|-------|
| INTENT | `decomposes_into` | TASK | Yes | At least one task per intent |
| TASK | `assigned_to` | AGENT | No | Rule-based tasks may skip |
| AGENT | `invokes` | MODEL | No | Non-LLM agents skip |
| MODEL | `produces` | MODEL_OUTPUT | No | Non-LLM agents skip |
| MODEL_OUTPUT | `considered_by` | AGENT_DECISION | No | Direct execution possible |
| AGENT_DECISION | `submitted_to` | POLICY_DECISION | No | Only if policy gate exists |
| AGENT_DECISION | `submitted_to` | HUMAN_DECISION | No | Only if HITL required |
| POLICY_DECISION | `allows` | EXECUTION_AUTHORIZATION | No | |
| HUMAN_DECISION | `approves` | EXECUTION_AUTHORIZATION | No | |
| HUMAN_DECISION | `rejects` | AGENT_DECISION | No | |
| HUMAN_DECISION | `overrides` | AGENT_DECISION | No | |
| EXECUTION_AUTHORIZATION | `authorizes` | EXECUTION | Yes | |
| EXECUTION | `has_attempt` | ATTEMPT | No | Only on retry |
| EXECUTION | `invokes` | TOOL_CALL | No | Tool-less executions valid |
| TOOL_CALL | `produces` | ARTIFACT | No | Side-effect-free tools |
| ARTIFACT | `changes` | STATE | No | Read-only tools |
| STATE | `verified_by` | VERIFICATION | No | |
| VERIFICATION | `recorded_in` | PROVENANCE_RECORD | Yes | |

### 5.2 Optionality Rules

```
Minimal path (rule-based, no verification):
  INTENT → TASK → EXECUTION_AUTHORIZATION → EXECUTION → TOOL_CALL

Standard path (LLM + policy):
  INTENT → TASK → AGENT → MODEL → MODEL_OUTPUT → AGENT_DECISION →
  POLICY_DECISION → EXECUTION_AUTHORIZATION → EXECUTION → TOOL_CALL →
  ARTIFACT → STATE → VERIFICATION

Full path (LLM + policy + HITL):
  INTENT → TASK → AGENT → MODEL → MODEL_OUTPUT → AGENT_DECISION →
  HUMAN_DECISION → EXECUTION_AUTHORIZATION → EXECUTION → TOOL_CALL →
  ARTIFACT → STATE → VERIFICATION
```

### 5.3 Parallel Execution

```
INTENT
  ├── TASK_A (branch_id: "branch_a")
  │     └── EXECUTION_A
  ├── TASK_B (branch_id: "branch_b")
  │     └── EXECUTION_B
  └── JOIN (join_id: "join_1", condition: ALL)
        └── VERIFICATION
```

Join conditions:
- `ALL` — wait for all branches (default)
- `ANY` — first branch triggers join
- `QUORUM` — N of M must complete
- `THRESHOLD` — branches meeting criteria
- `TIMEOUT` — deadline-based
- `BEST_EFFORT` — whatever is available

The join decision itself is recorded as a PROVENANCE_EVENT with `event_type = "execution.join"`.

---

## 6. DECISION MODEL

### 6.1 Four-Type Decomposition

| Type | Source | Non-deterministic? | Evidence | Accountability |
|------|--------|-------------------|----------|---------------|
| `MODEL_OUTPUT` | LLM completion | Yes | prompt hash, config, response hash | Model provider |
| `AGENT_DECISION` | Agent logic | Partially | candidates, selection rule | Agent developer |
| `POLICY_DECISION` | Deterministic rules | No | rule ID, inputs, match result | System operator |
| `HUMAN_DECISION` | Human operator | Yes | identity, auth context, rationale | Human operator |

### 6.2 Causal Chain (MUST be recorded explicitly)

```
MODEL_OUTPUT "proposed_action_X"
  │  [NOT: "the LLM decided X"]
  ▼
AGENT_DECISION "selected_action_X from candidates [X, Y, Z]"
  │
  ▼
POLICY_DECISION "policy_p99 allows_action_X"
  │
  ▼
EXECUTION_AUTHORIZATION "execution_of_X authorized"
  │
  ▼
EXECUTION "tool_call_X(args)"
```

### 6.3 Semantic Prohibition

**The provenance layer MUST NEVER state:**
- "the LLM decided X"
- "the model selected X"

**The provenance layer MUST state:**
- "the model generated candidate X" (MODEL_OUTPUT)
- "the agent selected X from candidates [X, Y, Z]" (AGENT_DECISION)
- "policy P allowed execution of X" (POLICY_DECISION)

### 6.4 Decision Reconstruction Queries

The provenance system must support answering:
1. "What did the model suggest?" → Query `MODEL_OUTPUT` events
2. "What did the agent select?" → Query `AGENT_DECISION` events
3. "What policy allowed?" → Query `POLICY_DECISION` events
4. "What did the human approve or reject?" → Query `HUMAN_DECISION` events
5. "What was actually executed?" → Query `EXECUTION` events

---

## 7. EXECUTION MODEL

### 7.1 Lifecycle

```
REQUESTED → AUTHORIZED → STARTED → RUNNING → COMPLETED
                                          → FAILED → RETRYING → RUNNING
```

### 7.2 Final States

- `COMPLETED` — execution succeeded
- `FAILED` — execution failed after all retries exhausted
- `CANCELLED` — execution was cancelled before completion

### 7.3 Completion Semantics

An execution is marked `COMPLETED` ONLY when:
1. The tool executor returns a success result
2. The result passes integrity verification (receipt finalized + hash matches)
3. If verification is required, the verification passes

**An execution MUST NOT be marked COMPLETED merely because an agent produced a success message.**

### 7.4 State Transitions

```python
_VALID_TRANSITIONS = {
    "requested": {"authorized"},
    "authorized": {"started", "cancelled"},
    "started": {"running", "failed", "cancelled"},
    "running": {"completed", "failed", "retrying"},
    "retrying": {"running", "failed"},
    "completed": set(),  # terminal
    "failed": {"retrying"},  # can retry if policy allows
    "cancelled": set(),  # terminal
}
```

---

## 8. SIMULATION/EXECUTION BOUNDARY

### 8.1 Execution Modes

Defined in `features/identity/reality.py`:

| Mode | Meaning | Can produce receipt? | Can produce verification? |
|------|---------|---------------------|--------------------------|
| `REAL` | Actual execution against real systems | YES | YES |
| `SIMULATED` | Dry-run, no side effects | NO | CONTEXT_DEPENDENT |
| `PROPOSED` | Planning only | NO | NO |
| `SHADOW` | Runs alongside real, no side effects | NO | CONTEXT_DEPENDENT |
| `REPLAY` | Re-execution of historical execution | YES (new receipt) | YES (new verification) |

### 8.2 Verification Mode Matrix

From `features/identity/reality.py`:

| Mode | unverified | verified | failed | rejected |
|------|-----------|----------|--------|----------|
| real | VALID | VALID | VALID | VALID |
| simulated | VALID | CONTEXT_DEPENDENT | VALID | VALID |
| proposed | VALID | INVALID | INVALID | VALID |
| shadow | VALID | VALID | VALID | VALID |
| replay | VALID | CONTEXT_DEPENDENT | VALID | VALID |

### 8.3 Mandatory Rules

1. **Simulation MUST NOT generate an authoritative execution receipt.**
2. **Planning MUST NOT generate an authoritative execution receipt.**
3. **Predicted state MUST NOT become observed state.**
4. **Agent claims MUST NOT become authoritative execution evidence.**
5. **proposed + verified = INVALID** — a plan cannot be verified before execution.
6. **proposed + running = INVALID** — a plan is not executed.

---

## 9. VERIFICATION ENGINE CONTRACT

### 9.1 Verifier Interface

```python
# features/provenance/verification_engine.py

from typing import Protocol, Any

class Verifier(Protocol):
    """Protocol for all verifiers."""

    @property
    def verifier_type(self) -> VerifierType: ...

    @property
    def verifier_id(self) -> str: ...

    def verify(self, subject: Any, expected: dict) -> VerificationResult: ...
```

### 9.2 Built-in Verifiers (MVP)

#### Deterministic Verifier

```python
class DeterministicVerifier:
    verifier_type = VerifierType.DETERMINISTIC

    def verify(self, receipt: ExecutionReceipt, expected: dict = None) -> VerificationResult:
        """Recomputes receipt hash and compares."""
        if not receipt.finalized:
            return VerificationResult(status=VerificationStatus.INCONCLUSIVE, ...)
        if receipt.verify_integrity():
            return VerificationResult(status=VerificationStatus.PASSED, ...)
        return VerificationResult(status=VerificationStatus.FAILED, ...)
```

#### Schema Verifier

```python
class SchemaVerifier:
    verifier_type = VerifierType.SCHEMA

    def verify(self, data: dict, expected: dict) -> VerificationResult:
        """Validates data against JSON Schema."""
        schema = expected.get("schema", {})
        errors = validate_json_schema(data, schema)
        if not errors:
            return VerificationResult(status=VerificationStatus.PASSED, ...)
        return VerificationResult(status=VerificationStatus.FAILED, ...)
```

#### Invariant Verifier

```python
class InvariantVerifier:
    verifier_type = VerifierType.INVARIANT

    def verify(self, data: dict, expected: dict) -> VerificationResult:
        """Checks invariant conditions hold."""
        conditions = expected.get("conditions", [])
        for cond in conditions:
            if not evaluate_condition(data, cond):
                return VerificationResult(status=VerificationStatus.FAILED, ...)
        return VerificationResult(status=VerificationStatus.PASSED, ...)
```

#### Rule Engine Verifier

```python
class RuleEngineVerifier:
    verifier_type = VerifierType.RULE_ENGINE

    def verify(self, data: dict, expected: dict) -> VerificationResult:
        """Evaluates deterministic policy rules."""
        rules = expected.get("rules", [])
        results = [evaluate_rule(data, rule) for rule in rules]
        if all(r.passed for r in results):
            return VerificationResult(status=VerificationStatus.PASSED, ...)
        return VerificationResult(status=VerificationStatus.FAILED, ...)
```

### 9.3 Verifier Registry

```python
class VerifierRegistry:
    def __init__(self):
        self._verifiers: dict[str, Verifier] = {}

    def register(self, verifier_id: str, verifier: Verifier) -> None:
        self._verifiers[verifier_id] = verifier

    def get(self, verifier_id: str) -> Optional[Verifier]:
        return self._verifiers.get(verifier_id)

    def list_all(self) -> list[str]:
        return list(self._verifiers.keys())

    def verify(self, verifier_id: str, subject: Any, expected: dict) -> VerificationResult:
        verifier = self.get(verifier_id)
        if verifier is None:
            return VerificationResult(
                status=VerificationStatus.INCONCLUSIVE,
                evidence={"reason": f"Verifier '{verifier_id}' not found"}
            )
        return verifier.verify(subject, expected)
```

### 9.4 Verification Lifecycle

```
REQUESTED → RUNNING → PASSED
                    → FAILED
                    → INCONCLUSIVE
                    → OVERRIDDEN (human or policy override)
```

### 9.5 Verification Targets

```python
class VerificationTarget(str, Enum):
    EXECUTION = "execution"     # validates logical execution completion
    ATTEMPT = "attempt"         # validates physical attempt success
    ARTIFACT = "artifact"       # validates artifact correctness
    STATE = "state"             # validates state correctness
```

**Critical rule:** A verification of `attempt_2` must NOT be silently interpreted as verification of `attempt_3`. The `subject_id` field must specify exactly which attempt or artifact is being verified.

### 9.6 Evidence Strength Classification

| VerifierType | Evidence Strength | Regulatory Use |
|-------------|------------------|----------------|
| DETERMINISTIC | **STRONG** — exact match | Audit trail |
| SCHEMA | **STRONG** — format validated | Input validation |
| INVARIANT | **STRONG** — constraint holds | Business rules |
| RULE_ENGINE | **STRONG** — deterministic rules | Authorization |
| CRYPTOGRAPHIC | **STRONG** — signature verified | Non-repudiation |
| SIMULATION | **PARTIAL** — model-based | What-if analysis |
| MODEL_CRITIC | **WEAK** — probabilistic | Quality check |
| INDEPENDENT_MODEL | **WEAK** — cross-check | Consistency check |
| HUMAN | **CONTEXTUAL** — depends on authority | HITL approval |

---

## 10. RETRY ACCOUNTING

### 10.1 Data Model

```
execution_id = exec_01J2XYZ...    (logical — shared across all retries)
attempt_id:
  att_01J2...001                  (physical attempt 1)
  att_01J2...002                  (physical attempt 2)
  att_01J2...003                  (physical attempt 3)
```

### 10.2 ExecutionReceipt Retry Fields

From `features/tool_runtime/tool_runtime.py`:

```python
class ExecutionReceipt:
    # ... existing fields ...
    retry_count: int      # total retries so far
    attempt_number: int   # 1-based attempt number
```

### 10.3 Attempt Tracking

Each attempt creates a new `Attempt` record with:
- `attempt_id` = new UUIDv7
- `execution_id` = same logical execution
- `attempt_number` = sequential (1, 2, 3, ...)
- `status` = started → running → completed/failed
- `result_hash` = sha256 of attempt result

### 10.4 Verification Targeting

```python
# Correct: verification targets specific attempt
verification.subject_id = "att_01J2...003"  # attempt 3
verification.subject_type = VerificationTarget.ATTEMPT

# Correct: verification targets logical execution
verification.subject_id = "exec_01J2..."  # logical execution
verification.subject_type = VerificationTarget.EXECUTION

# WRONG: verification ambiguously references "the execution"
# without specifying which attempt
```

---

## 11. REPLAY MODEL

### 11.1 Replay Execution

A replay is a NEW execution with its OWN:
- `execution_id` (new UUIDv7)
- `attempt_id` values (new UUIDv7s)
- `ProvenanceRecord` events

It references the original via:
```python
execution.replay_of = "exec_01J2ORIGINAL..."  # original execution_id
```

### 11.2 Replay Classification

```python
class ReplayClassification(str, Enum):
    REPLAYABLE = "replayable"               # deterministic: same input → same output
    PARTIALLY_REPLAYABLE = "partially_replayable"  # deterministic with probabilistic components
    NON_REPLAYABLE = "non_replayable"       # inherently non-deterministic
```

### 11.3 Metadata Capture

For each replay, capture:
- `model_id` and config (for non-determinism analysis)
- `tool_versions` (for environment reproducibility)
- `knowledge_snapshot` (for RAG reproducibility)
- `retrieved_context_refs` (for context reproducibility)

### 11.4 Rules

1. A replay MUST have a new `execution_id`
2. A replay MUST reference the original via `replay_of`
3. A replay's provenance events are NEW events with new `event_id` values
4. The original provenance record is NEVER modified
5. Replays are classified by reproducibility

---

## 12. NON-DETERMINISM METADATA

### 12.1 Required Metadata Per Execution

For model-driven executions, capture:

| Field | Source | Storage |
|-------|--------|---------|
| `model_id` | Model entity | ProvenanceRecord.payload |
| `model_version` | Model entity | ProvenanceRecord.payload |
| `provider` | Model entity | ProvenanceRecord.payload |
| `system_prompt_hash` | sha256 of system prompt | ProvenanceRecord.payload |
| `prompt_hash` | sha256 of user prompt | ProvenanceRecord.payload |
| `input_artifact_hashes` | sha256 of referenced artifacts | ProvenanceRecord.payload |
| `tool_context` | available tools at decision time | ProvenanceRecord.payload |
| `temperature` | model config | ProvenanceRecord.payload |
| `top_p` | model config | ProvenanceRecord.payload |
| `seed` | model config (may be null) | ProvenanceRecord.payload |
| `sampling_parameters` | full config dict | ProvenanceRecord.payload |
| `runtime_environment` | OS, Python version, packages | ProvenanceRecord.payload |
| `retrieved_context_refs` | RAG chunk references | ProvenanceRecord.payload |
| `knowledge_snapshot` | knowledge base version | ProvenanceRecord.payload |
| `tool_versions` | versions of all tools | ProvenanceRecord.payload |

### 12.2 Privacy Rules

- Do NOT store raw prompt content in provenance events by default
- Store hashes, references, or encrypted content blobs
- Use retention-controlled storage for content
- Respect GDPR data minimization

---

## 13. OTEL MAPPING

### 13.1 Concept Mapping

| MCPL Concept | OTel Mapping | Implementation |
|-------------|--------------|----------------|
| Intent/Workflow | `Trace` | Root span = intent |
| Task | `Span` (child of trace) | One span per task |
| Execution | `Span` | Attributes: execution_id, attempt_count |
| Attempt | `Span` (child of execution span) | Attributes: attempt_id, attempt_number |
| Model invocation | `Span` | SemiConv GenAI attributes |
| Decision | `Event` on parent span | Decision-specific attributes |
| Tool call | `Span` | Tool name, args hash, result hash |
| Artifact | `Span` attribute or Event | Artifact ID, hash, type |
| Verification | `Span` | Verification ID, status, method |
| State change | `Event` (annotates span) | State diff, scope |

### 13.2 Required Span Attributes

```python
# Execution span attributes
OTEL_ATTR_EXECUTION_ID = "muscal.execution.id"
OTEL_ATTR_TASK_ID = "muscal.task.id"
OTEL_ATTR_INTENT_ID = "muscal.intent.id"
OTEL_ATTR_CORRELATION_ID = "muscal.correlation.id"
OTEL_ATTR_TENANT_ID = "muscal.tenant.id"

# Tool call attributes
OTEL_ATTR_TOOL_NAME = "muscal.tool.name"
OTEL_ATTR_TOOL_ARGS_HASH = "muscal.tool.args_hash"
OTEL_ATTR_TOOL_RESULT_HASH = "muscal.tool.result_hash"

# Verification attributes
OTEL_ATTR_VERIFICATION_ID = "muscal.verification.id"
OTEL_ATTR_VERIFICATION_STATUS = "muscal.verification.status"
OTEL_ATTR_VERIFIER_TYPE = "muscal.verifier.type"
```

### 13.3 Required Span Events

```python
# Decision event
OTEL_EVENT_DECISION = "muscal.decision"
# Attributes: decision_id, decision_type, selected, candidates

# Verification event
OTEL_EVENT_VERIFICATION = "muscal.verification"
# Attributes: verification_id, status, verifier_type, confidence

# State change event
OTEL_EVENT_STATE_CHANGED = "muscal.state.changed"
# Attributes: state_id, artifact_id, previous_hash, current_hash
```

### 13.4 What MUST NOT Be Stored in OTel

- Full provenance DAG (too large for span metadata)
- Signed receipts
- Verification evidence blobs
- Long causal chains
- Content blobs (use external store + span correlation)

---

## 14. W3C PROV MAPPING

### 14.1 Entity Mapping

| MCPL Entity | PROV Type | PROV Class |
|-------------|-----------|------------|
| Intent | Entity | `prov:Entity` + `muscal:Intent` |
| Task | Entity | `prov:Entity` + `muscal:Task` |
| Agent | Agent | `prov:Agent` |
| Model | Agent | `prov:Agent` + `muscal:Model` |
| ModelOutput | Entity | `prov:Entity` + `muscal:ModelOutput` |
| Decision | Activity | `prov:Activity` (transforms input → output) |
| Execution | Activity | `prov:Activity` |
| ToolCall | Activity | `prov:Activity` + `muscal:ToolCall` |
| Artifact | Entity | `prov:Entity` |
| State | Entity | `prov:Entity` + `muscal:State` |
| Verification | Activity | `prov:Activity` + `muscal:Verification` |
| Human | Agent | `prov:Agent` + `prov:Person` |
| Policy | Entity | `prov:Entity` + `muscal:Policy` |
| Join | Activity | `prov:Activity` + `muscal:Join` |

### 14.2 Relationship Mapping

| MCPL Relationship | PROV Relationship |
|------------------|-------------------|
| `decomposes_into` | `prov:wasDerivedFrom` (with specialization) |
| `assigned_to` | `prov:wasAssociatedWith` |
| `invokes` | `prov:used` |
| `produces` | `prov:wasGeneratedBy` |
| `considered_by` | `prov:wasDerivedFrom` |
| `authorizes` | `prov:wasInformedBy` |
| `has_attempt` | `prov:wasDerivedFrom` |
| `invokes` (tool) | `prov:used` |
| `produces` (artifact) | `prov:wasGeneratedBy` |
| `changes` (state) | `prov:wasDerivedFrom` |
| `verified_by` | `prov:wasGeneratedBy` |
| `recorded_in` | `prov:wasDerivedFrom` |

### 14.3 Extension Classes

MUSCAL publishes a PROV-N vocabulary document with extension classes:
- `muscal:Intent` — intent entity
- `muscal:Task` — task entity
- `muscal:Model` — model agent
- `muscal:ModelOutput` — model output entity
- `muscal:ToolCall` — tool call activity
- `muscal:Verification` — verification activity
- `muscal:Policy` — policy entity
- `muscal:Join` — join activity

---

## 15. STORAGE ARCHITECTURE

### 15.1 Development Mode (SQLite)

```sql
-- New MCPL tables in muscal.db

CREATE TABLE IF NOT EXISTS mcpl_intents (
    intent_id TEXT PRIMARY KEY,
    description TEXT,
    created_at TEXT,
    correlation_id TEXT,
    causation_id TEXT,
    tenant_id TEXT,
    status TEXT DEFAULT 'created',
    metadata TEXT DEFAULT '{}'
);

CREATE TABLE IF NOT EXISTS mcpl_tasks (
    task_id TEXT PRIMARY KEY,
    intent_id TEXT,
    description TEXT,
    created_at TEXT,
    correlation_id TEXT,
    causation_id TEXT,
    tenant_id TEXT,
    status TEXT DEFAULT 'created',
    agent_id TEXT,
    join_id TEXT,
    metadata TEXT DEFAULT '{}',
    FOREIGN KEY (intent_id) REFERENCES mcpl_intents(intent_id)
);

CREATE TABLE IF NOT EXISTS mcpl_decisions (
    decision_id TEXT PRIMARY KEY,
    decision_type TEXT,
    task_id TEXT,
    agent_id TEXT,
    created_at TEXT,
    correlation_id TEXT,
    causation_id TEXT,
    tenant_id TEXT,
    status TEXT DEFAULT 'active',
    reasoning TEXT,
    confidence REAL DEFAULT 0.0,
    model_output_id TEXT,
    parent_decision_id TEXT,
    -- AgentDecision fields
    candidates TEXT DEFAULT '[]',
    selected TEXT DEFAULT '',
    selection_rationale TEXT DEFAULT '',
    -- PolicyDecision fields
    policy_id TEXT DEFAULT '',
    policy_version TEXT DEFAULT '',
    match_result TEXT DEFAULT '',
    -- HumanDecision fields
    human_action TEXT DEFAULT '',
    human_id TEXT DEFAULT '',
    automated_decision_id TEXT DEFAULT '',
    rationale TEXT DEFAULT ''
);

CREATE TABLE IF NOT EXISTS mcpl_executions (
    execution_id TEXT PRIMARY KEY,
    task_id TEXT,
    tool_name TEXT,
    created_at TEXT,
    correlation_id TEXT,
    causation_id TEXT,
    tenant_id TEXT,
    status TEXT DEFAULT 'requested',
    authorization_id TEXT,
    decision_id TEXT,
    attempt_count INTEGER DEFAULT 0,
    replay_of TEXT DEFAULT '',
    replay_classification TEXT DEFAULT '',
    metadata TEXT DEFAULT '{}',
    FOREIGN KEY (task_id) REFERENCES mcpl_tasks(task_id)
);

CREATE TABLE IF NOT EXISTS mcpl_attempts (
    attempt_id TEXT PRIMARY KEY,
    execution_id TEXT,
    attempt_number INTEGER,
    created_at TEXT,
    started_at TEXT DEFAULT '',
    completed_at TEXT DEFAULT '',
    status TEXT DEFAULT 'started',
    error TEXT DEFAULT '',
    error_type TEXT DEFAULT '',
    duration_ms REAL DEFAULT 0.0,
    result_hash TEXT DEFAULT '',
    receipt_id TEXT DEFAULT '',
    tenant_id TEXT,
    FOREIGN KEY (execution_id) REFERENCES mcpl_executions(execution_id)
);

CREATE TABLE IF NOT EXISTS mcpl_artifacts (
    artifact_id TEXT PRIMARY KEY,
    name TEXT,
    artifact_type TEXT,
    content_hash TEXT,
    content_ref TEXT,
    mime_type TEXT DEFAULT '',
    size_bytes INTEGER DEFAULT 0,
    created_at TEXT,
    tool_call_id TEXT,
    execution_id TEXT,
    tenant_id TEXT,
    metadata TEXT DEFAULT '{}'
);

CREATE TABLE IF NOT EXISTS mcpl_verifications (
    verification_id TEXT PRIMARY KEY,
    subject_id TEXT,
    subject_type TEXT,
    verifier_type TEXT,
    verifier_id TEXT,
    method TEXT DEFAULT '',
    expected_condition TEXT DEFAULT '{}',
    observed_result TEXT DEFAULT '{}',
    status TEXT DEFAULT 'requested',
    confidence REAL DEFAULT 0.0,
    evidence_ref TEXT DEFAULT '',
    created_at TEXT,
    verified_at TEXT DEFAULT '',
    correlation_id TEXT,
    causation_id TEXT,
    tenant_id TEXT,
    decision_id TEXT DEFAULT ''
);

CREATE TABLE IF NOT EXISTS mcpl_provenance_events (
    event_id TEXT PRIMARY KEY,
    schema_version TEXT DEFAULT '1.0.0',
    parent_id TEXT DEFAULT '',
    causation_id TEXT DEFAULT '',
    correlation_id TEXT DEFAULT '',
    event_type TEXT,
    timestamp TEXT,
    tenant_id TEXT DEFAULT '',
    actor TEXT DEFAULT '{}',
    subject TEXT DEFAULT '{}',
    causal_links TEXT DEFAULT '[]',
    payload TEXT DEFAULT '{}',
    integrity TEXT DEFAULT '{}',
    retention TEXT DEFAULT '{}'
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_mcpl_tasks_intent ON mcpl_tasks(intent_id);
CREATE INDEX IF NOT EXISTS idx_mcpl_executions_task ON mcpl_executions(task_id);
CREATE INDEX IF NOT EXISTS idx_mcpl_attempts_execution ON mcpl_attempts(execution_id);
CREATE INDEX IF NOT EXISTS idx_mcpl_decisions_task ON mcpl_decisions(task_id);
CREATE INDEX IF NOT EXISTS idx_mcpl_artifacts_execution ON mcpl_artifacts(execution_id);
CREATE INDEX IF NOT EXISTS idx_mcpl_verifications_subject ON mcpl_verifications(subject_id);
CREATE INDEX IF NOT EXISTS idx_mcpl_events_type ON mcpl_provenance_events(event_type);
CREATE INDEX IF NOT EXISTS idx_mcpl_events_correlation ON mcpl_provenance_events(correlation_id);
CREATE INDEX IF NOT EXISTS idx_mcpl_events_causation ON mcpl_provenance_events(causation_id);
CREATE INDEX IF NOT EXISTS idx_mcpl_events_timestamp ON mcpl_provenance_events(timestamp);
```

### 15.2 Production Mode (Transactional Outbox + Object Storage)

For production:

1. **Transactional Outbox**: Critical provenance events written to outbox table in application DB, then CDC'd to external store
2. **Object Storage**: Full provenance payloads stored in S3/GCS (JSONL format, gzip compressed)
3. **Query Index**: DynamoDB/PostgreSQL index for queryable fields (event_type, correlation_id, causation_id, tenant_id, timestamp)
4. **No business state duplication**: Store references and hashes, not full business data

### 15.3 Migration Path

```
SQLite (dev) → Object Storage + Index (prod)
  1. Same schema in both
  2. Same API in both
  3. Configuration-driven backend selection
  4. No code changes required for migration
```

---

## 16. REPOSITORY INTEGRATION MAP

### 16.1 Component Integration

| Component | File | Current Behavior | MCPL Integration |
|-----------|------|------------------|------------------|
| **kernel.py** | `kernel.py` | 8-stage pipeline with 14 hooks | Add MCPL emission hooks at each stage |
| **event_bus.py** | `event_bus.py` | In-memory pub/sub | Subscribe MCPL listener → persist events |
| **EventStore** | `runtime/event_store.py` | SQLite event persistence | **Extend** with MCPL columns (already has execution_id, correlation_id, causation_id) |
| **ExecutionReceipt** | `features/tool_runtime/tool_runtime.py` | SHA-256 integrity hash | **Extend** with attempt_id field |
| **VerificationResult** | `features/tool_runtime/tool_runtime.py` | Status enum + expected/observed | **Extend** with verifier_type, subject_type, confidence |
| **ExecutionContext** | `features/identity/execution_context.py` | Thread-local context | **Extend** with intent_id, task_id |
| **DecisionWriter** | `features/provenance/decision_writer.py` | Writes to decisions table | **Extend** with decision_type decomposition |
| **ProvenanceResolver** | `features/provenance/resolver.py` | Post-hoc reconstruction | **Add** real-time emission capability |
| **EvidenceClassifier** | `features/provenance/classifier.py` | Classification methods | No change needed |
| **MetaEvaluator** | `features/provenance/evaluation.py` | Quality evaluation | No change needed |
| **trace_engine.py** | `trace_engine.py` | In-memory CLI trace | **Replace** with OTel-compatible spans |

### 16.2 Files to Create

```
features/provenance/mcpl_schema.py           — MCPL entity types
features/provenance/mcpl_events.py           — Event type registry + emission
features/provenance/mcpl_emitter.py          — Provenance event emitter
features/provenance/verification_engine.py   — Verification engine + registry
features/provenance/verifiers/               — Built-in verifiers
  features/provenance/verifiers/deterministic.py
  features/provenance/verifiers/schema.py
  features/provenance/verifiers/invariant.py
  features/provenance/verifiers/rule_engine.py
features/provenance/mcpl_store.py            — MCPL persistence layer
features/provenance/mcpl_query.py            — Query interface
features/provenance/mcpl_otel.py             — OTel mapping
features/provenance/mcpl_prov.py             — W3C PROV mapping
features/provenance/kernel_hooks.py          — Kernel integration hooks
tests/provenance/test_mcpl_schema.py
tests/provenance/test_mcpl_events.py
tests/provenance/test_verification_engine.py
tests/provenance/test_mcpl_store.py
tests/provenance/test_mcpl_query.py
tests/provenance/test_mcpl_otel.py
tests/provenance/test_mcpl_security.py
```

### 16.3 Files to Modify

```
features/identity/execution_context.py      — Add intent_id, task_id
features/identity/reality.py                — Add attempt_status enum
features/tool_runtime/tool_runtime.py       — Add attempt_id to ExecutionReceipt
features/provenance/models.py               — Add new entity types
features/provenance/decision_writer.py      — Add decision_type support
features/provenance/context.py              — Add intent_id, task_id context
runtime/event_store.py                      — Add MCPL column support
runtime/database.py                         — Add MCPL table creation
kernel.py                                   — Add MCPL emission hooks
```

---

## 17. MIGRATION/RECONCILIATION PLAN

### 17.1 Phase 1: Schema Extension (Week 1)

1. Create `features/provenance/mcpl_schema.py` with all entity types
2. Extend `features/identity/execution_context.py` with `intent_id`, `task_id`
3. Extend `features/tool_runtime/tool_runtime.py:ExecutionReceipt` with `attempt_id`
4. Add MCPL tables to `runtime/database.py`
5. All existing tests must continue to pass

### 17.2 Phase 2: Event Emission (Week 2)

1. Create `features/provenance/mcpl_emitter.py`
2. Create `features/provenance/mcpl_events.py` (event type registry)
3. Add emission hooks to `kernel.py` pipeline stages
4. Wire emitter to `EventStore`
5. Integration tests for event emission

### 17.3 Phase 3: Verification Engine (Week 3)

1. Create `features/provenance/verification_engine.py`
2. Create built-in verifiers (deterministic, schema, invariant, rule_engine)
3. Create `VerifierRegistry`
4. Extend `VerificationResult` with new fields
5. Integration tests for verification

### 17.4 Phase 4: Query & Reconstruction (Week 4)

1. Create `features/provenance/mcpl_store.py`
2. Create `features/provenance/mcpl_query.py`
3. Extend `ProvenanceResolver` for real-time emission
4. Causal graph reconstruction tests

### 17.5 Phase 5: OTel + PROV Mapping (Week 5)

1. Create `features/provenance/mcpl_otel.py`
2. Create `features/provenance/mcpl_prov.py`
3. Map all MCPL entities to OTel spans/attributes
4. Map all MCPL entities to PROV entities/activities
5. OTel exporter integration tests

### 17.6 Phase 6: Security & Adversarial Tests (Week 6)

1. Create `tests/provenance/test_mcpl_security.py`
2. Implement all adversarial test cases
3. Verify all bypass paths are blocked
4. Final regression test suite

---

## 18. TEST STRATEGY

### 18.1 Unit Tests

| Test File | Coverage |
|-----------|----------|
| `test_mcpl_schema.py` | All entity types, field validation, serialization |
| `test_mcpl_events.py` | Event type registry, event creation, event validation |
| `test_verification_engine.py` | All verifier types, lifecycle, evidence classification |
| `test_mcpl_store.py` | SQLite persistence, CRUD operations, migration |
| `test_mcpl_query.py` | Query interface, causal graph traversal |

### 18.2 Integration Tests

| Test File | Coverage |
|-----------|----------|
| `test_mcpl_kernel_hooks.py` | End-to-end: kernel pipeline → MCPL events |
| `test_mcpl_retry.py` | Retry accounting, attempt tracking |
| `test_mcpl_replay.py` | Replay metadata, replay_of tracking |
| `test_mcpl_parallel.py` | Parallel execution, join conditions |
| `test_mcpl_decision.py` | Decision decomposition, causal chain |
| `test_mcpl_human.py` | Human decision recording, override tracking |

### 18.3 Security Tests

| Test File | Coverage |
|-----------|----------|
| `test_mcpl_security.py` | All adversarial scenarios from Section 19 |

### 18.4 Existing Test Compatibility

All 547 existing tests MUST continue to pass after each phase. MCPL is additive — no existing behavior changes.

---

## 19. SECURITY/ADVERSARIAL TEST PLAN

### 19.1 Attack Vectors

| # | Attack | Severity | Mitigation | Test |
|---|--------|----------|------------|------|
| S1 | Fabricate execution success | HIGH | ExecutionReceipt integrity hash + verification independence | Test: forged receipt fails integrity check |
| S2 | Fabricate receipts | HIGH | Receipt signed by UTR only; receipt_id is UUIDv7 | Test: external receipt not accepted |
| S3 | Alter verification results | HIGH | Verification stored independently; hash chain | Test: modified verification detected |
| S4 | Alter expected state after execution | HIGH | Expected state frozen before execution; hash committed | Test: post-hoc modification detected |
| S5 | Replay without distinction | MEDIUM | replay_of field; new execution_id for replay | Test: replay has distinct provenance |
| S6 | Confuse attempt_id and execution_id | MEDIUM | Schema validation; attempt_id must belong to execution_id | Test: cross-reference validation |
| S7 | Bypass policy decisions | HIGH | PolicyDecision recorded before execution; required for authorization | Test: execution without policy decision flagged |
| S8 | Bypass human approval | HIGH | HumanDecision recorded; approval required before execution | Test: execution without approval flagged |
| S9 | Create false causal links | MEDIUM | Causal links validated against entity existence | Test: dangling references detected |
| S10 | Claim simulation as actual execution | HIGH | ExecutionMode enforced; simulated cannot produce receipt | Test: simulated + verified = INVALID |
| S11 | Inject false provenance events | MEDIUM | Event IDs are UUIDv7; duplicate detection | Test: duplicate event_id rejected |

### 19.2 Test Implementation

Each attack vector has:
1. Attack scenario description
2. Expected mitigation behavior
3. Automated test that attempts the attack
4. Verification that mitigation blocks the attack
5. Regression test that runs in CI

---

## 20. IMPLEMENTATION SEQUENCE

### Batch 1: Foundation (Week 1)
```
1. features/provenance/mcpl_schema.py           — All entity types
2. features/provenance/mcpl_events.py            — Event type registry
3. features/identity/execution_context.py        — Extend with intent_id, task_id
4. features/tool_runtime/tool_runtime.py         — Add attempt_id to ExecutionReceipt
5. runtime/database.py                           — Add MCPL tables
6. tests/provenance/test_mcpl_schema.py          — Schema tests
```

### Batch 2: Emission (Week 2)
```
7. features/provenance/mcpl_emitter.py           — Event emitter
8. features/provenance/mcpl_store.py             — SQLite persistence
9. features/provenance/kernel_hooks.py           — Kernel integration
10. kernel.py                                     — Add MCPL emission hooks
11. tests/provenance/test_mcpl_events.py         — Event tests
12. tests/provenance/test_mcpl_store.py          — Store tests
```

### Batch 3: Verification (Week 3)
```
13. features/provenance/verification_engine.py   — Verification engine
14. features/provenance/verifiers/deterministic.py
15. features/provenance/verifiers/schema.py
16. features/provenance/verifiers/invariant.py
17. features/provenance/verifiers/rule_engine.py
18. tests/provenance/test_verification_engine.py — Verification tests
```

### Batch 4: Query (Week 4)
```
19. features/provenance/mcpl_query.py            — Query interface
20. features/provenance/resolver.py              — Extend for MCPL
21. tests/provenance/test_mcpl_query.py          — Query tests
```

### Batch 5: OTel + PROV (Week 5)
```
22. features/provenance/mcpl_otel.py             — OTel mapping
23. features/provenance/mcpl_prov.py             — W3C PROV mapping
24. tests/provenance/test_mcpl_otel.py           — OTel tests
```

### Batch 6: Security (Week 6)
```
25. tests/provenance/test_mcpl_security.py       — All adversarial tests
26. tests/provenance/test_mcpl_retry.py          — Retry tests
27. tests/provenance/test_mcpl_replay.py         — Replay tests
28. tests/provenance/test_mcpl_parallel.py       — Parallel tests
29. tests/provenance/test_mcpl_decision.py       — Decision tests
30. tests/provenance/test_mcpl_human.py          — Human decision tests
```

---

## 21. STATUS SUMMARY

### MC-006 STATUS

```
ARCHITECTURE:      READY
IMPLEMENTATION:    READY
P0 ISSUES:         NONE (all resolved in MC-005)
P1 ISSUES:         NONE (deferred to Phase 2)
```

### Files Requiring Change

| File | Change | Priority |
|------|--------|----------|
| `features/identity/execution_context.py` | Add intent_id, task_id | P0 |
| `features/identity/reality.py` | Add attempt_status enum | P0 |
| `features/tool_runtime/tool_runtime.py` | Add attempt_id to ExecutionReceipt | P0 |
| `features/provenance/models.py` | Add new entity types | P0 |
| `features/provenance/decision_writer.py` | Add decision_type support | P0 |
| `features/provenance/context.py` | Add intent_id, task_id context | P0 |
| `runtime/event_store.py` | Add MCPL column support | P0 |
| `runtime/database.py` | Add MCPL table creation | P0 |
| `kernel.py` | Add MCPL emission hooks | P1 |
| `features/provenance/resolver.py` | Extend for MCPL | P1 |

### Files to Create

| File | Purpose | Priority |
|------|---------|----------|
| `features/provenance/mcpl_schema.py` | MCPL entity types | P0 |
| `features/provenance/mcpl_events.py` | Event type registry | P0 |
| `features/provenance/mcpl_emitter.py` | Provenance event emitter | P0 |
| `features/provenance/mcpl_store.py` | MCPL persistence layer | P0 |
| `features/provenance/verification_engine.py` | Verification engine | P0 |
| `features/provenance/verifiers/deterministic.py` | Deterministic verifier | P0 |
| `features/provenance/verifiers/schema.py` | Schema verifier | P0 |
| `features/provenance/verifiers/invariant.py` | Invariant verifier | P0 |
| `features/provenance/verifiers/rule_engine.py` | Rule engine verifier | P0 |
| `features/provenance/mcpl_query.py` | Query interface | P1 |
| `features/provenance/mcpl_otel.py` | OTel mapping | P1 |
| `features/provenance/mcpl_prov.py` | W3C PROV mapping | P1 |
| `features/provenance/kernel_hooks.py` | Kernel integration | P1 |
| `tests/provenance/test_mcpl_schema.py` | Schema tests | P0 |
| `tests/provenance/test_mcpl_events.py` | Event tests | P0 |
| `tests/provenance/test_verification_engine.py` | Verification tests | P0 |
| `tests/provenance/test_mcpl_store.py` | Store tests | P0 |
| `tests/provenance/test_mcpl_query.py` | Query tests | P1 |
| `tests/provenance/test_mcpl_otel.py` | OTel tests | P1 |
| `tests/provenance/test_mcpl_security.py` | Security tests | P0 |
| `tests/provenance/test_mcpl_retry.py` | Retry tests | P0 |
| `tests/provenance/test_mcpl_replay.py` | Replay tests | P0 |
| `tests/provenance/test_mcpl_parallel.py` | Parallel tests | P0 |
| `tests/provenance/test_mcpl_decision.py` | Decision tests | P0 |
| `tests/provenance/test_mcpl_human.py` | Human decision tests | P0 |

### Tests to Create

| Test | Coverage | Priority |
|------|----------|----------|
| `test_mcpl_schema.py` | All entity types, field validation, serialization | P0 |
| `test_mcpl_events.py` | Event type registry, event creation | P0 |
| `test_verification_engine.py` | All verifier types, lifecycle | P0 |
| `test_mcpl_store.py` | SQLite persistence, CRUD | P0 |
| `test_mcpl_query.py` | Query interface, causal graph | P1 |
| `test_mcpl_kernel_hooks.py` | End-to-end kernel integration | P1 |
| `test_mcpl_otel.py` | OTel mapping | P1 |
| `test_mcpl_security.py` | All adversarial scenarios | P0 |
| `test_mcpl_retry.py` | Retry accounting | P0 |
| `test_mcpl_replay.py` | Replay metadata | P0 |
| `test_mcpl_parallel.py` | Parallel execution | P0 |
| `test_mcpl_decision.py` | Decision decomposition | P0 |
| `test_mcpl_human.py` | Human decision recording | P0 |

### Security Risks

| Risk | Severity | Mitigation |
|------|----------|------------|
| Forged execution success | HIGH | Receipt integrity + verification independence |
| Fabricated receipts | HIGH | UTR-only receipt generation |
| Altered verification | HIGH | Independent verification storage |
| Simulation as execution | HIGH | ExecutionMode enforcement |
| Causal link injection | MEDIUM | Entity existence validation |

### Next Implementation Batch

**Batch 1: Foundation** — Weeks 1-2
1. Create `features/provenance/mcpl_schema.py`
2. Create `features/provenance/mcpl_events.py`
3. Extend `features/identity/execution_context.py`
4. Extend `features/tool_runtime/tool_runtime.py`
5. Add MCPL tables to `runtime/database.py`
6. Create `features/provenance/mcpl_emitter.py`
7. Create `features/provenance/mcpl_store.py`
8. Add emission hooks to `kernel.py`

### Estimated Iterations to Production Readiness

**6 batches × 1 week each = 6 weeks**

With 547 existing tests passing at 100%, MCPL is additive and non-breaking. Each batch can be merged independently with full test compatibility.

---

*MC-006 Technical Specification v1.0 — 2026-07-24*
*Based on repository inspection of MUSCAL CORE v0.8+*
*Ready for implementation.*
