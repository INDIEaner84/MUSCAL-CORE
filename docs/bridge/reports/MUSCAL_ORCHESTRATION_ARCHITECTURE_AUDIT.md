# MUSCAL Orchestration Architecture Audit

## 1. Existing Components

| Component | Location | Role |
|---|---|---|
| TaskContract | `features/bridge/task_contract.py` | Task definition (id, project, objective, constraints, verification) |
| RuntimeCoordinator | `features/runtime/coordinator.py` | Session/checkpoint/observability management, bridge invocation |
| ApprovalPolicy | `features/runtime/models.py` | A0-A5 action-level permission matrix |
| AutonomyPolicy | `features/execution_guard/policy.py` | Code-level autonomy permissions with forbidden actions |
| AutonomyLevel | `features/execution_guard/models.py` | Enum A0-A5 |
| KnowledgeRetriever | `features/knowledge/retriever.py` | Relevance-scored knowledge retrieval |
| MREILCapture | `features/execution/mreil.py` | Resource metrics (latency, tokens, CPU, RAM) |
| BridgeOrchestrator | `features/bridge/orchestrator.py` | Single-model execution via OpenCode |
| ExecutionGuard | `features/execution_guard/guard.py` | Pre/post execution guard checks |
| SessionManager | `features/runtime/session_manager.py` | Session lifecycle |
| CheckpointManager | `features/runtime/checkpoint_manager.py` | Git/state checkpoints |

## 2. Where Orchestration Should Live

New module: `features/orchestration/`

Rationale:
- Orchestration is a **cognitive planning layer**, not a workflow engine — it analyzes tasks, selects agents, and builds execution plans
- It must NOT replace RuntimeCoordinator — it feeds into it
- Keeps agent routing/planning separate from execution lifecycle

## 3. Interaction with Runtime

```
CognitiveOrchestrator.plan(task)
    ↓
TaskAnalysis (category, complexity, risk, capabilities)
    ↓
KnowledgeRetrieval (context from past executions)
    ↓
AgentSelection (capability matching + policy)
    ↓
ExecutionPlan (steps, agents, controls)
    ↓
RuntimeCoordinator.execute(plan)    ← Runtime executes, orchestrator does not
```

The CognitiveOrchestrator **proposes** — Runtime **executes**.

## 4. Decisions Requiring Approval

| Decision | Approval Required |
|---|---|
| Agent selection for task | Yes (A3+ auto, A2 propose) |
| Autonomy level escalation | Yes (A4+ requires approval) |
| Multi-step plan execution | Yes (A3+ auto for modify/test) |
| External push/deploy | Yes (always requires confirmation) |

## 5. Reusable Components

- `TaskContract` → already models task structure
- `ApprovalPolicy` → can be used directly for action-level authorization
- `AutonomyLevel` → maps directly to orchestration autonomy
- `KnowledgeRetriever` → provides evidence context for agent selection
- `MREILCapture` → provides `evaluate_agent_efficiency()` interface
- `RuntimeCoordinator` → execution target for orchestration plans

## 6. Gaps Filled by Iteration 8

- No structured task analysis (complexity, risk, capability requirements)
- No agent capability registry (which model/agent does what)
- No capability-based agent selection
- No execution plan generation
- No MREIL efficiency interface for agent comparison

## 7. Authority Boundaries

```
Git                  = Source Authority
EventStore           = Execution History Authority
ADR                  = Architecture Decision Authority
Verification Layer   = Truth Validation Authority
Knowledge Layer      = Validated Experience
ExecutionGuard       = Safety Authority
CognitiveOrchestrator = Planning Authority (NEW — propose only)
RuntimeCoordinator    = Execution Authority (executes)
```
