# Interface Layer Audit

## Status: Complete

## Existing Capabilities

| Component | File | Status |
|-----------|------|--------|
| Browser Tool | `features/tools/browser_tool.py` | **Stub** — no actual browser integration |
| Desktop Tool | `features/tools/desktop_tool.py` | **Stub** — no actual desktop integration |
| OpenCode Adapter | `features/bridge/opencode_adapter.py` | **Functional** — subprocess-based task execution |
| OpenCode Tool Wrapper | `features/tools/opencode_tool.py` | **Functional** — wraps OpenCodeAdapter as a tool |
| Tool Registry | `features/tools/registry.py` | **Complete** — 10 built-in tool definitions |
| Tool Executor | `features/tools/executor.py` | **Complete** — dispatch with policy + approval + audit |
| Tool Policy | `features/tools/policy.py` | **Complete** — autonomy-level gating |
| Tool Audit | `features/tools/audit.py` | **Complete** — event recording |
| Tool Approval | `features/tools/approval.py` | **Complete** — approval request lifecycle |
| MCP (MCPL) | `features/provenance/mcpl_*.py` | **Provenance-focused** — not a general MCP gateway |

## Missing Adapters

- **Browser**: No Playwright/Selenium integration. `navigate()` and `screenshot()` return "not implemented".
- **Desktop**: No PyAutoGUI/AT-SPI/Win32 integration. `click()` and `type_text()` return "not implemented".
- **MCP Gateway**: No generic MCP tool discovery, schema validation, or request routing.
- **Interface Models**: No `InterfaceRequest`, `InterfaceResponse`, `InterfaceCapability`, or `InterfaceSession` types.
- **Interface Events**: No `interface.*` events in the runtime event system.

## Security Risks

1. **No interface-layer policy enforcement**: The existing Tool Governance chain (policy → approval → audit) is not abstracted for interface adapters.
2. **Browser stub returns success=false, error defined**: No security risk currently, but a real browser integration must enforce URL allowlists, content sanitization, and session isolation.
3. **Desktop stub returns success=false, error defined**: A real desktop integration must enforce action allowlists, coordinate confirmation, and isolate input events.
4. **No identity tracking per interface session**: Interface actions cannot be traced back to specific sessions or users without InterfaceSession.
5. **No interface-level verification**: Verification is applied at tool/kernel level but not at the external interface boundary.

## Ownership Boundaries

| Boundary | Owner | Description |
|----------|-------|-------------|
| Kernel | reasoning | Intent/goal/strategy creation |
| Runtime | execution | Session/checkpoint/execution lifecycle |
| Tool Governance | permission | Tool registry, policy, approval, audit |
| **Interface Gateway** | **connection** | New — browser, desktop, MCP adapters |
| Verification | validation | Result integrity checking |

## Recommendation

Create `features/interface_gateway/` with:
1. **Models** — InterfaceRequest, InterfaceResponse, InterfaceCapability, InterfaceSession
2. **Policy Adapter** — wraps ToolPolicy for interface-level gating
3. **Adapter Registry** — manages browser, desktop, MCP adapter instances
4. **Audit** — interface-specific audit trail
5. **Gateway** — central entry point coordinating policy → adapter → audit
6. **Browser Adapter** — governed browser interface (navigate, read, extract, screenshot)
7. **Desktop Adapter** — governed desktop interface (mouse, keyboard, window, filesystem)
8. **MCP Gateway** — MCP tool discovery, schema validation, request routing
9. **Benchmark Hooks** — latency, success, overhead, cost, resource measurement
