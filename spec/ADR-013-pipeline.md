# ADR-013: Feature Plugin Migration Path (historisch — superseded by ADR-007)

**Hinweis (2026-08-01):** Diese Datei war fälschlich als „ADR-007" benannt; der Inhalt ist der
historische ADR-007-Entwurf (Feature Plugin Migration Path). Gemäß `spec/ADR-INDEX.md` wird der
Inhalt als ADR-013 (historisch, superseded by ADR-007 Core Immutability) geführt.

**Context:** The project's architecture mandates that all extensions go to `features/` as plugins (`AGENTS.md` / `SESSION_RULES.md`). However, the current `features/` directory contains mostly empty shells:

```
features/
├── __init__.py        (empty)
├── bridge/            (1 plugin: input_classifier_plugin.py)
├── memory/            (empty __init__.py only)
├── mkc/               (4 plugins: audit, confidence, rag_enrich, trace)
└── runtime/           (1 plugin: health_monitor.py)
```

Meanwhile, the active pipeline imports directly from top-level modules (`kernel.py`, `mkc.py`, `bridge.py`, `mel.py`, `memory.py`, `rag.py`, `feedback.py`, `graph.py`, `event_bus.py`), which are listed as IMMUTABLE CORE files. This creates a tension: core is immutable but also the only place where pipeline logic lives. New features cannot be implemented as plugins because the plugin system (`plugin_registry.py` / `plugin_loader.py`) only provides hooks, not pipeline composition.

Concretely:
- The `HOOKS` dict in `plugin_registry.py` supports `kernel_before/after`, `mkc_before/after`, `bridge_before/after`, `mel_before/after`, `feedback_before/after`, `memory_before/after` — all passive observation hooks.
- No hook allows a plugin to REPLACE a pipeline stage.
- No hook allows a plugin to INSERT a new stage between existing ones.

**Decision:** We transition the plugin system from **Hook-Only** to **Pipeline-Composable** in 3 phases:

### Phase 1 — Pipeline Stage Protocol (now)
Define a `PipelineStage` protocol in `interfaces.py`:

```python
class PipelineStage(Protocol):
    name: str
    order: int  # sort key for insertion
    def process(self, context: dict) -> dict: ...
```

Each core module (`mkc`, `bridge`, `mel`, `feedback`, `memory`) gets a thin adapter wrapping its current API into `PipelineStage`. The adapter lives in `features/` and imports the immutable core module.

### Phase 2 — Plugin Pipeline Registry (next)
Extend `plugin_registry.py` with:
```python
def register_stage(stage: PipelineStage, before: str = None, after: str = None): ...
def build_pipeline(stages: list[str]) -> list[PipelineStage]: ...
```

This allows plugins to:
- Insert new stages between existing ones
- Wrap stages with monitoring/logging/validation
- Replace a stage (with explicit override flag)

### Phase 3 — Migration (after freeze)
Move the following into `features/` as plugins:
- All existing `features/bridge/`, `features/mkc/`, `features/memory/`, `features/runtime/` plugins are ported to the new Protocol
- Pipeline composition moves from hardcoded `kernel.py` to `build_pipeline()` calls
- Core modules remain immutable; plugin adapters are the extension surface

**Consequences:**
- + Clear, typed protocol for pipeline composition
- + Plugins can finally REPLACE pipeline stages (e.g., custom compiler)
- + Backward compatible: existing hooks continue to work
- + Core immutability preserved (adapters live in `features/`)
- - Requires changes to `plugin_registry.py` (core file — needs `--allow-core-write`)
- - Migration takes multiple iterations for full rollout
- - Pipeline ordering becomes dynamic (harder to reason about at a glance)

**Rationale:** The current hook-only system was a good start but cannot fulfill the architecture mandate of "all extensions go to features/." Without pipeline-stage composability, every new feature either requires a core change (violating immutability) or is limited to passive observation. The `PipelineStage` protocol is minimal, typed, and composable — exactly what a plugin system needs.

**Datum:** 2026-07-08
**Status:** SUPERSEDED (by ADR-007 — Core Immutability, Write Guard Policy)
**Supersedes:** —
