# GLOBAL_STATE_ARCHITECTURE_DECISION_DRAFT — ADR-042 Vorschlag

**Status:** DRAFT — keine Akzeptierung ohne Human/ARB Approval
**Date:** 2026-08-01 · **Decision-ID:** D-042 (DECISION_REGISTRY, G2)
**Referenz:** FL01A_FLAKINESS_REGISTER.md (§2 Root Cause), G5_READINESS_REPORT §3-B7
**Mandat:** RC-3 (Decision Closure Package)

---

## 1. Aktueller Singleton-State (Ist-Zustand, [C0])

| Global | Ort | Verwendung | Reset-Mechanismus |
|--------|-----|-----------|-------------------|
| `_UTR = None` / `set_global_utr()` / `_get_global_utr()` | `features/tools/tools.py:9-24` | Tool-Executions teilen eine UTR-Instanz pro Prozess | **keiner** — Modulebene, kein Test-Reset |
| `set_global_default_timeout()` / `get_global_default_timeout()` | `features/tool_runtime/tool_runtime.py:37-42` | globaler Timeout-Wert | **keiner** |
| globaler Event-Store-Zugriff | `tool_runtime.py:28-42` (set/get-global-Event-Store-Pfad) | Persistenz-Pfad im Tool-Runtime | **keiner** |

**Konsequenz:** Modulebene-Globals werden über Test-Läufe hinweg mutiert; Tests sind
reihenfolge-abhängig (FL-01a: 19 Tests; verifiziert grün in Isolation/Subset).

## 2. Risiken

| # | Risiko | Severity |
|---|--------|----------|
| G-R1 | Order-Dependent-Failures in CI (19 dokumentierte Tests, D-040) | MEDIUM |
| G-R2 | Recalibrierungs-Drift: EXPECTED_TOTAL=470 (FL-01b) könnte bei weiterer Singleton-Mutation erneut falsch werden | MEDIUM |
| G-R3 | Falsche Alarmierung verschleiert echte Regressionen (G5-§3-B7) | MEDIUM |
| G-R4 | Parallele Test-Ausführung (falls eingeführt) deterministisch unbrauchbar | LOW (derzeit nicht genutzt) |

## 3. Alternativen

| Option | Beschreibung | Code-Wirkung | Aufwand | Bewertung |
|--------|--------------|--------------|---------|-----------|
| A | **Test-Fixtures mit Session-Scoped-Reset** (conftest.py: autouse-fixture resettet `_UTR`, Timeout, Event-Store vor/nach jedem Test) | Test-only (kein Produktionscode) | S | ✅ **Empfohlen** — minimal-invasiv, kein Refactoring |
| B | Dependency Injection (Kontext-Objekt statt Globals) | Produktions-Refactoring | L | Risiko: Core-Interfaces (`tools.py` ist CORE, IMMUTABLE) → erfordert OVERRIDE-Pfad |
| C | DI-Container (dienstbasiert) | neues Framework | L | Overkill für aktuellen Stand; Architektur-Roadmap (MUSCAL 2.0) offen |
| D | Status quo + erweiterte Dokumentation | keine | S | Flakiness bleibt; Recalibrierungs-Risiko bleibt |

## 4. Empfehlung

**Option A (Test-Fixtures) + ADR-Dokumentation (dieser Entwurf):**
1. `tests/conftest.py` erhält Session-Scoped-Fixures, die `_UTR`/Timeout/Event-Store
   zwischen Test-Modulen zurücksetzen (Test-only; `tests/` ist nicht CORE).
2. Singletons im Produktionscode bleiben UNVERÄNDERT (Core-Immutabilität, D-006/D-020).
3. Langfristig (MUSCAL 2.0, ADR-022) werden Globals durch DI ersetzt — diese
   Entscheidung wird in diesem DRAFT vorbereitet, aber NICHT heute gefällt.

## 5. ADR-042 Vorschlag (Textvorschlag für den künftigen Decision Record)

```
# ADR-042: Global-State Policy — Test-Isolation statt Produktions-Refactoring

**Status:** PROPOSED (Entwurf)
**Date:** 2026-08-01

## Context
Modulglobale Singletons (_UTR, default_timeout, Event-Store-Pfad) verursachen
19 order-dependent Test-Failures (FL-01a). Produktionsseitiges Refactoring
kollidiert mit der Core-Immutabilität (ADR-007/D-020).

## Decision
- P1: Test-Fixtures (Session-Scoped-Reset in conftest.py) — Test-only.
- P2: Singletons bleiben bis MUSCAL 2.0 (ADR-022-Entscheidung) unverändert.
- P3: Bei künftigem DI-Refactoring greift der OVERRIDE-Pfad (ADRs/OVERRIDE.md).

## Compliance Check
- 19 FL-01a-Tests grün in Gesamt-Suite (Reihenfolge-unabhängig).
- Keine Core-Datei modifiziert.
```

**Offene Punkte vor Akzeptierung:** (1) ARB-Review des Fixture-Ansatzes,
(2) Zustimmung zum Verzicht auf Produktions-Refactoring bis MUSCAL 2.0,
(3) Freigabe Test-only-Commit.

---

*DRAFT erstellt im Decision-Closure-Mandat (RC-3). Keine Akzeptierung ohne Human/ARB-Approval (Auftrag: „Keine ADR-Akzeptierung ohne Human Approval").*
