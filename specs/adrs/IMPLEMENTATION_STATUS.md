# ADR Implementation Status

> **DEPRECATED** — Historical ADR implementation status from v0.7 prototype.
> ADR numbering and statuses have been restructured.
> Current authoritative ADR index: `spec/ADR-INDEX.md`
> Retained for historical reference only.

> Stand: 2026-07-09 | Checkpoint 23.28 — Architecture Audit

| ADR | Titel | Status | Phase | Impl. % | Letzte Änderung |
|-----|-------|--------|-------|---------|-----------------|
| 001 | Execution Graph Compiler statt Interpreter | ACCEPTED | — | 30 % | 2026-07-04 |
| 002 | Layer-Architektur mit Spine-Validierung | ACCEPTED | — | 20 % | 2026-07-04 |
| 003 | Capability-First statt Model-First | ACCEPTED | — | 10 % | 2026-07-04 |
| 004 | GraphMemory Interface Consolidation | ACCEPTED | ✅ DONE | 100 % | 2026-07-08 |
| 005 | Kernel Interface Consolidation | ACCEPTED | ✅ DONE | 100 % | 2026-07-08 |
| 006 | Dead Code Deprecation Lifecycle | ACCEPTED | Phase 2/4 | 75 % | 2026-07-09 |
| 007 | Feature Plugin Migration Path | ACCEPTED | Phase 2/3 | 60 % | 2026-07-09 |

---

## ADR-001 — Execution Graph Compiler

**Ziel:** MCXF/YAML/MKC-Output in validierten, optimierten Execution DAG compilieren.

### Umgesetzt
- `runtime/optimizer/graph.py` — `ExecutionDAG` + `DAGNode`-Dataclasses
- `runtime/optimizer/pipeline.py` — `OptimizedPlan` mit Layer-Struktur
- `runtime/optimizer/base_pass.py` — `OptimizationPass`-ABC

### Nicht umgesetzt
- MAS-0301 Compiler-Pfad (AST → optimierter DAG)
- BNF-Parser in MKC
- Bridge-Matcher → AST-Node-Translation
- Spine-Validierung als HARD GATE

### Blocked by
- Kein aktiver Entwicklungsfokus

---

## ADR-002 — Layer-Architektur mit Spine-Validierung

**Ziel:** 7-Layer-Architektur (L0–L6) mit 4 Sub-Kernels und Spine-Validierung.

### Umgesetzt
- (Keine Code-Implementierung)

### Nicht umgesetzt
- Layer-Zuordnung in Modulen
- Spine-Validierung für Event-Transitionen
- Verbotene Transitionen
- Bridge-Registration

### Blocked by
- Keine Runtime-Infrastruktur für Layer-Prüfung

---

## ADR-003 — Capability-First statt Model-First

**Ziel:** Task-Routing gegen Capabilities, nicht Modell-Namen.

### Umgesetzt
- (Keine Code-Implementierung)

### Nicht umgesetzt
- Capability Registry
- Capability-basiertes Routing in `scheduler.py`
- Capability-basiertes Routing in `bridge.py`
- MREIL-gesteuerte Auswahl

### Blocked by
- Capability Registry nicht definiert

---

## ADR-004 — GraphMemory Interface Consolidation

**Ziel:** Einheitliches `MemoryProvider`-Protokoll für alle Memory-Implementierungen.

### Umgesetzt
- `interfaces.py`:
  - `MemoryProvider`-Protokoll (graph + store + store_snapshot + search)
  - `GraphMemoryProvider`-Protokoll (add_node, add_edge, get_node, ...)
  - `MemoryStoreProvider`-Protokoll (save, retrieve, search)
- `features/memory/sqlite_adapter.py` — `SQLiteMemoryAdapter` implementiert `MemoryStoreProvider`
- `features/memory/unified_memory.py` — `UnifiedMemory` implementiert `MemoryProvider`
- `tests/test_core_pipeline.py` — 3 Memory-Tests (store, feedback, graph-ingest)

### Status: ✅ DONE

---

## ADR-005 — Kernel Interface Consolidation

**Ziel:** `MuscalKernel` (kernel.py) als alleinige Authority; `kernel_core.Kernel` deprecated.

### Umgesetzt
- `kernel.py` — aktiv, unverändert
- `kernel_core.py` — FROZEN seit 2026-07-09 (ADR-006)
- `interfaces.py` — `KernelProvider`-Protokoll
- `spec/OVERRIDE.md` — OVERRIDE-018: MKC Exception Handling dokumentiert
- 7 kernel_core-Dependencies mit DEPRECATED-Headern

### Status: ✅ DONE

---

## ADR-006 — Dead Code Deprecation Lifecycle

**Ziel:** 4-Stufen-Lebenszyklus für toten Code.

### Phasen-Status

| Phase | Status | Beschreibung | Datum |
|-------|--------|-------------|-------|
| 1 Labelled | ✅ DONE | DEPRECATED-Header in kernel_core.py + 7 Dependencies | 2026-07-08 |
| 2 Frozen | ✅ DONE | kernel_core.py FROZEN bis 2026-08-08 | 2026-07-09 |
| 3 Archived | ❌ OFFEN | Verschiebung nach attic/ | nach 2026-08-08 |
| 4 Deleted | ❌ OFFEN | Entfernung nach nächstem Release | nach Archivierung |

### Dateien mit DEPRECATED-Header
- `kernel_core.py` — ⚠️ FROZEN
- `simple_executor.py`, `simple_mkc.py`, `simple_rag.py`, `simple_trace.py`
- `minimal_graph_memory.py`, `minimal_memory.py`
- `evolution_evaluator.py`

### Nächster Schritt
- Phase 3 starten nach 2026-08-08: Dateien nach `attic/kernel_core/` verschieben
- `attic/INDEX.md` mit Manifest erstellen

---

## ADR-007 — Feature Plugin Migration Path

**Ziel:** Plugin-System von Hook-Only zu Pipeline-Composable migrieren.

### Phasen-Status

| Phase | Status | Beschreibung | Datum |
|-------|--------|-------------|-------|
| 1 Protocol | ✅ DONE | `PipelineStage` in `interfaces.py` + `PipelineBuilder` in `features/runtime/pipeline_builder.py` | 2026-07-08 |
| 2 Registry | ✅ DONE | `STAGES`, `register_stage()`, `build_pipeline()` in `plugin_registry.py` | 2026-07-09 |
| 3 Migration | ❌ OFFEN | kernel.py auf `build_pipeline()` umstellen | Blocked |

### Umgesetzt (Phase 1+2)
- `interfaces.py:49-60` — `PipelineStage`-Protokoll
- `features/runtime/pipeline_builder.py` — `PipelineBuilder` (register + build)
- `plugin_registry.py` — `STAGES`-Dict, `register_stage()`, `build_pipeline()`
- `tests/test_boot_contract.py` — 4 Tests für register_stage/build_pipeline

### Phase 3 Blocked by
- `kernel.py` ist immutable (AGENTS.md)
- Erfordert `--allow-core-write` und OVERRIDE-Dokumentation
- Bestehende Pipeline muss parallel weiterlaufen (Rückwärtskompatibilität)

### Migration Checklist (Phase 3)
- [ ] OVERRIDE-Dokumentation in `spec/OVERRIDE.md`
- [ ] PipelineStage-Adapter für MKC in `features/mkc/`
- [ ] PipelineStage-Adapter für Bridge in `features/bridge/`
- [ ] PipelineStage-Adapter für MEL in `features/runtime/`
- [ ] PipelineStage-Adapter für Optimizer in `features/runtime/`
- [ ] kernel.py: `build_pipeline()` statt hardcodierter Stages
- [ ] Tests: kernel.py-Pipeline verhält sich identisch

---

## Zusammenfassung

```
ADR-001  30 % ███████░░░░░░░░░░░░░
ADR-002  20 % ████░░░░░░░░░░░░░░░░
ADR-003  10 % ██░░░░░░░░░░░░░░░░░░
ADR-004 100 % ████████████████████  ✅
ADR-005 100 % ████████████████████  ✅
ADR-006  75 % ███████████████░░░░░
ADR-007  60 % ████████████░░░░░░░░
         ───── ───────────────────
         55 %  ⚠️  Mittel
```

**4 von 7 ADRs vollständig implementiert (ADR-004, 005, 006 Phase 1-2, 007 Phase 1-2).**
**3 von 7 ADRs (001, 002, 003) haben keine signifikante Code-Implementierung.**
