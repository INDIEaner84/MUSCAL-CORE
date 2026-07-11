# MUSCAL CORE — Project State

**Letzte Aktualisierung:** 2026-07-11
**Nächste Aktualisierung:** Bei nächstem Meilenstein

---

## Project Phase

Prototype Stable

## Status

READY WITH RISKS

## Last Validated

2026-07-11

## Stress Test

PASS (100 Iterationen, 0 Crashes, deterministisch)

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
| 8 | Kein Event-Persistence-ADR | Low | — |

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
| ADRs | `specs/adrs/*` | Architecture Decision Records |
| IMMUTABILITY CONTRACT | `spec/IMMUTABILITY_CONTRACT.md` | Core/Feature-Grenzen |
| PLUGIN_API.md | `spec/PLUGIN_API.md` | Plugin SDK |

## Historische Audits

Historische Analysen dienen ausschließlich als Referenz.
Sie dürfen NICHT als aktueller Projektzustand interpretiert werden.

Falls Aussagen historischen Dokumenten widersprechen,
haben immer die Baseline-Dokumente Vorrang.
