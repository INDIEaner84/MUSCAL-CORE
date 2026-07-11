# ADR-001: Kernel Runtime — Single Pipeline Authority

**Status:** ACCEPTED — Phase 1 ✅  
**Date:** 2026-07-08  
**Author:** MASTER ORCHESTRATOR  

---

## Context

MUSCAL v0.7 hat **4 verschiedene Kernel-Implementierungen**:

| Kernel | File | LOC | Status |
|--------|------|-----|--------|
| **MuscalKernel** | `kernel.py` | 448 | ✅ ACTIV — Vollständige Pipeline |
| **Kernel (minimal)** | `kernel_core.py` | 68 | ⛔ DEPRECATED ab v0.8 |
| **DistributedKernel** | `distributed_kernel.py` | ~10 | ⏳ Stub |
| **MuscalLoop** | `muscal_loop.py` | 565 | ⚠️ Legacy — LLM-Orchestrator, eigene Pipeline |

Diese Redundanz verursacht:
- **Wartungsaufwand** — Änderungen müssen 4x gemacht werden
- **Inkonsistenz** — Unterschiedliche Fehlerbehandlung, Event-Routing, Plugin-Integration
- **Unklare Zuständigkeit** — Welcher Kernel ist der "echte"?

---

## Decision

**`MuscalKernel` (`kernel.py`) ist die einzige Runtime-Pipeline.**

Begründung:
- Vollständigste Implementierung (alle 8 Pipeline-Stufen)
- Plugin-System via `run_hooks()` integriert
- Graph/Sphere/EventBus angebunden
- Debugger-Integration
- Getestet (13 pytest-Tests + Stresstest + Plugin-Tests)

---

## Migration Plan

### Phase 1: Deprecate `kernel_core.py` ✅

```python
# kernel_core.py — ab v0.8 deprecated (APPLIED)
import warnings
warnings.warn(
    "kernel_core.py is deprecated. Use kernel.MuscalKernel instead.",
    DeprecationWarning, stacklevel=2
)
```

### Phase 2: Replace callee references 🔲

`memory_system.py` und `graph_system_loop.py` nutzen bereits `graph_memory.GraphMemory` (kein Import von `kernel_core`).  
Prüfen: Existieren Skripte, die `from kernel_core import Kernel` importieren?

### Phase 3: MuscalLoop audit ⏳

`muscal_loop.py` (565 LOC) — Analyse abgeschlossen:

**Dupliziert mit `MuscalKernel`:**
| Funktion in muscal_loop.py | Entspricht in kernel.py |
|---|---|
| `EXECUTORS` dict (Zeile 372) | `mel.py` + `tools.py` (TOOL_REGISTRY) |
| `validate_tasks()` (Zeile 277) | `bridge.validate_plan()` + `mkc_rules.SIGNAL_RULES` |
| `build_feedback()` (Zeile 400) | `feedback.py` (FeedbackModule) |
| `llm_compile()` → MCXF (Zeile 250) | `mkc.py` + `mkc_rules.py` |
| `parse_mcxf()` (Zeile 260) | `schema.py` (MCXFDocument, validate_mcxf) |

**Echte Erweiterung (nicht in MuscalKernel):**
| Funktion | Beschreibung |
|---|---|
| `MuscalLoop.run()` | Iterativer LLM-gesteuerter Loop (MAX_ITERATIONS) |
| `BrowserAgent` | Playwright-Browser-Lebenszyklus |
| `_stub_llm()` / `_ollama_llm()` | LLM-Compiler (Stub-deterministisch oder Ollama) |
| `StateStore` + `KernelDiffEngine` | State-Diff-Tracking zwischen Iterationen |
| `ReplayEngine` | Replay-Fähigkeit |

**Empfehlung:** `MuscalLoop` behält den LLM-Orchestrierungs-Loop, Browser-Lebenszyklus, State-Diff-Tracking.  
Die innere Pipeline (`EXECUTORS`, `validate_tasks`, `build_feedback`, `parse_mcxf`) wird durch `MuscalKernel.run()` ersetzt.

### Phase 4: Remove stubs 🔲

- `distributed_kernel.py` → Nach Produktivsetzung von `MuscalKernel` entfernen
- `kernel_core.py` → Nach Migration aller Consumer entfernen

---

## Consequences

### Positive
- Ein Single Point of Truth für die Pipeline
- Weniger Wartungsaufwand
- Einheitliches Event-Routing und Plugin-System
- Klare API für externe Konsumenten

### Negative
- `muscal_loop.py`-Refactoring nötig (größter Einzelfile mit 562 LOC)
- Bestehende Skripte, die `kernel_core.Kernel` nutzen, müssen migrieren

### Neutral
- `DistributedKernel` ist ein Stub — kein Migrationseffekt

---

## Compliance Checklist

- [x] `kernel_core.py` deprecated (Phase 1) — APPLIED
- [ ] Alle Imports von `kernel_core` ersetzt (Phase 2)
- [ ] `muscal_loop.py` innere Pipeline durch `MuscalKernel` ersetzt (Phase 3)
- [ ] Stubs entfernt (Phase 4)
- [ ] Alle Tests passieren nach Migration
