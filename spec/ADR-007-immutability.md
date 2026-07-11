# ADR-007: Core Immutability — Write Guard Policy

**Status:** PROPOSED  
**Date:** 2026-07-08  
**Author:** MASTER ORCHESTRATOR  

---

## Context

MUSCAL v0.7 introduced a **write guard** to prevent accidental modifications to core files:

| Mechanism | File | Scope |
|-----------|------|-------|
| **Write Guard** | `guards/write_guard.py` | Blocks writes to 35+ core files + 6 core directories |
| **Immutability Contract** | `spec/IMMUTABILITY_CONTRACT.md` | Documents which files are immutable and why |
| **Override** | `spec/OVERRIDE.md` | Documents allowed exceptions with reason |

### Protected Files (35+)

```
kernel.py, mkc.py, bridge.py, memory.py, mel.py, schema.py,
mkc_rules.py, config.py, event_bus.py, graph.py, feedback.py,
muscal_os.py, main.py, main_boot.py, boot_manager.py, os_config.py,
sphere.py, debugger.py, tools.py, rag.py, trace_engine.py,
plugin_registry.py, plugin_loader.py

runtime/kernel/*, runtime/llm/*, runtime/optimizer/*,
runtime/api/*, runtime/services/*
```

### Why Immutability?

1. **Stability**: Core files (448 LOC kernel.py, 219 LOC graph.py) have 18 passing tests — modification risks regression
2. **Plugin enforcement**: All new behavior MUST go to `features/` — this is the architectural invariant
3. **Vendor lock prevention**: If core files change every session, no stable API for plugins

### Escalation Path

```
Write to core file?
  ├── Guard blocks? → Check OVERRIDE.md
  │     ├── Override exists? → Allow with --allow-core-write flag
  │     └── No override?   → File issue or create ADR
  └── Not blocked?  → Proceed (e.g. features/, tests/, spec/)
```

---

## Decision

**Accept core immutability as the primary stability mechanism for v0.8.**

### Rules

1. **New behavior** goes to `features/` as a plugin — never to kernel.py
2. **Bug fixes** in core files require a documented override with test evidence
3. **Refactoring** (rename, extract) requires an ADR and approval
4. **Emergency fixes** (crash, data loss) can bypass — but must be documented within 24h

### Override Categories

| Category | Example | Procedure |
|----------|---------|-----------|
| **Bug fix** | Lambda closure bug in kernel.py lines 161/166 | `OVERRIDE.md` entry + test proving the fix |
| **Hook injection** | Adding run_hooks() calls to kernel.py | `OVERRIDE.md` entry + hook test |
| **Interface alignment** | Adding query_related() to graph_memory.py | `OVERRIDE.md` entry + ADR-002 migration |
| **Emergency** | Crash in main.py on empty input | Fix + document within 24h |

### Write Guard Enhancements (v0.8)

Current guard uses a hardcoded list. Future improvements:

```python
# Phase 1: Content-based immutability
# If a file is referenced in spec/IMMUTABILITY_CONTRACT.md, block writes

# Phase 2: Git-based immutability
# If a core file has >50 commits and >300 LOC, require --allow-core-write

# Phase 3: Hash-based immutability
# Store sha256 of approved core files; reject any modification that changes hash
```

---

## Migration Plan

### Phase 1: Content-based guard (v0.8)

Parse `spec/IMMUTABILITY_CONTRACT.md` to build the blocklist dynamically instead of hardcoding.

### Phase 2: Hash verification (v0.9)

On boot, verify core file hashes match `spec/CORE_HASHES.json`. Warn on mismatch.

---

## Consequences

### Positive
- Core stability guarantees — no accidental regressions
- Plugin ecosystem enforced — all new code goes to features/
- Clear override path with documentation requirement
- 18 tests serve as regression check for any core change

### Negative
- Some changes are harder (e.g., hook injection required reading kernel.py first)
- Emergency fixes require post-hoc documentation
- Refactoring requires ADR overhead

### Neutral
- Write guard can be bypassed with `--allow-core-write` for development

---

## Compliance Check

- [ ] Write guard blocks all 35+ core files
- [ ] OVERRIDE.md documents all exceptions
- [ ] Content-based guard (Phase 1) implemented
- [ ] No core files modified outside features/ in last 10 sessions
- [ ] 18/18 tests pass
