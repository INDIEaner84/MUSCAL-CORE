# Test Coverage Report

> Stand: 2026-07-09 | Checkpoint 23.28 — Architecture Audit

## Test Suite Overview

| Metrik | Wert |
|--------|------|
| pytest-kompatible Tests | 119 (11 Dateien) |
| Script-basierte Checks | 28 Dateien (nicht pytest-kompatibel) |
| Collection Errors | 0 |
| xfail-Marker | 0 |
| Gesamt Pass | 119 / 119 |
| Testabdeckung (Module direkt) | ~28 / ~200 (14 %) |

---

## Pytest-Kompatible Tests (119)

| Datei | Tests | Getestete Module |
|-------|-------|------------------|
| `test_core_pipeline.py` | 19 | bridge, mkc, mel, schema, features/memory/unified_memory, runtime/optimizer/pipeline |
| `test_graph.py` | 26 | graph, event_bus, schema |
| `test_events.py` | 14 | event_bus |
| `test_boot.py` | 13 | kernel |
| `test_state_transition.py` | 9 | kernel, memory, schema, event_bus |
| `test_system_optimizer_pipeline.py` | 9 | runtime/optimizer/pipeline, runtime/optimizer/graph, schema |
| `test_boot_contract.py` | 8 | config, memory, kernel, plugin_registry, plugin_loader, schema, event_bus |
| `test_graph_memory.py` | 8 | graph_memory |
| `test_eventbus_verification.py` | 6 | event_bus |
| `test_event_contract.py` | 5 | event_bus |
| `test_lambda_closure.py` | 2 | kernel |

---

## Script-basierte Tests (28 — nicht von pytest erfasst)

Diese Dateien verwenden `def check()` und `sys.exit(1)` bei Fehlern.
Müssen manuell mit `python tests/<pfad>` ausgeführt werden.

| Bereich | Dateien | Tests |
|---------|---------|-------|
| API | `api/test_api_boot.py` | 6 |
| Compiler | `compiler/test_bridge.py`, `compiler/test_mkc.py` | 22 |
| Container | `container/test_deployment.py` | 12 |
| Contract | `contract/test_supervisor_lifecycle.py` * | 10 |
| Execution | `execution/test_mel.py` | 10 |
| Graph | `graph/test_graph.py` | 16 |
| Kernel | `kernel/test_boot.py`, `kernel/test_events.py`, `kernel/test_state_transition.py` | 30 |
| Memory | `memory/test_memory.py` | 8 |
| Reference | `reference/test_full_pipeline.py`, `reference/test_execution_trace.py`, `reference/test_memory_consistency.py`, `reference/test_replay_determinism.py` | 53 |
| Security | `security/test_database_validation.py`, `security/test_input_limits.py`, `security/test_path_policy.py`, `security/test_tool_return_contract.py` | 27 |
| Plugins | `plugin_loading.py`, `plugin_audit.py`, `plugin_confidence.py`, `plugin_health.py`, `hook_coverage.py` | 40 |
| Stress | `stress_test.py` | 2 |

\* `test_supervisor_lifecycle.py` — läuft durch (ALL PASS). Hinweis: pytest ignoriert `tests/contract/` via `norecursedirs` in `pyproject.toml`.

---

## Coverage by Module Group

### Critical Path (MKC → Bridge → Optimizer → MEL → Memory)

| Modul | Tests | Coverage |
|-------|-------|----------|
| `kernel.py` | ✅ test_boot (13), test_state_transition (9), test_lambda_closure (2), test_boot_contract | Hoch |
| `mkc.py` | ✅ test_core_pipeline (3), test_boot_contract | Mittel |
| `bridge.py` | ✅ test_core_pipeline (3) | Mittel |
| `mel.py` | ✅ test_core_pipeline (2), test_global_state | Mittel |
| `runtime/optimizer/pipeline.py` | ✅ test_core_pipeline (5), system/test_optimizer_pipeline (9) | Hoch |
| `features/memory/unified_memory.py` | ✅ test_core_pipeline (3) | Mittel |
| `memory.py` | ✅ test_global_state, test_determinism, memory/, reference/ | Hoch |
| `schema.py` | ✅ test_core_pipeline, test_graph, test_state_transition, ... | Hoch |
| `event_bus.py` | ✅ test_events (14), test_event_contract (5), test_eventbus_verification (6) | Hoch |
| `graph.py` | ✅ test_graph (26) | Hoch |

### Unterstützende Module

| Modul | Tests | Coverage |
|-------|-------|----------|
| `rag.py` | ✅ test_determinism | Niedrig |
| `feedback.py` | ✅ test_core_pipeline (1) | Niedrig |
| `tools.py` | ✅ security/test_tool_return_contract, security/test_path_policy | Mittel |
| `config.py` | ✅ test_boot_contract, test_import_safety, container/ | Mittel |
| `plugin_loader.py` | ✅ test_boot_contract, plugin_*.py | Mittel |
| `plugin_registry.py` | ✅ test_boot_contract (5), plugin_*.py | Hoch |
| `mkc_rules.py` | ✅ test_core_pipeline (1), reference/, test_global_state | Mittel |
| `runtime/database.py` | ✅ security/test_database_validation | Niedrig |
| `runtime/llm/client.py` | ✅ test_import_safety | Niedrig |

### Unzureichend getestet

| Modul | Problem |
|-------|---------|
| `features/memory/sqlite_adapter.py` | Nur indirekt über UnifiedMemory getestet |
| `features/` plugins (10 Dateien) | Keine Isolationstests |
| `runtime/optimizer/*` (außer pipeline/graph) | base_pass, report, etc. nicht isoliert getestet |
| `runtime/api/*` | Nur create_app-Import getestet |
| `runtime/kernel/*` | Keine Tests |
| `sphere.py` | Keine Tests |
| `boot_manager.py` | Keine Tests |
| `muscal_os.py` | Keine Tests |

### Nicht getestet (~145 Module)

95 Root-Level-Module + 36 Subpackage-Module + 14 Feature-Plugins haben keine direkten Tests.
Liste: `reports/architecture_audit_23.28.json` → `coverage_summary.untested_critical_modules`

---

## Tech Debt

| Kategorie | Anzahl |
|-----------|--------|
| TODO im Code | 0 |
| FIXME im Code | 0 |
| HACK im Code | 0 |
| xfail-Marker | 0 |
| Collection Errors | 0 |
| Script-Tests (nicht pytest) | 28 |

---

## Empfehlungen

1. **Nächstes Sprint:** 28 Script-Tests in pytest migrieren (CI-Sichtbarkeit)
3. **Kurzfristig:** Adapter-Tests für features/*-Plugins
4. **Mittelfristig:** Coverage für ADR-001/002/003-Kernmodule aufbauen
5. **Langfristig:** Coverage-Ziel 50 % der kritischen Module
