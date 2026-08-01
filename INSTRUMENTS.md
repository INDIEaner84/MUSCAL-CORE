# E3.1 Canonical Tool Schema — INSTRUMENTS.md

## Overview

This document defines the canonical tool schema for all tool execution within the MUSCAL architecture. Every tool execution MUST converge on the Unified Tool Runtime (UTR) through SafetyGate validation.

---

## Canonical Tools

### console.print

| Field | Value |
|-------|-------|
| Canonical Name | `console.print` |
| UTR Status | IMPLEMENTED |
| Risk | LOW |
| SafetyGate | `LOW_RISK_TOOLS` |
| Executor | `features/tool_runtime/tool_runtime.py:_register_console_print` |
| Governance | None |
| Legacy Alias | none |
| Deprecation | none |

**Input Schema:**
```json
{"text": {"type": "string", "required": true}}
```

**Output Schema:**
```json
{"status": "success", "text": "<printed text>"}
```

---

### filesystem.write

| Field | Value |
|-------|-------|
| Canonical Name | `filesystem.write` |
| UTR Status | IMPLEMENTED |
| Risk | MEDIUM |
| SafetyGate | `MEDIUM_RISK_TOOLS` |
| Executor | `features/tool_runtime/tool_runtime.py:_register_file_write` |
| Governance | Path validation |
| Legacy Alias | `file.write` |
| Deprecation | `file.write` is an alias; prefer `filesystem.write` |

**Input Schema:**
```json
{
  "path": {"type": "string", "required": true, "description": "Absolute file path"},
  "content": {"type": "string", "required": true},
  "mode": {"type": "string", "enum": ["write", "append"], "default": "write"}
}
```

**Output Schema:**
```json
{"status": "written", "path": "<resolved path>", "size": 123}
```

---

### math.add

| Field | Value |
|-------|-------|
| Canonical Name | `math.add` |
| UTR Status | IMPLEMENTED |
| Risk | LOW |
| SafetyGate | `LOW_RISK_TOOLS` |
| Executor | `features/tool_runtime/tool_runtime.py:_register_math_add` |
| Governance | None |
| Legacy Alias | none |
| Deprecation | none |

**Input Schema:**
```json
{
  "a": {"type": "number", "required": true},
  "b": {"type": "number", "required": true}
}
```

**Output Schema:**
```json
{"status": "success", "result": 5}
```

---

### opencode.run

| Field | Value |
|-------|-------|
| Canonical Name | `opencode.run` |
| UTR Status | IMPLEMENTED |
| Risk | HIGH |
| SafetyGate | `HIGH_RISK_TOOLS` |
| Executor | `features/tool_runtime/tool_runtime.py:_register_opencode_run` |
| Governance | Explicit `permit()` required |
| Legacy Alias | none |
| Deprecation | none |

**Input Schema:**
```json
{
  "command": {"type": "string", "required": true},
  "timeout": {"type": "number", "default": 30}
}
```

**Output Schema:**
```json
{"status": "success", "output": "<stdout>", "returncode": 0}
```

---

### browser.open

| Field | Value |
|-------|-------|
| Canonical Name | `browser.open` |
| UTR Status | IMPLEMENTED |
| Risk | HIGH |
| SafetyGate | `HIGH_RISK_TOOLS` |
| Executor | `features/tool_runtime/tool_runtime.py:BrowserAgent.open` |
| Governance | URL validation |
| Legacy Alias | none |
| Deprecation | none |

**Input Schema:**
```json
{"url": {"type": "string", "required": true, "pattern": "^https?://"}}
```

**Output Schema:**
```json
{"status": "opened", "url": "<resolved url>", "title": "<page title>"}
```

---

### browser.click

| Field | Value |
|-------|-------|
| Canonical Name | `browser.click` |
| UTR Status | IMPLEMENTED |
| Risk | HIGH |
| SafetyGate | `HIGH_RISK_TOOLS` |
| Executor | `features/tool_runtime/tool_runtime.py:BrowserAgent.click` |
| Governance | None |
| Legacy Alias | none |
| Deprecation | none |

**Input Schema:**
```json
{"selector": {"type": "string", "required": true}}
```

**Output Schema:**
```json
{"status": "clicked", "selector": "<selector>"}
```

---

### browser.type

| Field | Value |
|-------|-------|
| Canonical Name | `browser.type` |
| UTR Status | IMPLEMENTED |
| Risk | HIGH |
| SafetyGate | `HIGH_RISK_TOOLS` |
| Executor | `features/tool_runtime/tool_runtime.py:BrowserAgent.type_text` |
| Governance | None |
| Legacy Alias | none |
| Deprecation | none |

**Input Schema:**
```json
{
  "selector": {"type": "string", "required": true},
  "text": {"type": "string", "required": true}
}
```

**Output Schema:**
```json
{"status": "typed", "selector": "<selector>"}
```

---

### browser.extract_text

| Field | Value |
|-------|-------|
| Canonical Name | `browser.extract_text` |
| UTR Status | IMPLEMENTED |
| Risk | HIGH |
| SafetyGate | `HIGH_RISK_TOOLS` |
| Executor | `features/tool_runtime/tool_runtime.py:BrowserAgent.extract_text` |
| Governance | None |
| Legacy Alias | none |
| Deprecation | none |

**Input Schema:**
```json
{"selector": {"type": "string", "default": "body"}}
```

**Output Schema:**
```json
{"status": "success", "text": "<extracted text>", "length": 123}
```

---

### browser.screenshot

| Field | Value |
|-------|-------|
| Canonical Name | `browser.screenshot` |
| UTR Status | IMPLEMENTED |
| Risk | HIGH |
| SafetyGate | `HIGH_RISK_TOOLS` |
| Executor | `features/tool_runtime/tool_runtime.py:BrowserAgent.screenshot` |
| Governance | None |
| Legacy Alias | none |
| Deprecation | none |

**Input Schema:**
```json
{}
```

**Output Schema:**
```json
{"status": "success", "screenshot_path": "<path>"}
```

---

### browser.scroll

| Field | Value |
|-------|-------|
| Canonical Name | `browser.scroll` |
| UTR Status | IMPLEMENTED |
| Risk | HIGH |
| SafetyGate | `HIGH_RISK_TOOLS` |
| Executor | `features/tool_runtime/tool_runtime.py:BrowserAgent.scroll` |
| Governance | None |
| Legacy Alias | none |
| Deprecation | none |

**Input Schema:**
```json
{"direction": {"type": "string", "enum": ["up", "down"], "default": "down"}}
```

**Output Schema:**
```json
{"status": "scrolled", "direction": "<direction>"}
```

---

### desktop.* tools

All desktop tools (desktop.screenshot, desktop.type, desktop.click, desktop.open_app, desktop.move, desktop.keypress) are registered in UTR as UNAVAILABLE stubs — no pyautogui implementation exists.

| Field | Value |
|-------|-------|
| Canonical Name | `desktop.*` |
| UTR Status | STUB |
| Risk | HIGH |
| SafetyGate | `HIGH_RISK_TOOLS` |
| Executor | Stub returning unavailable |
| Governance | N/A |
| Legacy Alias | none |
| Deprecation | none |

---

## Execution Path Summary

```
Hot Path (kernel.py:run → mel.py):
  kernel.run()
    → mel.execute(plan)
      → UTR.execute(tool_name, args)
        → SafetyGate.check(tool_name, args)
        → Executor function

Warm Path (kernel.py:_run_pipeline):
  Pipeline (11 stages)
    → MEL stage
      → UTR.execute(tool_name, args)
        → SafetyGate.check(tool_name, args)
        → Executor function

CognitiveUnit Path (not yet active in pipeline):
  CU.execute(context)
    → Governance.check(context)
    → SafetyGate.check(tool_name, args)
    → UTR.execute(tool_name, args)
    → Executor function

Deprecated Paths (fallback only):
  mel.py:_execute_step → TOOL_REGISTRY (if UTR returns Unknown tool)
  muscal_loop.py:execute_tool → EXECUTORS
  system_runtime.py:execute → UTR (redirected)
```

## Legacy Aliases

| Legacy Name | Canonical Name | Status |
|-------------|----------------|--------|
| `file.write` | `filesystem.write` | Alias — both registered in UTR |

## Tools Not Yet Implemented

| Tool | Reason |
|------|--------|
| `desktop.screenshot` | No pyautogui dependency |
| `desktop.type` | No pyautogui dependency |
| `desktop.click` | No pyautogui dependency |
| `desktop.open_app` | No pyautogui dependency |
| `desktop.move` | No pyautogui dependency |
| `desktop.keypress` | No pyautogui dependency |
