# STUB INVENTORY

**Date:** 2026-07-09  
**Last updated:** 2026-07-10 (8 files deleted in 23.27)  
**Total files (≤20 lines):** 83 (25 `__init__.py` + 58 non-init stubs)

---

## 1. Package `__init__.py` — ✅ BEHALTEN (25 files, 0 lines each)

Standard Python package markers. Alle leer (0 lines). Keine Aktion.

```
./api/__init__.py
./core/__init__.py
./features/__init__.py
./features/auth/__init__.py
./features/bridge/__init__.py
./features/memory/__init__.py
./features/mkc/__init__.py
./features/runtime/__init__.py
./guards/__init__.py
./runtime/__init__.py
./runtime/api/blueprints/__init__.py
./runtime/kernel/__init__.py
./runtime/llm/__init__.py
./runtime/observation/__init__.py
./runtime/services/__init__.py
./tests/__init__.py
./tests/api/__init__.py
./tests/compiler/__init__.py
./tests/execution/__init__.py
./tests/graph/__init__.py
./tests/kernel/__init__.py
./tests/memory/__init__.py
./tests/reference/__init__.py
```

---

## 2. `minimal_*` — ⚠️ PLACEHOLDER (9 files)

Minimal-Implementierungen als Platzhalter für Roadmap-Items. Später durch volle Implementierung ersetzt oder als deprecated markiert.

| File | Lines | Status |
|------|-------|--------|
| `minimal_context.py` | 3 | Placeholder |
| `minimal_graph_memory.py` | 4 | Placeholder |
| `minimal_mcxf_memory.py` | 6 | **AKTIV** — re-exports MCXFMemoryStore |
| `minimal_memory.py` | 6 | Placeholder |
| `minimal_mkc.py` | 6 | Placeholder |
| `minimal_feedback.py` | 9 | Placeholder |
| `minimal_rag.py` | 13 | Placeholder |
| `minimal_evaluator.py` | 15 | Placeholder |
| `simple_mkc.py` | 18 | Vereinfachte MKC |

---

## 3. Active Minimal Components — ✅ BEHALTEN (7 files)

Liefern echte Funktionalität trotz geringer Zeilenzahl.

| File | Lines | Funktion |
|------|-------|----------|
| `simple_trace.py` | 9 | Trace-Implementierung |
| `simple_executor.py` | 16 | Execution-Implementierung |
| `embedder.py` | 10 | Embedding-Layer |
| `runtime/api/errors.py` | 9 | Error-Handling für API |
| `runtime/api/handoff.py` | 16 | Handoff-Endpoint |
| `api/main.py` | 3 | Entry Point |
| `ui_state.py` | 8 | UI-State-Modell |
| `compiler_version.py` | 16 | Compiler-Versionierung |
| `tests/conftest.py` | 4 | pytest-Konfiguration |

---

## 4. Deleted in 23.27 Cleanup — 🗑️ GELÖSCHT (8 files)

Alle unbenutzt, kein aktiver Code importiert sie. Siehe 23.27-Stabilization-Review.

| File | Grund |
|------|-------|
| `event_bus_swarm.py` | DEPRECATED, Scheduled für v0.9 Removal |
| `muscal_swarm.py` | Dead — Swarm nicht funktionsfähig |
| `muscal_node.py` | Dead — abhängig von Swarm |
| `rag_minimal.py` | Duplikat von `minimal_rag.py` |
| `global_memory.py` | Ersetzt durch `interfaces.py` Protocols |
| `core/swarm.py` | Deprecated Chain, einziger User von muscal_swarm+muscal_node |
| `bootstrap.py` | DEPRECATED, einziger User von core/swarm.py |
| `minimal.py` | Standalone-Script, einziger User von rag_minimal.py |

---

## 5. Duplikate / Redundant — 🔴 DUPLIKAT (4 files — 2 gelöscht)

Ersetzt durch modernere Interfaces oder nicht mehr verwendet.

| File | Lines | Grund |
|------|-------|-------|
| `memory_system.py` | 12 | Ersetzt durch `interfaces.py` Protocols (Blocked: kernel_core.py FROZEN) |
| `meta_compiler.py` | 10 | Nicht verwendet, MKC ist aktiv |
| `compiler_updater.py` | 5 | Nicht verwendet |
| `compiler_validator.py` | 12 | Nicht verwendet (mkc.py validiert selbst) |

---

## 6. Performance / Analyse / Evaluation — ⚠️ PLACEHOLDER (9 files)

Roadmap-Stubs. Nicht implementiert, aber für spätere Features vorgemerkt.

| File | Lines |
|------|-------|
| `performance_analyzer.py` | 6 |
| `decision_analyzer.py` | 8 |
| `scenario_evaluator.py` | 8 |
| `explanation_builder.py` | 9 |
| `explanation_refiner.py` | 9 |
| `metric_evolution_engine.py` | 9 |
| `causality_engine.py` | 15 |
| `counterfactual_engine.py` | 16 |
| `evolution_evaluator.py` | 19 |

---

## 7. Consensus / Coordination — ⚠️ PLACEHOLDER (6 files)

| File | Lines |
|------|-------|
| `consensus_engine.py` | 18 |
| `evolving_critique.py` | 18 |
| `emergent_consensus.py` | 16 |
| `evolution_mkc.py` | 17 |
| `message_broker.py` | 13 |
| `metric_registry.py` | 13 |

---

## 8. Router / Task / Browser — ⚠️ PLACEHOLDER (8 files)

| File | Lines |
|------|-------|
| `adaptive_router.py` | 11 |
| `browser_executor.py` | 8 |
| `browser_router.py` | 8 |
| `browser_node.py` | 13 |
| `task_router.py` | 12 |
| `task_queue.py` | 17 |
| `task_model.py` | 6 |
| `safe_executor.py` | 6 |

---

## 9. Memory Ancillary — ⚠️ PLACEHOLDER (4 files)

| File | Lines |
|------|-------|
| `distributed_memory.py` | 9 |
| `memory_compressor.py` | 16 |
| `memory_rewriter.py` | 20 |
| `replay_engine.py` | 16 |

---

## 10. Vision / Worker — ⚠️ PLACEHOLDER (5 files)

| File | Lines |
|------|-------|
| `vision_layer.py` | 12 |
| `vision_planner.py` | 12 |
| `worker_node.py` | 13 |
| `state_builder.py` | 13 |
| `result_collector.py` | 12 |

---

## 11. Unclassified — ❓ UNKLAR (5 files)

Nicht eindeutig zuordenbar. Braucht manuelle Prüfung.

| File | Lines | Frage |
|------|-------|-------|
| `reconfig_engine.py` | 11 | Wird das noch gebraucht? |
| `reasoning_engine.py` | 12 | Roadmap oder dead? |
| `loop_controller.py` | 15 | Wird das noch gebraucht? |
| `triple_extractor.py` | 20 | Teil von MKC? |
| `vector_memory.py` | 20 | Teil von Memory? |
| `compiler_state.py` | 15 | Teil von MKC? |
| `event_node.py` | 14 | Teil von EventBus? |

---

## Zusammenfassung

| Kategorie | Count | Aktion |
|-----------|-------|--------|
| ✅ Package `__init__.py` | 25 | behalten |
| ✅ Active Minimal | 9 | behalten |
| ⚠️ Placeholder | 41 | behalten (Roadmap) |
| 🗑️ Deleted (23.27) | 8 | gelöscht |
| 🔴 Duplikat (Blocked) | 4 | entfernen (nach Freeze 2026-08-08) |
| ❓ Unklar | 7 | prüfen |
| **Total existing** | **83** | |
| **Total deleted** | **8** | |
