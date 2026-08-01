# MUSCAL Cognitive Kernel Architecture Audit

## 1. Current Ownership

| Concern | Currently Owned By | Location | Status |
|---|---|---|---|
| **Intent** | TaskContract.objective | `features/bridge/task_contract.py` | Implicit string, no structure |
| **Goal** | TaskAnalysis (category, complexity, risk) | `features/orchestration/task_analyzer.py` | Implicit in analysis, not first-class |
| **Context** | Fragmented across 5+ subsystems | Various | No unified context |
| **Planning** | ExecutionPlanner | `features/orchestration/planner.py` | Step-based plans, no strategy layer |
| **Strategy** | None (direct mapping) | N/A | Missing — no strategy selection |
| **Execution** | RuntimeCoordinator | `features/runtime/coordinator.py` | Solid |
| **Safety** | ExecutionGuard | `features/execution_guard/guard.py` | Solid |
| **Knowledge** | Knowledge modules | `features/knowledge/` | Solid |
| **Tools** | ToolGovernance | `features/tools/` | Solid |
| **Optimization** | MREIL/Optimization | `features/optimization/` | Solid |

## 2. Overlaps

- **TaskAnalysis** (orchestration) and **TaskContract** (bridge) both describe the task — Kernel Intent merges them
- **ExecutionPlan** steps and **ToolRouter** both route work — Kernel Strategy decides which tools vs runtime
- **RuntimeState**, **KnowledgeRetriever**, **AgentProfileManager** all provide context — Kernel UnifiedContext merges them

## 3. Kernel Responsibilities

The Cognitive Kernel adds:

| Responsibility | Implementation |
|---|---|
| Convert TaskContract → structured Intent | IntentEngine |
| Decompose Intent → multiple Goals | GoalEngine |
| Merge all subsystem state → UnifiedContext | ContextEngine |
| Select Strategy from Intent + Goals | StrategyEngine |
| Coordinate pipeline: Intent → Goals → Context → Strategy → Planner → Runtime | CognitiveKernel |
| Emit kernel lifecycle events | Event emission in each engine |

## 4. What the Kernel Does NOT Own

| Concern | Remains With |
|---|---|
| Execution | RuntimeCoordinator |
| Verification | BridgeVerifier |
| Knowledge persistence | Knowledge modules |
| Tool governance | ToolGovernance |
| Event persistence | EventStore |
| Agent selection | AgentSelector |
| Session/checkpoint management | Runtime modules |

## 5. Integration

```
TaskContract
    ↓
CognitiveKernel.process()
    ├── IntentEngine.create(task)      → Intent
    ├── GoalEngine.create(intent)      → Goals
    ├── ContextEngine.build(...)       → UnifiedContext
    ├── StrategyEngine.select(...)     → Strategy
    ├── ExecutionPlanner.plan(...)     → Plan (existing)
    ├── AgentSelector.select(...)      → Selection (existing)
    └── RuntimeCoordinator.execute(...) → Result (existing)
```

**Existing CognitiveOrchestrator becomes a thin Kernel client.**
All existing modules remain unchanged.
