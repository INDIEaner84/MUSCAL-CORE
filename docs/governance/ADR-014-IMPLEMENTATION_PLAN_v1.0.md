# ADR-014 Implementation Plan v1.0
## Unified Tool Runtime — MUSCAL CORE

**Date:** 2026-07-15
**Status:** PLANNED
**Baseline:** MUSCAL_POST_OPENCODE_UPDATE_BASELINE_v1.0.md
**Constraint:** No new third tool stack. Only consolidate existing two runtimes.

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

Filesystem write has two names in the two systems:
- System A: `filesystem.write` (namespaced)
- System B: `file.write` (flat)

**Decision:** Keep `filesystem.write` as canonical name. `file.write` becomes alias during migration.

---

## 2. Dependency Graph

```
muscal_loop.py (standalone loop)
  ├── EXECUTORS (6 tools)
  │   ├── console.print
  │   ├── browser.open   → BrowserAgent (Playwright)
  │   ├── browser.click  → BrowserAgent
  │   ├── browser.type   → BrowserAgent
  │   ├── opencode.run   → subprocess (allowlisted)
  │   └── file.write     → os (path-allowlisted)
  ├── TOOL_SCHEMAS (6 tools, inline)
  ├── ALLOWED_TOOLS_SET
  ├── ALLOWED_OPENCODE_COMMANDS
  ├── ALLOWED_FILE_PATHS
  ├── validate_tasks()   ← shell metachar scan
  └── validate_safe_path()

kernel.py (pipeline orchestrator)
  ├── mel.py (tool dispatch)
  │   ├── tools.py:TOOL_REGISTRY (3 executors)
  │   │   ├── filesystem.write → write()
  │   │   ├── math.add → add()
  │   │   └── console.print → print_console()
  │   └── system_runtime.py:SystemAgentRuntime
  │       ├── browser_tools.BrowserRuntime (MISSING)
  │       └── desktop_tools.DesktopRuntime (MISSING)
  ├── bridge.py (MCXF → ExecutionPlan)
  │   ├── TOOL_REGISTRY (for validate_plan)
  │   └── TOOL_SCHEMAS (for validate_plan)
  └── runtime/kernel/ (separate infra layer)
      ├── gate.py — task lifecycle (unrelated to tool exec)
      ├── fs_api.py — file ops for API (unrelated to mel)
      └── sanitizer.py — injection detection (reusable)
```

### Current Data Flow (mel.py as routing hub)

```
User Input → kernel.run()
  → mkc.compile() → MCXF dict
  → dict_to_mcxf_document() → MCXFDocument (KnowledgeTriple list)
  → bridge.map_tasks() → ExecutionPlan (steps list with tool/args)
  → mel.execute(plan)
       ├── step.tool startswith "browser." or "desktop." → SystemAgentRuntime
       │   → SystemAgentRuntime.execute()
       │       ├── browser.* → browser_tools.BrowserRuntime (MISSING)
       │       └── desktop.* → desktop_tools.DesktopRuntime (MISSING)
       └── other → TOOL_REGISTRY[tool](**args)
           ├── filesystem.write → write()
           ├── math.add → add()
           └── console.print → print_console()
```

### Current Data Flow (muscal_loop.py standalone)

```
User Input → MuscalLoop.run()
  → llm_compile() → JSON string
  → parse_mcxf() → tasks list
  → validate_tasks() → (ok, errors)
  → execute_tool(task)
       ├── EXECUTORS[tool](args)
       │   ├── console.print → _exec_console_print
       │   ├── browser.* → BrowserAgent
       │   ├── opencode.run → subprocess
       │   └── file.write → os.write
       └── unknown → {"status": "unknown_tool"}
```

---

## 3. Registry Mapping

### TOOL_REGISTRY (tools.py) — 3 executors

```
filesystem.write → write()
math.add         → add()
console.print    → print_console()
```

### TOOL_SCHEMAS (tools.py) — 15 schemas

Same 3 as above + 5 browser + 5 desktop + 2 unregistered. All have input/output/constraints defined.

### EXECUTORS (muscal_loop.py) — 6 executors

```
console.print    → _exec_console_print   [OVERLAP with tools.py]
browser.open     → _exec_browser_open    [executor exists, no schema in tools.py]
browser.click    → _exec_browser_click   [executor exists, no schema in tools.py]
browser.type     → _exec_browser_type    [executor exists, no schema in tools.py]
opencode.run     → _exec_opencode_run    [no overlap, unique]
file.write       → _exec_file_write      [OVERLAP with tools.py filesystem.write]
```

### muscal_loop.py TOOL_SCHEMAS — 6 schemas (simplified)

```
console.print    {args: {message: str}}
browser.open     {args: {url: str}}
browser.click    {args: {selector: str}}
browser.type     {args: {selector: str, text: str}}
opencode.run     {args: {command: str}}
file.write       {args: {path: str, content: str}}
```

### Target: Single TOOL_REGISTRY in UTR

| Tool | Executor Source | Schema Source | Safety Class |
|------|----------------|---------------|--------------|
| `filesystem.write` | tools.py | tools.py | RESTRICTED |
| `math.add` | tools.py | tools.py | SAFE |
| `console.print` | tools.py | tools.py | SAFE |
| `opencode.run` | muscal_loop.py | tools.py (new) | SANDBOXED |
| `browser.open` | muscal_loop BrowserAgent | tools.py | RESTRICTED |
| `browser.click` | muscal_loop BrowserAgent | tools.py | RESTRICTED |
| `browser.type` | muscal_loop BrowserAgent | tools.py | RESTRICTED |
| `browser.extract_text` | NEW (via BrowserAgent) | tools.py | RESTRICTED |
| `browser.screenshot` | NEW (via BrowserAgent) | tools.py | RESTRICTED |
| `browser.scroll` | NEW (via BrowserAgent) | tools.py | RESTRICTED |
| `desktop.*` (5) | NEW (via pyautogui) | tools.py | SANDBOXED |

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
| **Max string length** | — | — | — (handled in runtime/sanitizer.py) |
| **Injection detection** | — | — | — (handled in runtime/sanitizer.py) |

### 4.2 Target: Single SafetyGate

```
UTR SafetyGate
├── PathValidator    (consolidate tools.py + muscal_loop.py allowlists)
├── SizeValidator    (keep MAX_WRITE_SIZE from tools.py)
├── ToolAllowlist    (from muscal_loop.py ALLOWED_TOOLS)
├── OpenCodeAllowlist (from muscal_loop.py ALLOWED_OPENCODE_COMMANDS)
├── ShellMetacharScanner (from muscal_loop.py validate_tasks)
├── KeywordBlocker   (from system_runtime.py BLOCKED_KEYWORDS)
└── EventEmitter     (optional, from system_runtime.py → schema events)
```

**Key decision:** The `runtime/kernel/sanitizer.py` provides injection detection for the API layer. The UTR SafetyGate provides tool execution safety. These are different concerns and should remain separate.

---

## 5. Executor Mapping

### 5.1 Duplicate executors (identical function, different implementation)

| Tool | System A | System B | Differs? | Resolution |
|------|----------|----------|----------|------------|
| `console.print` | `print_console(message)` → `{"printed": message}` | `_exec_console_print(args)` → `{"printed": args["message"]}` | Same behavior, different API (kwargs vs single arg) | Keep A (tool.py), drop B |

### 5.2 Overlapping executors (same function, different names)

| Name A | Name B | Behavior Diff | Resolution |
|--------|--------|---------------|------------|
| `filesystem.write` | `file.write` | A: path allowlist (storage/, /tmp/) + size limit. B: path allowlist (output/, storage/, /tmp/) no size limit. A returns `{"status": "written"}`, B returns `{"status": "written", "path": abs}` | Consolidate into `filesystem.write`. Drop `file.write` alias. Keep stricter union of allowlists. |

### 5.3 Unique executors (no overlap)

| Tool | Source | Why unique |
|------|--------|------------|
| `math.add` | System A only | Pure function |
| `opencode.run` | System B only | Subprocess, unique to autonomous loop |
| `browser.open` | System B only (BrowserAgent) | Playwright-based |
| `browser.click` | System B only (BrowserAgent) | Playwright-based |
| `browser.type` | System B only (BrowserAgent) | Playwright-based |

### 5.4 Missing executors (schemas only, no implementation)

| Tool | Schema | Missing Since | Effort |
|------|--------|---------------|--------|
| `browser.extract_text` | tools.py:55 | Baseline | Low (BrowserAgent has page access) |
| `browser.screenshot` | tools.py:75 | Baseline | Low (BrowserAgent.screenshot exists) |
| `browser.scroll` | tools.py:80 | Baseline | Low (page.evaluate JS) |
| `desktop.screenshot` | tools.py:85 | Baseline | Medium (pyautogui) |
| `desktop.type` | tools.py:90 | Baseline | Medium (pyautogui) |
| `desktop.click` | tools.py:95 | Baseline | Medium (pyautogui) |
| `desktop.open_app` | tools.py:100 | Baseline | High (subprocess, needs sandboxing) |
| `desktop.move` | tools.py:105 | Baseline | Medium (pyautogui) |
| `desktop.keypress` | tools.py:110 | Baseline | Medium (pyautogui) |

---

## 6. Compatibility Matrix

### 6.1 API Signature Compatibility

| Consumer | Uses | Breaks if changed? |
|----------|------|-------------------|
| `mel.py:_execute_step` | `TOOL_REGISTRY[tool](**args)` | Yes — dict return format is caller-dependent |
| `mel.py` plan iteration | `hasattr(plan, "layers")` / `hasattr(plan, "steps")` / list | No — only cares about iterable |
| `bridge.py:validate_plan` | `TOOL_REGISTRY` (exists check) + `TOOL_SCHEMAS` (schema validation) | Yes — both must remain importable |
| `muscal_loop.py:execute_tool` | `EXECUTORS[tool](args)` | No — muscal_loop internals can be refactored |
| `kernel.py:run` | `mel.execute(plan)` | No — only calls mel.execute, no direct tool access |
| `tests/execution/test_mel.py` | `mel.execute(plan)` with various plans | No — tests use public API |
| `tests/security/test_tool_return_contract.py` | `tools.write()`, `tools.add()`, `tools.print_console()` | Yes — direct imports of tool functions |
| `test_determinism.py` | `muscal_loop._exec_opencode_run` | No — imports internal function, test expects it exists |

### 6.2 Backward Compatibility Guarantees

```
mel.execute(plan)     → STABLE (public API, used by kernel.py)
tools.TOOL_REGISTRY   → STABLE (imported by mel.py, bridge.py)
tools.TOOL_SCHEMAS    → STABLE (imported by bridge.py)
tools.write()         → STABLE (tested by test_tool_return_contract)
tools.add()           → STABLE (tested by test_tool_return_contract)
tools.print_console() → STABLE (tested by test_tool_return_contract)
system_runtime.SystemAgentRuntime → STABLE (imported by mel.py)

muscal_loop internals  → CAN REFACTOR (no external consumers except one test)
```

---

## 7. Risk Analysis

| Risk | Probability | Impact | Mitigation |
|------|------------|--------|------------|
| New third tool stack created | LOW | CRITICAL | Constraint in mission: only consolidate, no new stack |
| `bridge.py` validation breaks | MEDIUM | HIGH | Keep TOOL_SCHEMAS importable; add adapter |
| `mel.py` routing breaks | MEDIUM | HIGH | Keep mel.py unchanged; UTR is additive first |
| Existing tests fail | LOW | HIGH | Phase 0: capture all test signatures before migration |
| `muscal_loop.py` autonomous loop diverges | LOW | MEDIUM | muscal_loop keeps using EXECUTORS until final phase |
| Desktop tools still missing after consolidation | HIGH | MEDIUM | ADR-014 does not require desktop implementation |
| SART (`system_runtime.py`) becomes dead code | LOW | LOW | Can be deprecated, not removed |
| `file.write` vs `filesystem.write` naming confusion | MEDIUM | LOW | Alias mechanism during migration |

---

## 8. Implementation Order (TOOL-001 through TOOL-007)

### TOOL-000 (Phase 0): Baseline Capture — 0 core changes
- Run full test suite: `python -m pytest tests/ -q`
- Record all test names, counts, and outputs
- Snapshot current behavior as reference

### TOOL-001 (Phase 1): UTR Class in runtime/ — 0 core changes
- Create `runtime/tool_runtime.py` with `UnifiedToolRuntime` class
- `register(name, executor, schema)`, `execute(name, args)`, `validate(name, args)`, `available()`
- Register all 3 tools from TOOL_REGISTRY (copy, don't move)
- **NO changes to tools.py, mel.py, bridge.py, muscal_loop.py yet**
- **Changes:** 1 new file only
- **Tests:** Test that UTR mirrors existing TOOL_REGISTRY behavior

### TOOL-002 (Phase 2): UTR Execution Path in mel.py — 1 core change
- Modify `mel.py:_execute_step` to prefer UTR over TOOL_REGISTRY + SART split
- `mel.py` imports UTR, calls `utr.execute(step)` for all tools
- UTR internally routes to existing executors: tools.py functions, SART, or BrowserAgent adapters
- UTR singleton or module-level instance
- **Changes:** `mel.py` (core, needs override) + `runtime/tool_runtime.py`
- **Tests:** Existing `test_mel.py` must pass identically. New tests for UTR routing.

### TOOL-003 (Phase 3): Browser Executors in UTR — 0 core changes
- Add browser executors to UTR by wrapping `muscal_loop.BrowserAgent`
- Create shared BrowserAgent singleton or import from muscal_loop
- Register `browser.open/click/type/extract_text/screenshot/scroll` in UTR
- **Changes:** `runtime/tool_runtime.py` only (not core)
- **Tests:** Verify browser executors return same format as current BrowserAgent

### TOOL-004 (Phase 4): SafetyGate — 0 core changes
- Add `SafetyGate` class to `runtime/tool_runtime.py`
- Consolidate: path allowlists, size limits, shell metachar scan, keyword blocker
- Wire into UTR's `validate()` method
- **Changes:** `runtime/tool_runtime.py` only (not core)
- **Tests:** SafetyGate unit tests, existing muscal_loop validate_tasks tests retain coverage

### TOOL-005 (Phase 5): muscal_loop Migration — 0 core changes (non-core file)
- muscal_loop imports and uses UTR for execution
- Replace `_exec_*` functions with UTR calls
- muscal_loop keeps its own TOOL_SCHEMAS as cache (optional)
- **Changes:** `muscal_loop.py` only
- **Tests:** `test_determinism.py:test_muscal_loop_allowlist` must still pass

### TOOL-006 (Phase 6): Schema Unification — 0 core changes
- Create `INSTRUMENTS.md` as single source of truth for tool schemas
- Reference from tools.py TOOL_SCHEMAS (or generate tools.py from it)
- Ensure bridge.py and muscal_loop.py reference the same schemas
- **Changes:** New doc file only
- **Tests:** Verify bridge validation produces same results

### TOOL-007 (Phase 7): Cleanup & Deprecation — 1 core change (SART deprecation)
- Mark `system_runtime.py` as DEPRECATED (add docstring warning)
- Add note that UTR replaces SART for new development
- **NOT removing** SART — backward compat
- **Changes:** `system_runtime.py` docstring only
- **Tests:** No behavioral change expected

---

## 9. Rollback Plan

### Per-Phase Rollback

| Phase | Rollback Action | Risk if not rolled back |
|-------|----------------|------------------------|
| TOOL-001 | Delete `runtime/tool_runtime.py` | Dead code, no runtime impact |
| TOOL-002 | `git checkout mel.py` (restore TOOL_REGISTRY + SART routing) | Broken tool routing |
| TOOL-003 | Delete new executors from UTR | Browser tools fail (same as today) |
| TOOL-004 | Remove SafetyGate, restore old validation | Security regression |
| TOOL-005 | `git checkout muscal_loop.py` (restore standalone executors) | Loop uses old code path |
| TOOL-006 | Revert schema doc | No runtime impact |
| TOOL-007 | `git checkout system_runtime.py` | Stale deprecation warning |

### Full Rollback Trigger Conditions
1. Any test in `tests/` fails compared to TOOL-000 baseline
2. `mel.execute()` returns different results for same input
3. `kernel.run()` produces different ExecutionPlan structure
4. `bridge.validate_plan()` reports different validation results

---

## 10. Definition of Done

### Architecture Requirements
- [ ] Exactly one tool registry (UTR) — no third stack
- [ ] Both existing dispatch paths (mel.py and muscal_loop) route through UTR
- [ ] All 3+6+6 = 15 tool schemas from tools.py are registered in UTR
- [ ] All 3+6 = 9 executors (3 tools.py + 6 muscal_loop) are registered in UTR
- [ ] SafetyGate consolidates all 3 existing safety systems

### Backward Compatibility
- [ ] `mel.execute(plan)` returns identical results for same plan
- [ ] `tools.TOOL_REGISTRY` still importable (re-export from UTR or shim)
- [ ] `tools.TOOL_SCHEMAS` still importable
- [ ] `tools.write()`, `tools.add()`, `tools.print_console()` still callable directly
- [ ] `system_runtime.SystemAgentRuntime` still importable
- [ ] `bridge.validate_plan()` produces same results

### Test Requirements
- [ ] All 337+ existing tests pass without modification
- [ ] UTR-specific tests added:
  - UTR register/execute/validate/available basic operations
  - UTR routes console.print correctly
  - UTR routes filesystem.write correctly
  - UTR routes math.add correctly  
  - UTR routes browser.* correctly (stub mode)
  - UTR returns appropriate error for unknown tool
  - SafetyGate blocks path violations
  - SafetyGate blocks shell metacharacters
  - SafetyGate blocks blocked keywords
- [ ] Integration test: mel.py → UTR → correct executor for each tool type

### Core Protection
- [ ] `kernel.py` — NOT CHANGED
- [ ] `event_bus.py` — NOT CHANGED
- [ ] `config.py` — NOT CHANGED
- [ ] `muscal_os.py` — NOT CHANGED
- [ ] `plugin_loader.py` — NOT CHANGED
- [ ] `plugin_registry.py` — NOT CHANGED
- [ ] `mel.py` — CHANGED (Phase 2, override required)
- [ ] `system_runtime.py` — CHANGED (Phase 7, docstring only, override required)

---

## 11. Beantwortung der Validierungsfragen

### ✓ Entsteht irgendwo ein dritter Tool-Stack?
**NEIN.** Die UTR (UnifiedToolRuntime) ist kein dritter Stack, sondern eine Fassade, die beide bestehenden Registries kapselt. Alle Executoren kommen aus System A (tools.py) oder System B (muscal_loop.py). Die UTR führt keine neuen Executoren ein — sie registriert nur die existierenden. Die 8 bisher nicht implementierten Browser/Desktop-Executoren werden als NEW markiert, aber erst in TOOL-003 implementiert (und auch dann nur als Adapter um existierende Komponenten).

### ✓ Werden bestehende Tests ungültig?
**NEIN.** Die Implementierung ist rückwärtskompatibel auf allen Ebenen:
- `mel.execute()` bleibt stable (public API)
- `tools.TOOL_REGISTRY` bleibt importierbar
- `tools.TOOL_SCHEMAS` bleibt importierbar
- Alle 337 Tests müssen unverändert grün bleiben
- Nur additive Tests kommen hinzu

### ✓ Wird Core Lock Level 3 berührt?
**NEIN.** Es werden keine Core-Dateien in Lock Level 3 (`kernel.py`, `event_bus.py`, `config.py`, `muscal_os.py`, `plugin_loader.py`, `plugin_registry.py`) verändert. Die Änderungen betreffen:
- `runtime/tool_runtime.py` (NEU, nicht in CORE_FILES/CORE_DIRS)
- `mel.py` (core, aber Lock Level 1 — Feature Layer)
- `system_runtime.py` (core, aber nur Docstring-Änderung)
- `muscal_loop.py` (nicht in CORE_FILES/CORE_DIRS)

### ✓ Ist ADR-014 vollständig umsetzbar?
**JA.** Der Plan deckt alle 7 Phasen (TOOL-000 bis TOOL-007) ab. Jede Phase ist:
- Isoliert rückwärtskompatibel
- Auf maximal 1-2 Dateien begrenzt
- Mit eigenem Rollback-Plan versehen
- Vorab durch bestehende Tests validierbar

Einzige Abhängigkeit: TOOL-002 (mel.py change) benötigt OVERRIDE-Dokumentation.

### ✓ Welche Dateien werden später tatsächlich geändert?

| Phase | Datei | Änderungstyp | Core? | Lock Level |
|-------|------|-------------|-------|------------|
| TOOL-001 | `runtime/tool_runtime.py` | NEU | Nein | L0 |
| TOOL-002 | `mel.py` | MODIFIZIERT | **Ja** | L1 (Feature) |
| TOOL-002 | `runtime/tool_runtime.py` | MODIFIZIERT | Nein | L0 |
| TOOL-003 | `runtime/tool_runtime.py` | MODIFIZIERT | Nein | L0 |
| TOOL-004 | `runtime/tool_runtime.py` | MODIFIZIERT | Nein | L0 |
| TOOL-005 | `muscal_loop.py` | MODIFIZIERT | Nein | L0 |
| TOOL-006 | `INSTRUMENTS.md` | NEU | Nein | L0 |
| TOOL-007 | `system_runtime.py` | MODIFIZIERT (docstring) | **Ja** | L1 |

**Total:** 1 neue Datei (`runtime/tool_runtime.py`), 1 neue Dokumentation (`INSTRUMENTS.md`), 2 Core-Modifikationen (`mel.py`, `system_runtime.py`), 1 Non-Core-Modifikation (`muscal_loop.py`).

### Bestehende Lösungen, die ADR-014 teilweise erfüllen

| Vorhanden | Was | ADR-014 Anforderung | Status |
|-----------|-----|-------------------|--------|
| `tools.py:TOOL_SCHEMAS` | Alle 15 Schemas mit Typen + Constraints | Schema-Unification | Wiederverwenden |
| `muscal_loop:BrowserAgent` | Playwright-Integration | Browser-Executoren | Wiederverwenden |
| `tools.py:TOOL_REGISTRY` | 3 Executoren | Registry-Konsolidierung | Wiederverwenden |
| `runtime/kernel/sanitizer.py` | Injection-Detection | Safety | Teilweise — für API-Layer, nicht für Tool-Execution |

**Fazit:** Der Migrationsaufwand ist geringer als in ADR-014 ursprünglich angenommen, weil:
1. `tools.py:TOOL_SCHEMAS` bereits 15 vollständige Schemas enthält → kein neues Schema-Format nötig
2. `muscal_loop:EXECUTORS` sind direkt als UTR-Executoren verwendbar → keine Neuimplementierung
3. `BrowserAgent` ist production-ready (Playwright) → keine Neuentwicklung für Browser-Tools
4. SART existiert + importiert sauber → kann als DEPRECATED markiert, nicht ersetzt werden
