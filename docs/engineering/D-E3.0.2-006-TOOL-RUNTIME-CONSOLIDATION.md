# D-E3.0.2-006 — TOOL RUNTIME CONSOLIDATION SURFACE

**Status:** CORRECTED
**Supersedes:** D-E3.0-012 (§Tool Runtime), ADR-014 (status update)
**Date:** 2026-07-22

---

## 1. Previous Claim (E3.0)

ADR-014 identified "two independent tool runtimes" and proposed consolidation. The scope was understated.

## 2. Corrected Claim

**Four independent execution systems exist**, not two. Three are reachable through production paths:

| System | Location | Executors | Reachability |
|--------|----------|-----------|-------------|
| TOOL_REGISTRY | `tools.py` | 3 (write, add, print_console) | HOT_PATH (via mel.py) |
| EXECUTORS | `muscal_loop.py` | 6 (print, browser open/click/type, opencode.run, file.write) | EXPERIMENTAL (standalone) |
| SystemAgentRuntime | `system_runtime.py` | BrowserRuntime + DesktopRuntime (both stubs) | HOT_PATH (via mel.py for browser/desktop) |
| PermissionEngine+ToolExecutor | `permission_engine.py` | Reuses muscal_loop EXECUTORS | COLD_PATH |

## 3. Complete Inventory

### System A: `tools.py` (HOT_PATH)

| Tool | Executor | Schema | Executor Exists? | Reachable? |
|------|----------|--------|-----------------|------------|
| `filesystem.write` | `write()` | ✅ 3 fields | ✅ | ✅ (via mel.py → TOOL_REGISTRY) |
| `math.add` | `add()` | ✅ 3 fields | ✅ | ✅ |
| `console.print` | `print_console()` | ✅ 3 fields | ✅ | ✅ |
| `browser.open` | — | ✅ 5 fields | ❌ | ❌ (schema only) |
| `browser.click` | — | ✅ 2 fields | ❌ | ❌ |
| `browser.type` | — | ✅ 3 fields | ❌ | ❌ |
| `browser.extract_text` | — | ✅ 2 fields | ❌ | ❌ |
| `browser.screenshot` | — | ✅ 3 fields | ❌ | ❌ |
| `browser.scroll` | — | ✅ 2 fields | ❌ | ❌ |
| `desktop.screenshot` | — | ✅ 3 fields | ❌ | ❌ |
| `desktop.type` | — | ✅ 2 fields | ❌ | ❌ |
| `desktop.click` | — | ✅ 3 fields | ❌ | ❌ |
| `desktop.open_app` | — | ✅ 2 fields | ❌ | ❌ |
| `desktop.move` | — | ✅ 3 fields | ❌ | ❌ |
| `desktop.keypress` | — | ✅ 2 fields | ❌ | ❌ |

**Totals:** 14 schemas, 3 executors (11 missing executors)

### System B: `muscal_loop.py` (EXPERIMENTAL)

| Tool | Executor | Schema | Validation | Sandbox |
|------|----------|--------|-----------|---------|
| `console.print` | `_exec_console_print` | Inline | None | None |
| `browser.open` | `_exec_browser_open` → BrowserAgent | Inline | None | None |
| `browser.click` | `_exec_browser_click` → BrowserAgent | Inline | None | None |
| `browser.type` | `_exec_browser_type` → BrowserAgent | Inline | None | None |
| `opencode.run` | `_exec_opencode_run` | Inline | Tool allowlist + subprocess allowlist | Command prefix check |
| `file.write` | `_exec_file_write` | Inline | Path allowlist | None |

**Totals:** 6 tools, 6 executors, inline schemas, Playwright BrowserAgent, subprocess allowlist

### System C: `system_runtime.py` (HOT_PATH, via mel.py)

| Tool Category | Runtime | Status | Validation |
|---------------|---------|--------|-----------|
| `browser.*` (all) | `browser_tools.BrowserRuntime` | **MISSING** (ImportError → graceful fallback) | `SafetyViolation` (keyword + tool blocklist) |
| `desktop.*` (all) | `desktop_tools.DesktopRuntime` | **MISSING** (ImportError → graceful fallback) | Same |

**Reality:** When kernel.py processes a browser/desktop tool via mel.py, `SystemAgentRuntime.execute()` is called. It tries to import `browser_tools` and `desktop_tools`, which don't exist. The `ImportError` is caught and the runtime reports "not available." **Zero browser/desktop tools actually work in production.**

### System D: `permission_engine.py` (COLD_PATH)

| Component | Implementation | Notes |
|-----------|---------------|-------|
| `PermissionEngine` | Risk-level checker | 7 tools with risk levels (low/medium/high) |
| `ToolExecutor` | Wraps `muscal_loop.py:EXECUTORS` | Reuses System B executors |
| `ExecutionFirewall` | Check → Execute pipeline | Combines PermissionEngine + ToolExecutor |
| `run_muscal()` | Wraps ExecutionGovernor + LoopController | Orphaned (no callers) |

## 4. Overlap Analysis

| Tool Name | tools.py | muscal_loop.py | system_runtime.py | permission_engine.py |
|-----------|----------|---------------|-------------------|---------------------|
| `console.print` | ✅ Executor | ✅ Executor | ❌ | ✅ (via delegation) |
| `browser.open` | ❌ No executor | ✅ Executor | ✅ (stub) | ✅ (via delegation) |
| `browser.click` | ❌ No executor | ✅ Executor | ✅ (stub) | ✅ (via delegation) |
| `browser.type` | ❌ No executor | ✅ Executor | ✅ (stub) | ✅ (via delegation) |
| `browser.extract_text` | ❌ No executor | ❌ | ❌ | ❌ |
| `browser.screenshot` | ❌ No executor | ❌ | ❌ | ❌ |
| `browser.scroll` | ❌ No executor | ❌ | ❌ | ❌ |
| `filesystem.write` (tools) vs `file.write` (muscal) | ✅ Executor | ✅ Executor (different name) | ❌ | ❌ |
| `math.add` | ✅ Executor | ❌ | ❌ | ❌ |
| `opencode.run` | ❌ | ✅ Executor | ❌ | ✅ (via delegation) |

## 5. Confirmed: 11/14 Schemas Have No Executor

**Confirmed.** In `tools.py`, 14 schemas are defined but only 3 (`filesystem.write`, `math.add`, `console.print`) have corresponding functions in `TOOL_REGISTRY`. The remaining 11 browser/desktop tools have schemas but will raise `Exception("Unknown tool")` if called via `mel.py` → `TOOL_REGISTRY[tool_name]`.

## 6. Schema Sources

| Source | Location | Schema Format | Count |
|--------|----------|--------------|-------|
| Primary | `tools.py:TOOL_SCHEMAS` | `{tool: {"input": {}, "output": {}, "constraints": []}}` | 14 |
| Inline | `muscal_loop.py:TOOL_SCHEMAS` | `{tool: {"args": {}}}` | 6 |
| Risk list | `permission_engine.py:ALLOWED_TOOLS` | `{tool: {"risk": str}}` | 7 |

## 7. Validation Systems

| System | Validation | Scope |
|--------|-----------|-------|
| `mel.py` | None (relies on TOOL_REGISTRY key lookup) | Tools called via kernel hot path |
| `muscal_loop.py:validate_tasks()` | Tool allowlist + schema type check + shell metacharacter scan | Tools called via standalone loop |
| `system_runtime.py:validate_step()` | Blocked tools list + keyword scan | Browser/desktop tools via kernel |
| `permission_engine.py:PermissionEngine.check()` | Risk-level check | Through ExecutionFirewall |

## 8. Sandbox Infrastructure

| Component | Location | Status | Purpose |
|-----------|----------|--------|---------|
| PluginSandbox | `features/sandbox/plugin_sandbox.py` | **ORPHANED** | Plugin code execution isolation (import whitelist, restricted builtins, path restriction) |
| ResourceWatchdog | `features/sandbox/resource_watchdog.py` | **ORPHANED** | SIGALRM-based CPU timeout (Unix only, 5s default) |

The sandbox infrastructure isolates plugin scripts (user-written Python modules), not tool calls. This is a separate concern from tool execution safety.

## 9. Consolidation Recommendation

The ADR-014 consolidation plan (Phase 1-3) remains valid. Update from PROPOSED to DRAFT based on this surface analysis. The key additions from E3.0.2 findings are:

1. **4 systems, not 2** — consolidation plan must address all four
2. **11 missing executors** — not just a schema unification problem but a missing-implementation problem
3. **browser_tools + desktop_tools don't exist** — cannot simply "migrate" from stubs; must implement
4. **muscal_loop.py EXECUTORS (6) are the only complete browser implementation** — should be the migration source
5. **file.write vs filesystem.write overlap** — naming conflict must be resolved
6. **permission_engine.py** — adds no unique execution capability; can be deprecated

## 10. E3.1 Consequence

**REQUIRES CONSOLIDATION DURING E3.1 PHASE 3.** The four execution systems must converge into a single Unified Tool Runtime (UTR). The existing `muscal_loop.py` executors (6 tools) form the most complete implementation set and should serve as the migration foundation.
