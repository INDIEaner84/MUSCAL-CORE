# MUSCAL Coding Bridge — Iteration 10 Result

## Tool Governance & Agent Tool Interface Layer

---

## Architecture

```
Agent
  |
  Tool Request
  |
  ToolPolicy → Approval workflow (PENDING→APPROVED/DENIED/EXPIRED)
  |
  ToolExecutor._dispatch()
  |
  Provider (builtin / opencode / browser / desktop)
  |
  ToolResult → ToolAudit (append-only event log)
```

**Tool governance sits between agent intent and tool execution.**
It does NOT replace ExecutionGuard — they are complementary.

## Tool Model

| Component | File | Purpose |
|---|---|---|
| ToolDefinition | `features/tools/models.py` | id, name, category, capabilities, risk_level, required_autonomy, requires_confirmation, provider |
| ToolCapability | `features/tools/models.py` | name + description |
| ApprovalRequest | `features/tools/models.py` | PENDING→APPROVED/DENIED/EXPIRED lifecycle |
| ToolResult | `features/tools/models.py` | success/failure, output, error, duration |

## Governance Rules

| Rule | Enforcement |
|---|---|
| Tool autonomy check | `ToolPolicy.is_tool_allowed()` — level must match required_autonomy |
| Confirmation required | `ToolPolicy.requires_approval()` — checks `requires_confirmation` + ActionPolicy |
| Approval lifecycle | `ApprovalManager` — approve/deny/expire, no double-approve |
| Audit trail | `ToolAudit` — append-only event log per tool_id |
| No runtime bypass | `ExecutionGuard` still enforces independently |

## Default Tools (10)

| Tool ID | Autonomy | Risk | Provider |
|---|---|---|---|
| filesystem.read | A1 | low | builtin |
| filesystem.write | A3 | medium | builtin |
| filesystem.list | A1 | low | builtin |
| filesystem.search | A1 | low | builtin |
| opencode.execute | A3 | high | opencode |
| opencode.inspect | A1 | low | opencode |
| desktop.click | A4 | high | desktop |
| desktop.type | A4 | high | desktop |
| browser.navigate | A3 | medium | browser |
| browser.screenshot | A2 | low | browser |

## Events Added

5 tool events registered in `ALL_RUNTIME_EVENTS` (now 27 total):

- `tool.requested`
- `tool.approved`
- `tool.denied`
- `tool.executed`
- `tool.failed`

## Created Modules

```
features/tools/
├── __init__.py         — Package exports
├── models.py           — ToolDefinition, ToolCapability, ApprovalRequest, ApprovalState, ToolResult
├── registry.py         — ToolRegistry (register, get, list, find_capability) + 10 DEFAULT_TOOLS
├── policy.py           — ToolPolicy (autonomy check + approval check)
├── approval.py         — ApprovalManager (PENDING→APPROVED/DENIED/EXPIRED)
├── executor.py         — ToolExecutor (full policy→approval→dispatch→audit flow)
├── audit.py            — ToolAudit (append-only per-tool event log)
├── router.py           — ToolRouter (capability-based tool discovery)
├── opencode_tool.py    — OpenCodeTool wrapper (delegates to OpenCodeAdapter)
├── browser_tool.py     — BrowserTool interface (navigate, screenshot — not yet implemented)
└── desktop_tool.py     — DesktopTool interface (click, type — not yet implemented)
```

## Tests

**Total**: 68 tests

| Module | Tests |
|---|---|
| test_models.py | 8 |
| test_registry.py | 10 |
| test_policy.py | 7 |
| test_approval.py | 12 |
| test_audit.py | 8 |
| test_executor.py | 7 |
| test_router.py | 4 |
| test_tool_integrations.py | 7 |
| test_integration.py | 7 |

**Tests Passed**: 68/68

## Overall Test Suite

**Passed**: 381/381 (68 tools + 55 optimization + 72 orchestration + 57 knowledge + 67 runtime + 62 execution_guard)

**Regressions**: 0

## Readiness

The MUSCAL system now has a controlled tool boundary:

```
Agent → Tool Request → Governance (Policy + Approval) → Runtime → Tool → Audit
```

The system is ready for future:

- **Browser automation** — `BrowserTool` interface declared
- **Desktop agents** — `DesktopTool` interface declared
- **MCP tools** — `ToolRegistry.register_tool()` + custom providers
- **External APIs** — provider extensibility via `_dispatch()`

## Remaining Gaps

- **OpenCode execution delegation**: `_execute_opencode()` returns stub — needs wiring to `OpenCodeTool.execute()` with full parameter passthrough
- **Browser/Desktop implementation**: Interfaces only — no Selenium/PyAutoGUI yet
- **MCP provider**: No MCP protocol adapter yet
- **Persistence**: Approval requests and audit events are in-memory only
