# ADR-014: Unified Tool Runtime

**Status:** ACCEPTED
**Date:** 2026-07-15
**Updated:** 2026-07-22 — E3.0.2 reconciliation expanded scope to 4 systems
**Updated:** 2026-08-01 — G2 Adjudication: status finalized (ACCEPTED), governance links added (G2-03)

## Context

MUSCAL currently operates **two independent tool runtimes** with overlapping responsibility, fragmented schemas, and no single execution authority:

### System A — `tools.py` (TOOL_REGISTRY)

| Tool | Executor | Schema |
|------|----------|--------|
| `filesystem.write` | ✅ `write()` | ✅ |
| `math.add` | ✅ `add()` | ✅ |
| `console.print` | ✅ `print_console()` | ✅ |
| `browser.open` | ❌ missing | ✅ |
| `browser.click` | ❌ missing | ✅ |
| `browser.type` | ❌ missing | ✅ |
| `browser.extract_text` | ❌ missing | ✅ |
| `browser.screenshot` | ❌ missing | ✅ |
| `browser.scroll` | ❌ missing | ✅ |
| `desktop.screenshot` | ❌ missing | ✅ |
| `desktop.type` | ❌ missing | ✅ |
| `desktop.click` | ❌ missing | ✅ |
| `desktop.open_app` | ❌ missing | ✅ |
| `desktop.move` | ❌ missing | ✅ |
| `desktop.keypress` | ❌ missing | ✅ |

**11 schemas defined, only 3 executors registered.** 8 browser/desktop tools are declared but will fail at runtime if called via `mel.py`.

### System B — `muscal_loop.py` (EXECUTORS + BrowserAgent)

| Tool | Executor | Schema | Allowlist |
|------|----------|--------|-----------|
| `console.print` | ✅ `_exec_console_print` | ✅ inline | ✅ |
| `browser.open` | ✅ `_exec_browser_open` → BrowserAgent | ✅ inline | ✅ |
| `browser.click` | ✅ `_exec_browser_click` → BrowserAgent | ✅ inline | ✅ |
| `browser.type` | ✅ `_exec_browser_type` → BrowserAgent | ✅ inline | ✅ |
| `opencode.run` | ✅ `_exec_opencode_run` | ✅ inline | ✅ subprocess allowlist |
| `file.write` | ✅ `_exec_file_write` | ✅ inline | ✅ path allowlist |

**6 tools with inline schema, separate BrowserAgent class, subprocess allowlist, and path allowlist.** No overlap with `tools.py` except `console.print`.

### Routing Layer — `mel.py`

```
mel.execute(plan)
  ├── browser.* / desktop.* → SystemAgentRuntime (system_runtime.py)
  └── other → TOOL_REGISTRY (tools.py)
```

`SystemAgentRuntime` delegates to `browser_tools.BrowserRuntime` / `desktop_tools.DesktopRuntime` — both missing on disk (handled via ImportError gracefully, but zero functionality).

### Fragmentation Summary

| Concern | System A (tools.py) | System B (muscal_loop.py) | Bridge (mel.py) |
|---------|-------------------|--------------------------|-----------------|
| Schema source | `TOOL_SCHEMAS` dict | inline `TOOL_SCHEMAS` | none |
| Validation | none | `validate_tasks()` + shell-scan | `SafetyViolation` |
| Browser | absent | `BrowserAgent` (Playwright) | `browser_tools.BrowserRuntime` (missing) |
| Desktop | absent | absent | `desktop_tools.DesktopRuntime` (missing) |
| Permissions | path-based | path + subprocess allowlists | BLOCKED_TOOLS + keywords |
| Return format | `dict` per function | `dict` per executor | `{"status","tool","result"} wrapped |

## Decision

Consolidate into a **Unified Tool Runtime (UTR)** with a single registry, single schema source, single validation pipeline, and plugin-based executor extension.

### Phase 1 — Schema Unification (spec freeze)

1. **`INSTRUMENTS.md`** becomes the single source of truth for tool schemas, replacing both `tools.py:TOOL_SCHEMAS` and `muscal_loop.py:TOOL_SCHEMAS`
2. Each schema entry includes:
   - Tool name (namespaced, e.g., `browser.open`)
   - Input args with types
   - Output shape
   - Constraints (timeout, size, path allowlist, etc.)
   - Safety class: `SAFE` / `RESTRICTED` / `SANDBOXED` / `BLOCKED`
3. Schema document is versioned (v1) and validated by CI

### Phase 2 — Unified Registry (implementation)

1. Replace `tools.py:TOOL_REGISTRY` with `UTR` class in `runtime/tool_runtime.py`:
   ```python
   class UnifiedToolRuntime:
       def __init__(self):
           self._executors: dict[str, Executor] = {}
           self._schemas: dict[str, ToolSchema] = {}
   
       def register(self, name: str, executor: Callable, schema: ToolSchema) -> None: ...
       def execute(self, name: str, args: dict) -> ToolResult: ...
       def validate(self, name: str, args: dict) -> ValidationResult: ...
       def available(self) -> list[str]: ...
   ```
2. Migrate `muscal_loop.py` executors into UTR:
   - `console.print` → UTR (trivial)
   - `browser.*` → UTR via `BrowserAgent` adapter (keep BrowserAgent as internal impl)
   - `opencode.run` → UTR as `RESTRICTED` executor
   - `file.write` → UTR as `RESTRICTED` executor
3. Add missing browser/desktop executors from TOOL_SCHEMAS into UTR
4. `tools.py` becomes a thin re-export layer (backward compat shim)
5. `mel.py` dispatches all tools through UTR instead of splitting between TOOL_REGISTRY and SART

### Phase 3 — Safety Layer Consolidation

1. Replace three separate safety systems (`muscal_loop:validate_tasks`, `SART:validate_step`, `TOOL_SCHEMAS:constraints`) with a single `SafetyGate`:
   ```python
   class SafetyGate:
       def check(self, tool: str, args: dict) -> SafetyResult:
           # check allowlists, shell metacharacters, path safety, blocklist
           ...
   ```
2. Browser/Desktop availability is checked at UTR level, not scattered across mel.py and SART
3. `system_runtime.py` becomes a wrapper around UTR for backward compat or is deprecated

## Migration Plan

| Step | What | Who |
|------|------|-----|
| 1 | Create `INSTRUMENTS.md` v1 with all 14 tool schemas unified | TOOL-001 |
| 2 | Create `runtime/tool_runtime.py` with UTR class | TOOL-001 |
| 3 | Migrate `muscal_loop.py:EXECUTORS` (6 tools) into UTR | TOOL-002 |
| 4 | Add browser executors to UTR (5 tools) | TOOL-003 |
| 5 | Add desktop executors to UTR (5 tools) | TOOL-003 |
| 6 | Rewire `mel.py` to use UTR | TOOL-004 |
| 7 | Add `SafetyGate` class, consolidate all validation | TOOL-004 |
| 8 | Deprecate `system_runtime.py` — redirect to UTR | TOOL-005 |
| 9 | Remove `muscal_loop.py` inline TOOL_SCHEMAS and EXECUTORS | TOOL-006 |
| 10 | Integration test: MKC → Bridge → MEL → UTR → Memory | TOOL-007 |

## Consequences

- **+** Single execution authority: every tool call goes through one validate→execute pipeline
- **+** No schema drift: `INSTRUMENTS.md` is the only source of truth
- **+** Plugin-friendly: new tool families register via `UTR.register()` in `features/`
- **+** Backward compatible: `tools.py`, `mel.py`, `system_runtime.py` keep working via shims
- **+** Safety consolidated: one `SafetyGate` instead of three partial validators
- **-** Migration requires changes to 4 files (tools.py, mel.py, system_runtime.py, muscal_loop.py)
- **-** BrowserAgent duplication (muscal_loop vs browser_tools) needs resolution
- **-** Desktop tools remain unimplemented until browser_tools/desktop_tools modules are created

## Compliance Check

- Core immutability preserved: UTR lives in `runtime/tool_runtime.py` (already in ALLOWED core paths)
- `mel.py`, `tools.py`, `system_runtime.py` are core files — modifications require `--allow-core-write`
- `muscal_loop.py` is NOT in the core allowlist — modifications are unrestricted
- No ADRs superseded: ADR-014 is additive

---

## E3.0.2 Correction — Expanded Scope (2026-07-22)

The independent repository reconciliation (D-E3.0.2-006) identified **4 independent execution systems**, not 2:

| # | System | Location | Executors | Reachability |
|---|--------|----------|-----------|-------------|
| A | TOOL_REGISTRY | `tools.py` | 3 (write, add, print_console) | HOT_PATH (via mel.py) |
| B | EXECUTORS + BrowserAgent | `muscal_loop.py` | 6 (print, browser*3, opencode.run, file.write) | EXPERIMENTAL (standalone loop) |
| C | SystemAgentRuntime | `system_runtime.py` | BrowserRuntime + DesktopRuntime (both **stubs** — modules missing on disk) | HOT_PATH (via mel.py, but silent fallback) |
| D | PermissionEngine + ToolExecutor | `permission_engine.py` | Reuses muscal_loop EXECUTORS | COLD_PATH |

### Key Findings for Consolidation Plan

1. **11/14 schemas in tools.py have no executor** — confirmed. ADR-014's Phase 1-3 must add 11 missing executors.
2. **browser_tools.py and desktop_tools.py don't exist** — `SystemAgentRuntime` silently fails for all browser/desktop operations.
3. **muscal_loop.py EXECUTORS (6) are the only complete browser implementation** — should be the migration source for UTR's browser executors.
4. **file.write vs filesystem.write naming conflict** — must be resolved during schema unification.
5. **permission_engine.py adds no unique execution capability** — can be deprecated; its risk-level classification should merge into SafetyGate.
6. **`muscal_loop.py` IS in the core allowlist** — correction to original compliance check: `muscal_loop.py` is listed as immutable in both `IMMUTABILITY_CONTRACT.md` and `guards/write_guard.py`.

### Updated Migration Plan

| Step | What | Source System | Target |
|------|------|---------------|--------|
| 1 | Create `INSTRUMENTS.md` v1 | All schemas | Unified schema |
| 2 | Create `runtime/tool_runtime.py` (UTR) | — | New |
| 3 | Migrate console.print, browser.* | muscal_loop.py EXECUTORS | UTR |
| 4 | Add filesystem.write + math.add | tools.py TOOL_REGISTRY | UTR |
| 5 | Add browser.extract_text, screenshot, scroll | tools.py schemas (new executors) | UTR |
| 6 | Add desktop.* executors | tools.py schemas (new executors) | UTR |
| 7 | Rewire mel.py → UTR | mel.py | UTR dispatch |
| 8 | Create SafetyGate | muscal_loop + system_runtime + permission_engine validators | Single validator |
| 9 | Deprecate system_runtime.py | system_runtime.py | Redirect to UTR |
| 10 | Remove inline EXECUTORS from muscal_loop.py | muscal_loop.py | Removed after migration |

---

## Governance Links (added 2026-08-01, G2-03 adjudication)

**Status rationale:** DRAFT → ACCEPTED. The E3.2 Trust Boundary Closure (D-E3.2-002-FINAL-CLOSURE.md)
confirms the UTR consolidation as implemented and certified ("E3.2 CONFIRMED CLOSED", 9 bypasses
closed, full suite 824 passed). ADR-014 implementation evidence:

| Link | Reference | Role |
|------|-----------|------|
| Reconciliation evidence | `docs/engineering/D-E3.0.2-006-TOOL-RUNTIME-CONSOLIDATION.md` (Status: CORRECTED) | 4-system consolidation scope |
| Implementation certification | `docs/engineering/D-E3.2-002-FINAL-CLOSURE.md` | E3.2 CLOSED — UTR→SafetyGate→Governance→Receipt→Verification chain |
| Implementation plan | `docs/governance/ADR-014-IMPLEMENTATION_PLAN_v1.1.md` | Step plan TOOL-001..TOOL-007 |
| Core rewiring | `muscal_loop.py`, `tools.py`, `mel.py`, `permission_engine.py`, `system_runtime.py` (G2-03 SANCTIONED) | EXECUTORS→UTR routing |
| Decision registry | `KNOWLEDGE_FOUNDATION/audit/DECISION_REGISTRY.md` D-036/D-037 | Adjudication sanction + status finalization |

**Residual items (not blocking ACCEPTED):** desktop/browser executors still stubbed in UTR
(ADR-014 Phase 1, step 5-6); `system_runtime.py` deprecation pending (step 9); UTR test
isolation tracked as FL-01a (see KNOWLEDGE_FOUNDATION/audit/G2_ADJUDICATION_REPORT.md).
