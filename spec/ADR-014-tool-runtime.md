# ADR-014: Unified Tool Runtime

**Status:** PROPOSED
**Date:** 2026-07-15

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
