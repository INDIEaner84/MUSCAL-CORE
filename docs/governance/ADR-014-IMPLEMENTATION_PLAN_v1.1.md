# ADR-014 Implementation Plan v1.1
## Unified Tool Runtime — MUSCAL CORE

**Date:** 2026-07-15  
**Status:** REVISED (v1.0 → v1.1)  
**Baseline:** MUSCAL_POST_OPENCODE_UPDATE_BASELINE_v1.0.md  
**Constraint:** No new third tool stack. Only consolidate existing two runtimes.  
**Review Findings:** 5 issues resolved (sequencing, lifecycle, return format, event emission, alias resolution)

---

## 1. Migration Matrix: Alt → Neu

| Component | Alt (System A: tools.py) | Alt (System B: muscal_loop.py) | Neu (UTR) | Strategy |
|-----------|--------------------------|-------------------------------|-----------|----------|
| **console.print** | `TOOL_REGISTRY["console.print"] = print_console` | `EXECUTORS["console.print"] = _exec_console_print` | Single impl from System A | Keep A, drop B |
| **filesystem.write** | `TOOL_REGISTRY["filesystem.write"] = write` (path-allowlist) | `EXECUTORS["file.write"] = _exec_file_write` (path-allowlist) | Single impl from System A | Keep A, drop B |
| **math.add** | `TOOL_REGISTRY["math.add"] = add` (pure) | — | Keep A only | Trivial |
| **opencode.run** | — | `EXECUTORS["opencode.run"] = _exec_opencode_run` | Keep B only | Adapt to mel.py path |
| **browser.open** | Schema only (no executor) | `EXECUTORS["browser.open"] via BrowserAgent` | Keep B's BrowserAgent | Wrap in adapter |
| **browser.click** | Schema only (no executor) | `EXECUTORS["browser.click"] via BrowserAgent` | Keep B's BrowserAgent | Wrap in adapter |
| **browser.type** | Schema only (no executor) | `EXECUTORS["browser.type"] via BrowserAgent` | Keep B's BrowserAgent | Wrap in adapter |
| **browser.extract_text** | Schema only (no executor) | — | NEW executor needed | Implement via BrowserAgent |
| **browser.screenshot** | Schema only (no executor) | BrowserAgent has screenshot() | NEW adapter | Connect schema → BrowserAgent |
| **browser.scroll** | Schema only (no executor) | — | NEW executor needed | Implement via BrowserAgent |
| **desktop.screenshot** | Schema only (no executor) | — | NEW executor needed | Implement via pyautogui |
| **desktop.type** | Schema only (no executor) | — | NEW executor needed | Implement via pyautogui |
| **desktop.click** | Schema only (no executor) | — | NEW executor needed | Implement via pyautogui |
| **desktop.open_app** | Schema only (no executor) | — | NEW executor needed | Implement via subprocess (sandboxed) |
| **desktop.move** | Schema only (no executor) | — | NEW executor needed | Implement via pyautogui |
| **desktop.keypress** | Schema only (no executor) | — | NEW executor needed | Implement via pyautogui |

### Naming Normalization

| Name A | Name B | Canonical | Alias | Direction |
|--------|--------|-----------|-------|-----------|
| `filesystem.write` | `file.write` | `filesystem.write` | `file.write` → `filesystem.write` | B→A via alias |
| `console.print` | `console.print` | `console.print` | none | identical |

---

## 2. Dependency Graph

```
muscal_loop.py (standalone autonomous loop)
  ├── EXECUTORS (6 tools)          ── PHASE 5 ──→  UTR
  │   ├── console.print                              (registered in UTR via TOOL-001)
  │   ├── browser.open   → BrowserAgent             (registered in UTR via TOOL-002)
  │   ├── browser.click  → BrowserAgent             (registered in UTR via TOOL-002)
  │   ├── browser.type   → BrowserAgent             (registered in UTR via TOOL-002)
  │   ├── opencode.run   → subprocess (allowlisted) (registered in UTR via TOOL-001)
  │   └── file.write     → os (path-allowlisted)    (alias: filesystem.write via TOOL-005)
  ├── TOOL_SCHEMAS (6 tools, inline)
  ├── ALLOWED_TOOLS_SET
  ├── ALLOWED_OPENCODE_COMMANDS
  ├── ALLOWED_FILE_PATHS
  ├── validate_tasks()   ← shell metachar scan
  └── validate_safe_path()

kernel.py (pipeline orchestrator)
  ├── mel.py (tool dispatch)        ── PHASE 3 ──→  UTR
  │   ├── tools.py:TOOL_REGISTRY (3 executors)      UTR wraps, shim re-exports
  │   │   ├── filesystem.write → write()
  │   │   ├── math.add         → add()
  │   │   └── console.print    → print_console()
  │   └── system_runtime.py:SystemAgentRuntime       ── PHASE 7 → DEPRECATED
  │       ├── browser_tools.BrowserRuntime (MISSING)
  │       └── desktop_tools.DesktopRuntime (MISSING)
  ├── bridge.py (MCXF → ExecutionPlan)
  │   ├── TOOL_REGISTRY (for validate_plan)          ── kept as shim
  │   └── TOOL_SCHEMAS (for validate_plan)           ── kept as shim
  └── runtime/kernel/ (separate infra layer)
      ├── gate.py — task lifecycle (UNRELATED)
      ├── fs_api.py — file ops for API (UNRELATED)
      └── sanitizer.py — injection detection (KEEPS SEPARATE)

NEW: runtime/tool_runtime.py (UTR)
  ├── UnifiedToolRuntime class
  │   ├── register(name, executor, schema, aliases=[])
  │   ├── execute(name, args) → ToolResult
  │   ├── validate(name, args) → ValidationResult
  │   └── available() → list[str]
  ├── SafetyGate class
  │   ├── check(tool, args) → SafetyResult
  │   └── consolidated from 3 existing systems
  ├── BrowserAgentAdapter
  │   └── wraps muscal_loop.BrowserAgent (lazy init)
  └── ToolResult dataclass
```

---

## 3. Registry Mapping

### TOOL_REGISTRY (tools.py) — 3 executors

```
filesystem.write → write()          [RESTRICTED — path allowlist + size limit]
math.add         → add()            [SAFE — pure function]
console.print    → print_console()  [SAFE — stdout]
```

### EXECUTORS (muscal_loop.py) — 6 executors

```
console.print    → _exec_console_print    [OVERLAP with tools.py → resolved: keep tools.py version]
browser.open     → _exec_browser_open     [UNIQUE — Playwright]
browser.click    → _exec_browser_click    [UNIQUE — Playwright]
browser.type     → _exec_browser_type     [UNIQUE — Playwright]
opencode.run     → _exec_opencode_run     [UNIQUE — subprocess allowlist]
file.write       → _exec_file_write       [OVERLAP with filesystem.write → resolved: alias]
```

### Target: UTR Single Registry

| Tool | Executor Source | Schema Source | Safety Class | Phase |
|------|----------------|---------------|--------------|-------|
| `filesystem.write` | tools.py `write()` | tools.py | RESTRICTED | TOOL-001 |
| `math.add` | tools.py `add()` | tools.py | SAFE | TOOL-001 |
| `console.print` | tools.py `print_console()` | tools.py | SAFE | TOOL-001 |
| `opencode.run` | muscal_loop `_exec_opencode_run` | tools.py (new schema) | SANDBOXED | TOOL-001 |
| `browser.open` | BrowserAgent.open | tools.py | RESTRICTED | TOOL-002 |
| `browser.click` | BrowserAgent.click | tools.py | RESTRICTED | TOOL-002 |
| `browser.type` | BrowserAgent.type_text | tools.py | RESTRICTED | TOOL-002 |
| `browser.extract_text` | NEW (BrowserAgent.page) | tools.py | RESTRICTED | TOOL-002 |
| `browser.screenshot` | BrowserAgent.screenshot | tools.py | RESTRICTED | TOOL-002 |
| `browser.scroll` | NEW (BrowserAgent.page) | tools.py | RESTRICTED | TOOL-002 |
| `browser.*` (alias) | `file.write` → `filesystem.write` | tools.py | via target | TOOL-005 |

---

## 4. Security Mapping

### 4.1 Three separate safety systems today

| Concern | tools.py | muscal_loop.py | system_runtime.py |
|---------|----------|----------------|-------------------|
| **Path allowlist** | `ALLOWED_WRITE_PATHS: [./storage/, /tmp/]` | `ALLOWED_FILE_PATHS: [./output/, ./storage/, /tmp/]` | — |
| **Write size limit** | `MAX_WRITE_SIZE: 1MB` | — | — |
| **Tool allowlist** | — | `ALLOWED_TOOLS_SET` (6 tools) | `BLOCKED_TOOLS` (5 tools) |
| **Subprocess allowlist** | — | `ALLOWED_OPENCODE_COMMANDS` (8 cmds) | — |
| **Shell metachar scan** | — | `re.search(r'[;&|`$(){}\n\r]', v)` | — |
| **Keyword block** | — | — | `BLOCKED_KEYWORDS` (6 patterns) |
| **Event emission** | — | — | Graph: start/complete/fail |

### 4.2 Target: Single SafetyGate in UTR

```
UTR.SafetyGate
├── PathValidator         → UNION of tools.py + muscal_loop.py allowlists
│                            [./storage/, /tmp/, ./output/]
├── SizeValidator         → tools.py MAX_WRITE_SIZE (1MB) for filesystem.write
├── ToolAllowlist         → muscal_loop.py ALLOWED_TOOLS_SET pattern (optional)
├── OpenCodeAllowlist     → muscal_loop.py ALLOWED_OPENCODE_COMMANDS (8 cmds)
├── ShellMetacharScanner  → muscal_loop.py validate_tasks regex
├── KeywordBlocker        → system_runtime.py BLOCKED_KEYWORDS patterns
└── EventEmitter          → OPTIONAL callback for system action events
```

### 4.3 Separation of Concerns

```
UTR.SafetyGate         → tool execution safety (path, shell, subprocess, keywords)
runtime/kernel/sanitizer.py → API layer safety (injection detection, payload masking)
```

These remain separate — different concerns, different callers.

---

## 5. Executor Mapping

### 5.1 Duplicate executors (identical function, different implementation)

| Tool | System A | System B | Resolution |
|------|----------|----------|------------|
| `console.print` | `print_console(message)` → `{"printed": message}` | `_exec_console_print(args)` → `{"printed": args["message"]}` | Keep A (tools.py). Both return same shape: `{"printed": str}` |

### 5.2 Overlapping executors (same function, different names)

| Name A | Name B | Behavior Diff | Resolution |
|--------|--------|---------------|------------|
| `filesystem.write` | `file.write` | A: path allowlist (`storage/`, `/tmp/`) + 1MB size limit. Returns `{"status": "written", "path": path}`. B: path allowlist (`output/`, `storage/`, `/tmp/`), no size limit. Returns `{"status": "written", "path": abs}` | Consolidate into `filesystem.write`. B becomes alias (TOOL-005). Allowlists unioned. |

### 5.3 Unique executors (no overlap)

| Tool | Source | Phase |
|------|--------|-------|
| `math.add` | System A only | TOOL-001 |
| `opencode.run` | System B only | TOOL-001 |
| `browser.open` | System B (BrowserAgent) | TOOL-002 |
| `browser.click` | System B (BrowserAgent) | TOOL-002 |
| `browser.type` | System B (BrowserAgent) | TOOL-002 |

---

## 6. Compatibility Matrix

### 6.1 API Contract Stability

| Consumer | API Used | Must Remain Stable | Phase Risk |
|----------|----------|-------------------|------------|
| `mel.py:_execute_step` | `TOOL_REGISTRY[tool](**args)` → dict | Return dict shape | TOOL-003 (UTR wraps) |
| `mel.py` plan iteration | `hasattr(plan, "layers")` / `"steps"` / list | Plan iteration interface | None |
| `bridge.py:validate_plan` | `TOOL_REGISTRY` (key check) + `TOOL_SCHEMAS` | Both must stay importable | TOOL-001 (already kept) |
| `kernel.py:run` | `mel.execute(plan)` → list of dicts | mel.execute signature + return list | TOOL-003 |
| `kernel.py:_is_success` | checks `"error"` key in result dicts | Dict shape with `"error"` key missing means success | TOOL-003 (ToolResult preserves) |
| `kernel.py:_build_exec_result` | checks `"tool"` key, `"status"` = `"failed"` | Dict shape with tool/status keys | TOOL-003 (ToolResult preserves) |
| `kernel.py:SystemModule.on_action_event` | Graph events `SYSTEM_ACTION_STARTED/COMPLETED/FAILED` | Event emission from browser/desktop tools | TOOL-004 (EventEmitter) |
| `tests/execution/test_mel.py` | `mel.execute(plan)` | mel.execute public API | None |
| `tests/security/test_tool_return_contract.py` | `tools.write()`, `tools.add()`, `tools.print_console()` | Direct function calls | TOOL-001 (shim) |
| `tests/test_determinism.py` | `muscal_loop._exec_opencode_run` | Internal function exists | TOOL-005 (kept via UTR) |
| `tests/test_core_pipeline.py` | `from mel import execute as mel_execute` | mel.execute public API | TOOL-003 |

---

## 7. Risk Register

| Risk | Probability | Impact | Mitigation | Phase |
|------|------------|--------|------------|-------|
| **mel.py → UTR routing returns different dict shape, breaks kernel.py error detection** | MEDIUM | HIGH | ToolResult canonical contract preserves all existing keys. Pre-commit test suite catches differences. | TOOL-003 |
| **SART events not emitted → graph observability broken for browser/desktop actions** | HIGH | MEDIUM | EventEmitter callback in UTR, wired to same schema events. SystemModule.on_action_event unaffected. | TOOL-004 |
| **BrowserAgent lifecycle not managed → browser tools fail after first use** | MEDIUM | HIGH | Lazy singleton pattern in UTR BrowserAgentAdapter. muscal_loop._browser remains untouched. | TOOL-002 |
| **file.write alias not resolved → mel.py produces "unknown tool" errors** | HIGH | MEDIUM | Alias map in UTR.register(). Pre-registered: `file.write` → `filesystem.write`. | TOOL-001 |
| **New third tool stack created by accident** | LOW | CRITICAL | Constraint documented in every phase. All executors come from System A or System B. | All |
| **bridge.py validation breaks because TOOL_SCHEMAS format changed** | MEDIUM | HIGH | TOOL_SCHEMAS kept as-is. No schema format change. INSTRUMENTS.md is additive, not replacement. | TOOL-006 |
| **Desktop tools still missing after consolidation** | HIGH | MEDIUM | ADR-014 does not require desktop implementation. `desktop.*` tools get stub executors. | TOOL-002 |
| **muscal_loop.py diverges — loop uses old EXECUTORS while mel.py uses UTR** | LOW | MEDIUM | muscal_loop migrated to UTR in TOOL-005. Until then, both paths work independently. | TOOL-005 |
| **test_tool_return_contract.py imports break if tools.py refactored** | LOW | LOW | tools.py kept as shim/re-export layer. No refactoring of existing function signatures. | TOOL-001 |
| **`test_no_import_in_kernel` checks kernel.py source — UTR doesn't affect it** | LOW | LOW | UTR doesn't touch kernel.py. No risk. | — |

---

## 8. Implementation Order (TOOL-001 through TOOL-007)

### TOOL-000 (Phase 0): Baseline Capture — 0 core changes

**Action:**
```
python -m pytest tests/ -q --tb=line > docs/governance/baseline_test_output_v1.0.txt
```
Record all test names, pass/fail counts, durations. Snapshot as reference for all subsequent phases.

**Output:** `docs/governance/baseline_test_output_v1.0.txt`

---

### TOOL-001 (Phase 1): UTR Class + Core Executors — 0 core changes

**Goal:** Create UTR with the 4 non-browser executors (filesystem.write, math.add, console.print, opencode.run) and alias map.

**Changes:**
- `runtime/tool_runtime.py` — NEW file
- `tools.py` — NOT CHANGED (shim re-exports as-is)

**UTR API:**
```python
@dataclass
class ToolResult:
    tool: str
    status: str          # "success" | "error" | "blocked"
    result: dict         # original executor return payload
    error: str | None    = None

class UnifiedToolRuntime:
    def register(self, name: str, executor: Callable,
                 schema: dict | None = None,
                 aliases: list[str] | None = None) -> None: ...
    def execute(self, name: str, args: dict) -> ToolResult: ...
    def validate(self, name: str, args: dict) -> ValidationResult: ...
    def available(self) -> list[str]: ...
```

**Alias Pre-Registration:**
```python
utr.register("filesystem.write", tools.write, schema=tools.TOOL_SCHEMAS["filesystem.write"],
             aliases=["file.write"])
utr.register("math.add", tools.add, schema=tools.TOOL_SCHEMAS["math.add"])
utr.register("console.print", tools.print_console, schema=tools.TOOL_SCHEMAS["console.print"])
utr.register("opencode.run", _exec_opencode_run_wrapper, {...})
```

The `_exec_opencode_run_wrapper` adapts muscal_loop's `_exec_opencode_run` to receive `(name, args)` instead of `(args)`.

**ToolResult Canonical Contract:**
```python
# UTR wraps every executor return into ToolResult:
#   ToolResult(tool="filesystem.write", status="success",
#              result={"status": "written", "path": "/tmp/..."})
#
# kernel.py:_is_success checks:
#   - "error" in r  → unchanged (r is the dict inside ToolResult.result)
#   - r.get("tool") → ToolResult.tool
#   - r.get("status") == "failed" → ToolResult.status
#
# mel.py returns list[dict] to callers (backward compat):
#   each dict = {**ToolResult.result, "tool": ToolResult.tool}
```

**Tests (additive):**
- UTR basic operations (register, execute, validate, available)
- UTR routes console.print correctly
- UTR routes filesystem.write correctly (incl. alias `file.write`)
- UTR routes math.add correctly
- UTR routes opencode.run correctly
- UTR blocks unknown tools
- Alias resolution works (`file.write` → `filesystem.write`)
- ToolResult preserves existing dict keys

**Backward Compatibility Check:**
```bash
python -m pytest tests/ -q --tb=line
# Must match TOOL-000 baseline exactly (same count, same passes)
```

**Rollback:** Delete `runtime/tool_runtime.py`.

---

### TOOL-002 (Phase 2): Browser Executors in UTR — 0 core changes

**Goal:** Register all browser executors in UTR via BrowserAgentAdapter. Desktop executors get stub executors.

**Changes:**
- `runtime/tool_runtime.py` — MODIFIED (add executors + BrowserAgentAdapter)

**BrowserAgentAdapter Design:**
```python
class BrowserAgentAdapter:
    """Lazy singleton wrapper around muscal_loop.BrowserAgent."""
    
    _instance: "BrowserAgentAdapter | None" = None
    
    def __new__(cls):
        if cls._instance is None:
            from muscal_loop import _browser as loop_browser
            cls._instance = super().__new__(cls)
            cls._instance._browser = loop_browser
            cls._instance._initialized = False
        return cls._instance
    
    def ensure_started(self):
        if not self._initialized:
            self._browser.start()
            self._initialized = True
    
    def open(self, url: str) -> dict:
        self.ensure_started()
        return self._browser.open(url)
    
    def click(self, selector: str) -> dict:
        self.ensure_started()
        return self._browser.click(selector)
    
    def type_text(self, selector: str, text: str) -> dict:
        self.ensure_started()
        return self._browser.type_text(selector, text)
    
    def extract_text(self, selector: str) -> dict:
        self.ensure_started()
        return {"text": self._browser._page.inner_text(selector)}
    
    def screenshot(self, path: str = "screenshot.png") -> dict:
        self.ensure_started()
        return self._browser.screenshot(path)
    
    def scroll(self, direction: str) -> dict:
        self.ensure_started()
        self._browser._page.evaluate(f"window.scrollBy(0, {600 if direction == 'down' else -600})")
        return {"scrolled": direction}
```

**Lifecycle Strategy:**
- The adapter does NOT own start/close. It delegates to `muscal_loop._browser` which is managed by `MuscalLoop.run()`.
- If called from `mel.py` path (outside MuscalLoop), `ensure_started()` calls `start()` on the shared BrowserAgent singleton.
- No double-start risk: `_browser.start()` checks `self._available` and is idempotent.

**Events (preparation only, actual wiring in TOOL-004):**
- UTR execute() for browser tools calls an optional `on_before_exec(name, args)` and `on_after_exec(name, result)` callback
- These are stubs in this phase (no-op)

**Desktop Tools:**
- Register as stubs returning `{"status": "stub", "tool": name, "error": "not implemented"}`
- Same behavior as current SART without playwright/pyautogui

**Executors Registered in this Phase:**

| Tool | Executor | Implementation |
|------|----------|---------------|
| `browser.open` | `BrowserAgentAdapter.open` | Delegates to muscal_loop._browser.open |
| `browser.click` | `BrowserAgentAdapter.click` | Delegates to muscal_loop._browser.click |
| `browser.type` | `BrowserAgentAdapter.type_text` | Delegates to muscal_loop._browser.type_text |
| `browser.extract_text` | `BrowserAgentAdapter.extract_text` | NEW via page.inner_text |
| `browser.screenshot` | `BrowserAgentAdapter.screenshot` | Delegates to muscal_loop._browser.screenshot |
| `browser.scroll` | `BrowserAgentAdapter.scroll` | NEW via page.evaluate |
| `desktop.*` (5) | stub returning `{"status": "stub"}` | Stub (same as current SART fallback) |

**Tests (additive):**
- BrowserAgentAdapter lazy init (doesn't start before first call)
- BrowserAgentAdapter delegates correctly (stub mode)
- Desktop stubs return consistent shape
- All browser executors return ToolResult with correct keys

**Backward Compatibility Check:**
```bash
python -m pytest tests/ -q --tb=line
# Must match TOOL-000 baseline
```

**Rollback:** Revert `runtime/tool_runtime.py` to TOOL-001 state.

---

### TOOL-003 (Phase 3): UTR Execution Path in mel.py — 1 core change (override required)

**Goal:** Wire mel.py to dispatch ALL tools through UTR. SART and TOOL_REGISTRY become fallbacks.

**Changes:**
- `mel.py` — MODIFIED (core, needs `--allow-core-write` + OVERRIDE documentation)
- `runtime/tool_runtime.py` — MODIFIED (add UTR singleton instance)

**mel.py Before:**
```python
def _execute_step(step: dict) -> dict:
    tool_name = step["tool"]
    if tool_name == "UNMAPPED":
        return {"tool": "UNMAPPED", ...}
    if tool_name.startswith("browser.") or tool_name.startswith("desktop."):
        return _get_runtime().execute(step)
    if tool_name not in TOOL_REGISTRY:
        raise Exception(f"Unknown tool: {tool_name}")
    args = step["args"]
    return TOOL_REGISTRY[tool_name](**args)
```

**mel.py After:**
```python
from runtime.tool_runtime import utr, ToolResult

def _execute_step(step: dict) -> dict:
    tool_name = step["tool"]
    if tool_name == "UNMAPPED":
        return {"tool": "UNMAPPED", "original_task": step.get("original_task", ""),
                "reason": step.get("reason", ""), "status": "skipped"}
    
    # UTR dispatch (all tools)
    result: ToolResult = utr.execute(tool_name, step.get("args", {}))
    
    # Backward compat dict shape for callers
    backward = dict(result.result) if result.result else {}
    backward["tool"] = result.tool
    if result.status == "error":
        backward["error"] = result.error
    elif result.status == "blocked":
        backward["status"] = result.status
        backward["error"] = result.error
    return backward
```

**Key design decisions:**
- `mel.execute()` returns `list[dict]` (backward compat). Each dict is the original executor return, enriched with `"tool"` key.
- `kernel.py:_is_success()` and `_build_exec_result()` check dict keys — these are preserved.
- SART (`_get_runtime()`) is no longer called for browser/desktop tools. SART remains importable but becomes dead code.
- `TOOL_REGISTRY` remains importable from tools.py (used by bridge.py). Mel.py no longer imports it directly.

**Tests (existing must pass identically):**
- `test_mel.py` (4 tests) — mel.execute returns same list of dicts
- `test_core_pipeline.py` (17 tests) — `from mel import execute as mel_execute` works
- `test_full_pipeline.py` — kernel.run() calls mel.execute → UTR → same results
- `test_tool_return_contract.py` — tools.write/add/print_console still callable directly

**Tests (additive):**
- UTR dispatch from mel.py reaches correct executor
- mel.py returns same dict shape as before for console.print
- mel.py returns same dict shape as before for filesystem.write
- mel.py returns same dict shape as before for browser.* (stub mode)
- mel.py handles UNMAPPED steps identically

**Rollback:** `git checkout mel.py` reverts to TOOL_REGISTRY + SART routing.

---

### TOOL-004 (Phase 4): SafetyGate + Event Emission — 0 core changes

**Goal:** Add SafetyGate consolidation and EventEmitter for browser/desktop tool observability.

**Changes:**
- `runtime/tool_runtime.py` — MODIFIED (add SafetyGate + EventEmitter)

**SafetyGate:**
```python
class SafetyGate:
    def check(self, tool: str, args: dict) -> SafetyResult:
        # 1. PathValidator — union of tools.py + muscal_loop.py allowlists
        #    ALLOWED_WRITE_PATHS = [./storage/, /tmp/, ./output/]
        # 2. SizeValidator — 1MB for filesystem.write
        # 3. ToolAllowlist — optional, per-caller (muscal_loop has one, mel.py doesn't)
        # 4. OpenCodeAllowlist — 8 commands for opencode.run
        # 5. ShellMetacharScanner — for all string args
        # 6. KeywordBlocker — BLOCKED_KEYWORDS from system_runtime.py
```

**SafetyResult:**
```python
@dataclass
class SafetyResult:
    allowed: bool
    reason: str = ""
```

**Integration into UTR.execute():**
```python
def execute(self, name: str, args: dict) -> ToolResult:
    safety = self._safety.check(name, args)
    if not safety.allowed:
        return ToolResult(tool=name, status="blocked", result={}, error=safety.reason)
    
    self._emit_before(name, args)      # EVENT_SYSTEM_ACTION_STARTED
    try:
        result = self._executors[name](args)
        self._emit_after(name, result) # EVENT_SYSTEM_ACTION_COMPLETED
        return ToolResult(tool=name, status="success", result=result)
    except Exception as e:
        self._emit_error(name, str(e)) # EVENT_SYSTEM_ACTION_FAILED
        return ToolResult(tool=name, status="error", result={}, error=str(e))
```

**EventEmitter (optional wiring):**
```python
class EventEmitter:
    def __init__(self, emit_fn: Callable[[str, dict], None] | None = None):
        self._emit = emit_fn
    
    def on_before(self, tool: str, args: dict):
        if self._emit:
            self._emit(EVENT_SYSTEM_ACTION_STARTED,
                       {"tool": tool, "args": str(args)[:200]})
    
    def on_after(self, tool: str, result: dict):
        if self._emit:
            self._emit(EVENT_SYSTEM_ACTION_COMPLETED,
                       {"tool": tool, "result": str(result)[:200]})
    
    def on_error(self, tool: str, error: str):
        if self._emit:
            self._emit(EVENT_SYSTEM_ACTION_FAILED,
                       {"tool": tool, "error": error})
```

**Wiring in mel.py (TOOL-003 should already have this — included here for completeness):**
```python
# mel.py top level (or kernel.py during init)
from runtime.tool_runtime import utr
utr.set_event_emitter(lambda topic, payload: graph.emit(topic, payload))
```

**Tests (additive):**
- SafetyGate allows valid filesystem.write
- SafetyGate blocks path outside allowlist
- SafetyGate blocks shell metacharacters in args
- SafetyGate blocks blocked keywords
- SafetyGate allows safe opencode.run commands
- SafetyGate blocks unsafe opencode.run commands
- EventEmitter calls emit_fn before/after/error
- EventEmitter preserves SYSTEM_ACTION constant names

**Backward Compatibility Check:**
```bash
python -m pytest tests/ -q --tb=line
```

**Rollback:** Remove SafetyGate, revert EventEmitter wiring. mel.py still routes through UTR (just without validation gate).

---

### TOOL-005 (Phase 5): muscal_loop Migration — 0 core changes (non-core file)

**Goal:** muscal_loop imports and uses UTR for execution. Keeps its own TOOL_SCHEMAS as cache.

**Changes:**
- `muscal_loop.py` — MODIFIED (not core)

**muscal_loop.py After:**
```python
from runtime.tool_runtime import utr

# Replace EXECUTORS with UTR dispatch
def execute_tool(task):
    tool = task["tool"]
    args = task["args"]
    result = utr.execute(tool, args)
    backward = dict(result.result) if result.result else {}
    backward["tool"] = tool
    if result.status == "error":
        backward["status"] = "error"
        backward["error"] = result.error
    return backward
```

**SafetyGate integration:**
- muscal_loop's `validate_tasks()` is kept as a pre-check (shell metachar scan)
- But SafetyGate in UTR now also performs the same checks (belt-and-suspenders during transition)
- `ALLOWED_TOOLS_SET` can be deprecated — UTR.validate handles tool allowlisting

**What remains in muscal_loop:**
- `TOOL_SCHEMAS` — kept as local cache (potential removal in TOOL-006)
- `ALLOWED_TOOLS_SET` — kept for backward compat (potential removal in TOOL-006)
- `ALLOWED_OPENCODE_COMMANDS` — kept (now also enforced by SafetyGate)
- `ALLOWED_FILE_PATHS` — kept (now also enforced by SafetyGate)
- `validate_tasks()` — kept as pre-check
- `validate_safe_path()` — kept (now also enforced by SafetyGate)
- `BrowserAgent` — kept (UTR wraps it via BrowserAgentAdapter)

**Tests (existing must pass):**
- `test_determinism.py:test_muscal_loop_allowlist` — `callable(muscal_loop._exec_opencode_run)` — this internal function still exists because muscal_loop keeps its EXECUTORS. However, they're no longer called internally. The test checks `callable()` and source code inspection, which still passes.

**Tests (additive):**
- muscal_loop routes through UTR and produces same results
- muscal_loop validates + UTR SafetyGate = no double-blocking

**Rollback:** `git checkout muscal_loop.py` restores standalone EXECUTORS.

---

### TOOL-006 (Phase 6): Schema Unification (INSTRUMENTS.md) — 0 core changes

**Goal:** Create INSTRUMENTS.md as single source of truth for tool schemas.

**Changes:**
- `INSTRUMENTS.md` — NEW documentation file (not a code change)
- `tools.py:TOOL_SCHEMAS` — NOT CHANGED (kept as code-level schema source)
- `muscal_loop.py:TOOL_SCHEMAS` — optionally removed (depends on whether any internal usage remains)

**ADR-014 Phase Ordering Deviation — Documented:**

ADR-014 Phase 1 states "Schema Unification first (INSTRUMENTS.md)". This plan moves it to TOOL-006 (second-to-last). Rationale:
1. `tools.py:TOOL_SCHEMAS` already contains 15 complete schemas with types, outputs, and constraints
2. Creating an additional markdown document before implementation provides no runtime benefit
3. The code-level schemas in `tools.py` are the single source of truth during implementation
4. `INSTRUMENTS.md` serves as human-readable documentation and CI validation target, not as a runtime dependency
5. This avoids a circular dependency: INSTRUMENTS.md → UTR → tools.py → INSTRUMENTS.md

The deviation is incremental (additive, not structural) and does not violate ADR-014's intent of "single schema source." After TOOL-006, INSTRUMENTS.md becomes the authoritative reference, and tools.py TOOL_SCHEMAS must match it.

**INSTRUMENTS.md Structure:**
```markdown
# MUSCAL Tool Instruments v1

| Tool | Args | Returns | Safety Class | Constraints |
|------|------|---------|--------------|-------------|
| console.print | message: str | printed: str | SAFE | max_length:4096 |
| filesystem.write | path: str, content: str | status: str, path: str | RESTRICTED | size:1MB, paths:storage/...,/tmp/...,output/... |
| math.add | a: int|float, b: int|float | result: int|float | SAFE | pure |
| opencode.run | command: str | status: str, output: str | SANDBOXED | allowlist:ls,cat,echo,... |
| browser.open | url: str | status: str, title: str | RESTRICTED | timeout:10 |
| browser.click | selector: str | status: str | RESTRICTED | timeout:10 |
| browser.type | selector: str, text: str | status: str | RESTRICTED | max_length:1000 |
| browser.extract_text | selector: str | text: str | RESTRICTED | max_chars:10000 |
| browser.screenshot | path: str | status: str | RESTRICTED | path:screenshots/ |
| browser.scroll | direction: str | status: str | RESTRICTED | direction:up|down |
| desktop.screenshot | path: str | status: str | SANDBOXED | path:screenshots/ |
```

**Tests:**
- Verify bridge validation produces same results with TOOL_SCHEMAS → match INSTRUMENTS.md
- No behavioral change

**Rollback:** Revert INSTRUMENTS.md.

---

### TOOL-007 (Phase 7): Cleanup & Deprecation — 1 core change (docstring)

**Goal:** Mark SART as DEPRECATED. Remove dead code branches.

**Changes:**
- `system_runtime.py` — MODIFIED (docstring only, core, needs override)
- `tools.py` — optionally add deprecation warning for direct function calls (user-facing, not breaking)

**system_runtime.py Before:**
```python
"""
MUSCAL System Agent Runtime v0.1
Routes browser/desktop tool calls to their respective runtimes.
...
"""
```

**system_runtime.py After:**
```python
"""
MUSCAL System Agent Runtime v0.1 — DEPRECATED since 2026-07-15

Replaced by UnifiedToolRuntime (runtime/tool_runtime.py).
Browser/desktop tool calls now route through UTR.
SART remains importable for backward compatibility but is no longer
called by mel.py or any core pipeline component.

Use runtime.tool_runtime.utr for all new development.
"""
```

**NOT removing:**
- SART class — backward compat
- SART import in mel.py — kept dead (not called) but importable
- `tools.TOOL_REGISTRY` — kept as importable shim
- `tools.TOOL_SCHEMAS` — kept as importable schema source

**Tests:**
- SART still importable
- `system_runtime.SystemAgentRuntime` still instantiable
- All existing tests pass

**Rollback:** `git checkout system_runtime.py`.

---

## 9. Rollback Strategy

### Per-Phase Rollback

| Phase | Rollback Action | Impact if Skipped | Reversibility |
|-------|----------------|-------------------|---------------|
| TOOL-000 | Delete baseline file | No runtime impact | — |
| TOOL-001 | Delete `runtime/tool_runtime.py` | Dead code, no runtime impact | Immediate |
| TOOL-002 | Revert `runtime/tool_runtime.py` | Browser tools fail (same as before UTR) | Immediate |
| TOOL-003 | `git checkout mel.py` | mel.py routes via old TOOL_REGISTRY + SART | Immediate |
| TOOL-004 | Remove SafetyGate, revert EventEmitter | Security regression | Immediate |
| TOOL-005 | `git checkout muscal_loop.py` | Loop uses old EXECUTORS | Immediate |
| TOOL-006 | Revert INSTRUMENTS.md | No runtime impact | Immediate |
| TOOL-007 | `git checkout system_runtime.py` | Stale deprecation warning | Immediate |

### Full Rollback Trigger Conditions

1. Any test fails compared to TOOL-000 baseline
2. `kernel.run("print hello")` produces different `KernelResult` (different success, different memory_id, different errors)
3. `mel.execute(plan)` returns different results for same ExecutionPlan
4. `bridge.validate_plan()` reports different validation results for same plan
5. `kernel.py._is_success()` returns different boolean for same mel result list

### Rollback Command Sequence

```bash
# Full rollback from any TOOL-003+ phase
git checkout mel.py system_runtime.py muscal_loop.py
rm runtime/tool_runtime.py
python -m pytest tests/ -q
# Verify matches TOOL-000 baseline
```

---

## 10. Definition of Done

### Architecture Requirements
- [ ] Exactly one unified tool registry (UTR) in `runtime/tool_runtime.py`
- [ ] No third tool stack — all executors originate from tools.py or muscal_loop.py
- [ ] `mel.py` dispatches all tools through UTR (not SART, not TOOL_REGISTRY directly)
- [ ] `muscal_loop.py` dispatches all tools through UTR (not EXECUTORS directly)
- [ ] BrowserAgentAdapter wraps `muscal_loop._browser` (lazy singleton, no duplicate lifecycle)
- [ ] ToolResult canonical contract defined and used by all executors
- [ ] All 15 tool schemas from tools.py are registered in UTR
- [ ] All 9 executors (3 tools.py + 6 muscal_loop) are registered in UTR
- [ ] SafetyGate consolidates all 3 existing safety systems
- [ ] EventEmitter preserves SYSTEM_ACTION_STARTED/COMPLETED/FAILED events
- [ ] Alias map resolves `file.write` → `filesystem.write`

### Backward Compatibility
- [ ] `mel.execute(plan)` returns identical results for same ExecutionPlan
- [ ] `tools.TOOL_REGISTRY` still importable (shim in tools.py)
- [ ] `tools.TOOL_SCHEMAS` still importable
- [ ] `tools.write()`, `tools.add()`, `tools.print_console()` still callable directly
- [ ] `system_runtime.SystemAgentRuntime` still importable and instantiable
- [ ] `bridge.validate_plan()` produces same ValidationResult for same plan
- [ ] `kernel.py._is_success()` returns same boolean for same mel results
- [ ] `kernel.py._build_exec_result()` produces same ExecResult for same mel results

### Core Protection
- [ ] `kernel.py` — NOT CHANGED
- [ ] `event_bus.py` — NOT CHANGED
- [ ] `config.py` — NOT CHANGED
- [ ] `muscal_os.py` — NOT CHANGED
- [ ] `plugin_loader.py` — NOT CHANGED
- [ ] `plugin_registry.py` — NOT CHANGED

### Files Changed

| Phase | File | Type | Core? | Override? |
|-------|------|------|-------|-----------|
| TOOL-001 | `runtime/tool_runtime.py` | NEW | No | No |
| TOOL-002 | `runtime/tool_runtime.py` | MODIFY | No | No |
| TOOL-003 | `mel.py` | MODIFY | **Yes** | **Yes** — `--allow-core-write` |
| TOOL-003 | `runtime/tool_runtime.py` | MODIFY | No | No |
| TOOL-004 | `runtime/tool_runtime.py` | MODIFY | No | No |
| TOOL-005 | `muscal_loop.py` | MODIFY | No | No |
| TOOL-006 | `INSTRUMENTS.md` | NEW | No | No |
| TOOL-007 | `system_runtime.py` | MODIFY (docstring) | **Yes** | **Yes** — `--allow-core-write` |

**Total:** 1 new file (`runtime/tool_runtime.py`), 1 new doc (`INSTRUMENTS.md`), 2 core changes (`mel.py`, `system_runtime.py`), 1 non-core change (`muscal_loop.py`).

### Test Requirements

**Existing tests that must pass (unchanged):**
- `tests/execution/test_mel.py` (4 tests)
- `tests/security/test_tool_return_contract.py` (4 tests)
- `tests/test_determinism.py` (6 tests)
- `tests/test_core_pipeline.py` (17 tests)
- `tests/test_full_pipeline.py` (1 test)
- All reconciliation tests (47 tests)
- All integration pipeline tests (9 tests)
- All other 337+ tests

**New tests required:**

| Test Group | Count | Phase | What |
|-----------|-------|-------|------|
| UTR Basic Operations | 8 | TOOL-001 | register, execute, validate, available, unknown tool, alias resolution |
| UTR Core Executors | 4 | TOOL-001 | console.print, filesystem.write, math.add, opencode.run |
| UTR Browser Executors | 7 | TOOL-002 | browser.open/click/type/extract_text/screenshot/scroll + desktop stubs |
| BrowserAgentAdapter | 3 | TOOL-002 | lazy init, delegation, stub mode |
| UTR → mel.py Routing | 5 | TOOL-003 | dispatch reaches correct executor, dict shape preserved, UNMAPPED |
| SafetyGate Unit | 8 | TOOL-004 | path allowlist, size limit, shell metachar, keyword block, opencode allowlist, safepath, all-clear, tool allowlist |
| EventEmitter | 3 | TOOL-004 | before/after/error callbacks |
| muscal_loop → UTR | 2 | TOOL-005 | same results as old EXECUTORS |
| SafetyGate Integration | 2 | TOOL-004 | belt-and-suspenders with muscal_loop validators |

**Total new tests: ~42** (additive, not modifying existing).

---

## 11. File Change Matrix

| File | Before (v1.0 plan) | After (v1.1 plan) | Why Changed |
|------|-------------------|-------------------|-------------|
| TOOL-002 purpose | Wire mel.py to UTR | Register browser executors in UTR | Fix sequencing gap (review finding #1) |
| TOOL-003 purpose | Add browser executors | Wire mel.py to UTR (now has all 10 executors) | Fix sequencing gap (review finding #1) |
| UTR specification | abstract API only | ToolResult dataclass + backward compat dict | Fix return format (review finding #3) |
| BrowserAgent | "create shared singleton" | BrowserAgentAdapter with lazy init + lifecycle hooks | Fix lifecycle (review finding #2) |
| Event emission | "optional EventEmitter" | EventEmitter class + wiring spec + test plan | Fix event preservation (review finding #4) |
| Alias resolution | "file.write alias" (brief) | Pre-registered alias map + direction + test cases | Fix alias (review finding #5) |
| ADR-014 deviation | not documented | Phase Ordering Deviation documented in TOOL-006 | New section |
| Rollback | per-phase table | + full rollback trigger conditions + command sequence | Expanded |
| Acceptance Criteria | basic checklist | + backward compatibility matrix + core protection checklist + test migration plan | Expanded |

---

## 12. Beantwortung der Validierungsfragen

### ✓ Entsteht irgendwo ein dritter Tool-Stack?
**NEIN.** UTR ist eine Fassade, die ausschließlich existierende Executoren aus System A (tools.py) und System B (muscal_loop.py) registriert. Die BrowserAgentAdapter delegiert an `muscal_loop._browser`. Desktop-Stubs verhalten sich identisch zum aktuellen SART-Fallback. Kein neuer Code-Pfad für Tool-Execution.

### ✓ Werden bestehende Tests ungültig?
**NEIN.** Alle ~337 Tests bleiben unverändert grün:
- `mel.execute()` gibt gleiche `list[dict]` zurück (ToolResult.backward)
- `tools.TOOL_REGISTRY` bleibt importierbar
- `tools.TOOL_SCHEMAS` bleibt importierbar
- `muscal_loop._exec_opencode_run` bleibt `callable()` (TOOL-005)
- `kernel.py._is_success()` sieht gleiche dict-Keys

### ✓ Wird Core Lock Level 3 berührt?
**NEIN.** Keine Änderungen an `kernel.py`, `event_bus.py`, `config.py`, `muscal_os.py`, `plugin_loader.py`, `plugin_registry.py`. Core-Änderungen beschränken sich auf:
- `mel.py` (Lock Level 1 — Feature Layer, override erforderlich)
- `system_runtime.py` (Lock Level 1 — Feature Layer, nur Docstring, override erforderlich)

### ✓ Ist ADR-014 vollständig umsetzbar?
**JA.** 7 Phasen (TOOL-000 bis TOOL-007), alle mit:
- Isolierten Changes (max 1-2 Dateien pro Phase)
- Eigenem Rollback
- Bestehenden Tests als Sicherheitsnetz
- ~42 additiven Tests zur Absicherung

### ✓ Welche Dateien werden tatsächlich geändert?

| Datei | Phase | Änderung | Core |
|-------|-------|----------|------|
| `runtime/tool_runtime.py` | TOOL-001/002/003/004 | NEU + MODIFIZIERT | Nein |
| `mel.py` | TOOL-003 | MODIFIZIERT | Ja |
| `muscal_loop.py` | TOOL-005 | MODIFIZIERT | Nein |
| `INSTRUMENTS.md` | TOOL-006 | NEU | Nein |
| `system_runtime.py` | TOOL-007 | MODIFIZIERT (docstring) | Ja |
