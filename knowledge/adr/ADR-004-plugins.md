# ADR-004: Plugin System — Hook-Based Extensions

**Status:** ACCEPTED  
**Date:** 2026-07-08  
**Author:** MASTER ORCHESTRATOR  

---

## Context

MUSCAL v0.7 introduced a plugin system to allow extensions without modifying core files. The system has 3 components:

| Component | File | LOC | Responsibility |
|-----------|------|-----|----------------|
| **Plugin Registry** | `plugin_registry.py` | 160 | 14 hooks, `run_hooks()`, auto-heal, health listeners |
| **Plugin Loader** | `plugin_loader.py` | 57 | Auto-discovery in `features/`, `validate_plugin()` source-scan |
| **Plugins (6)** | `features/*.py` | 40-90 each | Audit, Trace, Confidence, RAG Enrich, Classifier, Health Monitor |

The current design has these properties:
- **Hook-based**: Plugins register callbacks on named hooks (string keys)
- **Context dict**: `run_hooks(name, ctx)` passes a mutable `ctx` dict to all plugins
- **Auto-heal**: Crashing plugins are removed after 3 consecutive failures
- **Boot-time loading**: `load_plugins()` scans `features/` and calls `plugin.register(hooks)` each

### Identified Risks

1. **No isolation**: A plugin crash can corrupt `ctx` mid-pipeline
2. **Ordering undefined**: `run_hooks` iterates `HOOKS[name]` in registration order — no priority or dependency system
3. **No versioning**: Breaking changes to hook signatures or ctx keys are undetectable
4. **No sandbox**: Plugins have full access to `sys`, `os`, filesystem — a malicious or buggy plugin can read/write anything

---

## Decision

**Accept hook-based ctx-passing as the primary extension mechanism for v0.8.**

### Why Not a Plugin IPC / Subprocess Model

- Current plugins are small (40–90 LOC) — subprocess overhead is unjustified
- The pipeline is single-threaded; async IPC adds latency without measurable benefit
- Auto-heal (3 failures → remove) handles the common case (transient errors)

### Constraints Applied

| Constraint | Rule | Enforcement |
|------------|------|-------------|
| **No cross-plugin imports** | Plugin A must not `from features.B import ...` | Code review + `validate_plugin()` scan |
| **ctx is the sole bridge** | Plugin→Plugin communication is via `ctx["key"]` | Runtime convention (no enforcement) |
| **No sys.modules manipulation** | Plugins must not add/remove modules | `validate_plugin()` scan |
| **No direct os.exec / subprocess** | Plugins must not spawn processes | `validate_plugin()` scan (future) |
| **No core file writes** | Plugins cannot modify `kernel.py` etc. | Write Guard blocks at filesystem level |

### Plugin Lifecycle

```
Boot:
  load_plugins()
    ├── scan features/*.py
    ├── import module
    ├── call plugin.register(hooks)
    └── [validation fail] → skip + log warning

Each run():
  run_hooks("kernel_before", ctx)       # pre-pipeline
  run_hooks("mkc_before", ctx)          # pre-MKC
  run_hooks("mkc_after", ctx)           # post-MKC
  run_hooks("bridge_before", ctx)       # pre-Bridge
  run_hooks("bridge_after", ctx)        # post-Bridge
  run_hooks("optimizer_before", ctx)    # pre-Optimizer
  run_hooks("optimizer_after", ctx)     # post-Optimizer
  run_hooks("mel_before", ctx)          # pre-MEL
  run_hooks("mel_after", ctx)           # post-MEL
  run_hooks("feedback_before", ctx)     # pre-Feedback
  run_hooks("feedback_after", ctx)      # post-Feedback
  run_hooks("memory_before", ctx)       # pre-Memory
  run_hooks("memory_after", ctx)        # post-Memory
  run_hooks("kernel_after", ctx)        # post-pipeline
```

### Hook Contract

```python
def run_hooks(name: str, ctx: dict) -> None:
    """
    name: Hook identifier (14 defined constants)
    ctx:  Mutable dict shared across all plugins for this hook.
          Plugins may READ and WRITE ctx keys.
          ctx must preserve all keys added by previous hooks in the same run.
    """
```

---

## Migration Plan

### Phase 1: Priority / Ordering (v0.8)

Add optional `priority` to registration:

```python
hooks["kernel_before"].append((plugin_fn, priority=100))
# Lower number = runs first
```

`run_hooks` sorts by priority before iteration.

### Phase 2: ctx Schema Validation (v0.8)

Each hook defines an expected `ctx` key schema:

```python
HOOK_SCHEMA = {
    "kernel_before": {"required": ["input_text"], "optional": ["kernel"]},
    "mkc_before":    {"required": ["input_text", "enriched_input"]},
    "mkc_after":     {"required": ["mcxf_dict", "mcxf"]},
}
```

Plugins that read undefined keys → logged warning.

### Phase 3: Sandbox (future)

For untrusted plugins, an optional `PluginSandbox` using `exec()` with restricted globals:

```python
sandbox = PluginSandbox(allowed_modules=["json", "re"], allowed_os_calls=["read"])
sandbox.run(plugin.execute, ctx)
```

Not default — only enabled via `plugin_loader.load_plugins(sandbox=True)`.

---

## Consequences

### Positive
- Zero core-file changes needed for new extensions
- Auto-heal handles plugin crashes without pipeline abort
- 14 hooks cover the full pipeline lifecycle
- 6 reference plugins prove the pattern works

### Negative
- No isolation between plugins (ctx corruption possible)
- No ordering guarantee without Phase 1
- Plugin failures are silently swallowed after auto-heal removal
- Debugging plugin interactions requires trace logs

### Neutral
- Plugin API is stable but versionless (will add semver in v0.9)

---

## Compliance Check

- [ ] Phase 1: Priority-based hook ordering
- [ ] Phase 2: ctx schema validation per hook
- [ ] Phase 3: Optional sandbox mode
- [ ] All 6 reference plugins updated for new features
- [ ] `validate_plugin()` scan covers sandbox restrictions
- [ ] 18/18 tests pass after each phase
