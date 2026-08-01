# MUSCAL Tool Governance Architecture Audit

## 1. Existing Tool Interfaces

| Interface | Location | Purpose |
|---|---|---|
| OpenCodeAdapter | `features/bridge/opencode_adapter.py` | Executes OpenCode CLI, returns OpenCodeResult |
| ExecutionGuard | `features/execution_guard/guard.py` | Pre/post execution safety checks |
| ApprovalPolicy | `features/runtime/models.py` | A0-A5 action-level permissions |
| AutonomyPolicy | `features/execution_guard/policy.py` | Code autonomy with forbidden actions |
| BridgeOrchestrator | `features/bridge/orchestrator.py` | Full execution pipeline |
| RuntimeObservability | `features/runtime/observability.py` | Event emission to EventStore |

## 2. Missing Abstraction

| Gap | Impact |
|---|---|
| No tool registry | Tools are hardcoded; no discovery |
| No tool-level policy | Tool access is not independently governed |
| No approval workflow | No PENDING/APPROVED/DENIED lifecycle |
| No tool audit trail | Tool usage not independently tracked |
| No capability-based tool discovery | Agent cannot find tools by capability |

## 3. Security Boundaries

```
Agent → Tool Request → Policy Check → Approval → Execution → Audit
                           ↓
                    ExecutionGuard (parallel safety)
```

Tool governance sits *between* agent intent and tool execution.
It does NOT replace ExecutionGuard — they are complementary.

## 4. Integration Strategy

- Tool registry is descriptive (no permissions)
- Tool policy uses existing ApprovalPolicy rules
- Tool approval adds PENDING/APPROVED/DENIED lifecycle
- OpenCodeAdapter is wrapped as `opencode_tool` — no logic duplication
- Browser/Desktop tools are interface-only for future implementation
- All tool events emitted via RuntimeObservability
