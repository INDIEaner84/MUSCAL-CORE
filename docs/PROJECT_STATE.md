# MUSCAL CORE — Project State

**Letzte Aktualisierung:** 2026-08-07 (Reality Synchronization Layer — `features/reality_sync/`)
**Nächste Aktualisierung:** Bei nächstem Meilenstein

---

## Notable Additions (2026-08-07)

- **Reality Synchronization Layer (RSL)** implementiert in `features/reality_sync/`
  (DriftDetector, RiskClassifier, ProposalEngine, RealitySynchronizer, Modelle, Validator).
  Reine Proposal-Pipeline — kein automatischer Write auf EventStore/Canonical.
  - Tests: `tests/features/reality_sync/test_reality_sync.py` — **11/11 PASS**
  - Regression: 24 relevante Event-/Knowledge-Tests PASS
  - Doku: `docs/reality_sync/` (ANALYSIS, ARCHITECTURE, IMPLEMENTATION_REPORT, VALIDATION_REPORT, RSL_COMPLETE)

## Project Phase

Prototype Stable

## Status

READY WITH RISKS

## Audit-Status (Stand 2026-08-01)

| Audit | Status | Datum | Hinweis |
|-------|--------|-------|---------|
| MC-TC-004 (EventStore Trust Boundary) | **CERTIFIED** | 2026-07-30 | ARB Decision in `docs/audit/MC-TC-004_ARB_DECISION.md` |
| MC-TC-006 (Replay deterministisch) | CERTIFIED | 2026-07-27 | `docs/audit/MC-TC-006-*` |
| MC-TC-007 (Reality Closure) | **CONDITIONAL GO** | 2026-07-31 | 2 P0 Blocker offen — siehe §P0 Blocker |
| MC-TC-005 (Verification Layer) | NOT AUTHORIZED | — | nur Vorarbeiten existieren |

Details: `docs/audit/` (55 Artefakte, MC-TC-002…007, GRAPH_OS-Freeze v1.0).
**Neueste Projektwahrheit ab 2026-07-27 liegt in `docs/audit/` — nicht mehr allein in diesem Dokument.**

## Last Validated

2026-07-20

## Stress Test

PASS (100 Iterationen, 0 Crashes, deterministisch)

## Testergebnis (2026-07-20)

- **547/547 passed (100%)**, 1 skipped, 0 failed, 0 errors
- P0/P1 Gaps: ✅ VOLLSTÄNDIG GESCHLOSSEN
- Letzter Checkpoint: 0.32 (P1 Gaps Closed)
- ⚠️ Zahlen vom 2026-07-20; Neu-Verifikation nach Audit-Wave ausstehend (Audit-Finding TF-06 — Testzahlen-Kontradiktion).

## P0 Blocker (offen, seit MC-TC-007 2026-07-31)

| # | Blocker | Status | Adressat |
|---|---------|--------|----------|
| P0-1 | Graph-OS-State (GraphState/SphereState) ist nur in-memory — nach Restart nicht rekonstruierbar | OFFEN — Entscheidung ausstehend | Phase A Remediation PA-08 (Entscheidung) |
| P0-2 | Watchdog-Events werden nicht in EventStore persistiert | OFFEN — Entscheidung ausstehend | Phase A Remediation PA-09 (Entscheidung) |

## Prototype

APPROVED

## Architecture

IMMUTABLE (laut `spec/IMMUTABILITY_CONTRACT.md`)

## Verbleibende Technical Debt

| # | Item | Severity | ADR |
|---|------|----------|-----|
| 1 | — (alle 28 Stubs in `archive/stubs/` gelöscht) | — | ADR-001 |
| 2 | Parallel-Kernel (kernel.py vs kernel_core.py, kernel_core.py gelöscht) | Resolved | ADR-001 |
| 3 | Plugin-System nur Hook-basiert (keine Pipeline-Composition) | Medium | ADR-004 |
| 4 | SIGNAL_RULES Confidence-Drift ohne Auto-Reset | Medium | — |
| 5 | FIFO-Eviction ohne semantische Bewertung | Low | — |
| 6 | DB-Migration via `scripts/migrate_sqlite.py` | Low | ADR-010 |
| 7 | CI/CD via `.github/workflows/test.yml` | Low | ADR-008 |
| 8 | — (Event-Persistence via ADR-012) | Resolved | ADR-012 |

## Phase abgeschlossen: Critical-Path Tests (18/18)

Folgende ADRs wurden erstellt/aktualisiert:

| ADR | Titel | Status |
|-----|-------|--------|
| ADR-001 | Kernel Runtime — Single Pipeline Authority | APPLIED |
| ADR-002 | Memory — GraphMemory als Standard-Interface | ACCEPTED (Ph1-4 ✅) |
| ADR-003 | Event System — EventBus als Standard | APPLIED |
| ADR-004 | Plugin System — Hook-Based Extensions | ACCEPTED |
| ADR-005 | Pipeline Architecture — Monolithic Data Flow | ACCEPTED |
| ADR-006 | Graph/Sphere — Event-Driven Execution Graph | ACCEPTED |
| ADR-007 | Core Immutability — Write Guard Policy | ACCEPTED |
| ADR-008 | Deployment Runtime — Supervisor Container Model | ACCEPTED |
| ADR-009 | Observability Foundation | ACCEPTED |
| ADR-010 | SQLite Consolidation — Unified Single Database | APPLIED |
| ADR-011 | Verification Layer Architecture | ACCEPTED |
| ADR-012 | Event Persistence — Audit Log + Replay | APPLIED |
| ADR-014 | Unified Tool Runtime — Consolidation | PROPOSED |

## Current Branch

prototype-stable

## Baseline Version

1.0.0

---

## Verbindliche Dokumente

| Dokument | Pfad | Zweck |
|----------|------|-------|
| TECHNICAL BASELINE | `docs/TECHNICAL_BASELINE.md` | Verbindliche Architektur |
| ARCHITECTURE.md | `docs/ARCHITECTURE.md` | Übersicht + Layering |
| ADRs | `spec/ADR-*.md` | Architecture Decision Records |
| AUDIT-WAVE | `docs/audit/` | Zertifizierungen MC-TC-002…007 (neueste Wahrheit ab 27.07) |
| IMMUTABILITY CONTRACT | `spec/IMMUTABILITY_CONTRACT.md` | Core/Feature-Grenzen |
| PLUGIN_API.md | `spec/PLUGIN_API.md` | Plugin SDK |

## Governance Status

| Decision | Status | Blocking |
|----------|--------|----------|
| HDR-001 (Architecture Council) | READY FOR HUMAN DECISION | Yes — 9 dependencies |
| HDR-002 (PMGA) | BLOCKED by HDR-001 | Yes |
| HDR-003 (Master Coding AI) | BLOCKED by HDR-001 | Yes |
| HDR-004 (Requirements) | BLOCKED by HDR-001 | Yes |

## G2 Adjudication Status (2026-08-01)

| Item | Status | Evidence |
|------|--------|----------|
| Immutability review (29 Dateien) | **ADJUDIZIERT** — 22 committet (Cluster C1–C4), 6 Swept retroaktiv sanktioniert, 0 Reverts | DECISION_REGISTRY D-036…D-039, G2_ADJUDICATION_REPORT.md |
| OVERRIDE.md | **REKONSTRUIERT** — Baseline-Registry (OVERRIDE-020…055) + Phase-1A-Wave + Wahrheitskorrektur; OVERRIDE-052-Mechanismus wieder aktiv | spec/OVERRIDE.md (1.541 Zeilen) |
| ADR-014 (Unified Tool Runtime) | **FINALISIERT** — Status ACCEPTED, Governance-Links (D-E3.0.2-006, D-E3.2-002) | spec/ADR-014-tool-runtime.md |
| FL-01a (19 flaky Tests) | **DOKUMENTIERT, NICHT GEFIXT** — Root Cause: globale Singletons (`tools._UTR`, `set_global_utr`, `set_global_event_store`); Fix (Test-Fixtures) in Phase B | G2_ADJUDICATION_REPORT.md FL-01a, D-040 |
| FL-01b (4 Baseline-Tests) | **KALIBRIERT** — EXPECTED_TOTAL an verifizierte Counts angepasst (test-only) | D-041 |
| Git-Zustand | 22 verbleibende modifizierte Dateien **committet**; Repo wieder sauber | git status, G2 execution commits |

**Konsequenz:** Die D-006/D-022-Verletzung („Core immutable" vs 29 modifizierte Dateien) ist mit
Ausnahme der Test-Flakiness (D-040) **geschlossen**; `Architecture: IMMUTABLE` gilt ab jetzt wieder
mit korrigiertem OVERRIDE-Register.

## Historische Audits

Historische Analysen dienen ausschließlich als Referenz.
Sie dürfen NICHT als aktueller Projektzustand interpretiert werden.

Falls Aussagen historischen Dokumenten widersprechen,
haben immer die Baseline-Dokumente Vorrang.
