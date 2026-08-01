# MUSCAL Architecture Decision Records — Kanonische Übersicht

> **G4.5 B1 (2026-08-01):** Kanonische Konsolidierung — ADR-014 Status korrigiert
> (PROPOSED → ACCEPTED, Datei-Stand 01.08), 5 bislang nicht-gelistete ADRs
> (API/EVENT/RUNTIME-001, ADR-020, ADR-021) aufgenommen, ADR-022…025 als
> DRAFT/PROPOSED registriert. Keine ADR gelöscht; alle bestehenden Zeilen erhalten.
> Referenz: `docs/audit/ADR_CANONICAL_MAP.md` (F-01…F-05).

## Status Definitions

- **DRAFT** — Entwurf, Entscheidung ausstehend (keine Autorität)
- **PROPOSED** — Vorgeschlagen, noch nicht umgesetzt
- **ACCEPTED** — Akzeptiert, Umsetzung begonnen
- **APPLIED** — Umsetzung abgeschlossen
- **DEPRECATED** — Nicht mehr gültig
- **SUPERSEDED** — Durch neueres ADR ersetzt

## Kanonische Tabelle (ADR-ID | Standort | Status | Autorität | Supersession | Konflikte)

| ID | Standort | Titel | Status | Autorität | Supersession | Konflikte |
|----|----------|-------|--------|-----------|--------------|-----------|
| ADR-001 | `spec/ADR-001-kernel.md` | Kernel Runtime — Single Pipeline Authority | APPLIED | kanonisch | — | — |
| ADR-002 | `spec/ADR-002-memory.md` | Memory — GraphMemory als Standard-Interface | ACCEPTED (Ph1-4 ✅) | kanonisch | — | — |
| ADR-003 | `spec/ADR-003-events.md` | Event System — EventBus als Standard | APPLIED | kanonisch | — | — |
| ADR-004 | `spec/ADR-004-plugins.md` | Plugin System — Hook-Based Extensions | ACCEPTED | kanonisch | — | — |
| ADR-005 | `spec/ADR-005-pipeline.md` | Pipeline Architecture — Monolithic Data Flow | ACCEPTED | kanonisch | — | — |
| ADR-006 | `spec/ADR-006-graph.md` | Graph/Sphere — Event-Driven Execution Graph | ACCEPTED | kanonisch | — | — |
| ADR-007 | `spec/ADR-007-immutability.md` | Core Immutability — Write Guard Policy | ACCEPTED | kanonisch (Write Guard Policy) | — | — |
| ADR-008 | `spec/ADR-008-deployment.md` | Deployment Runtime — Supervisor Container Model | ACCEPTED | kanonisch | — | — |
| ADR-009 | `spec/ADR-009-observability.md` | Observability Foundation | ACCEPTED | kanonisch | — | — |
| ADR-010 | `spec/ADR-010-sqlite.md` | SQLite Consolidation — Unified Single Database | APPLIED | kanonisch | — | — |
| ADR-011 | `spec/ADR-011-verification.md` | Verification Layer Architecture | ACCEPTED | kanonisch | — | — |
| ADR-012 | `spec/ADR-012-event-persistence.md` | Event Persistence — Audit Log + Replay | APPLIED | kanonisch | — | — |
| ADR-013 | `spec/ADR-013-pipeline.md` | Feature Plugin Migration Path (historisch, fehlbezeichnet) | **SUPERSEDED** | historisch | superseded by ADR-007 | ADR-007-Identitäts-Duplikat (behoben, d5f5ce7) |
| ADR-014 | `spec/ADR-014-tool-runtime.md` | Unified Tool Runtime | **ACCEPTED** (Datei-Stand 01.08; zuvor INDEX-Fehleintrag PROPOSED 15.07 — F-01) | kanonisch | — | historisch: PROPOSED vs modifizierte Datei (D-018, G2 RESOLVED) |
| ADR-API-001 | `spec/ADRs/ADR-API-001-dual-runtime.md` | Dual Runtime API | aktiv | erweitert ADR-014 | — | Standort außerhalb `spec/ADR-*.md`-Schema (F-02, aufgenommen) |
| ADR-EVENT-001 | `spec/ADRs/ADR-EVENT-001-eventstore-boundary.md` | EventStore Boundary | aktiv | erweitert ADR-010/ADR-012 | — | Standort außerhalb Schema (F-02, aufgenommen); Registry-§E-Gap adressiert |
| ADR-RUNTIME-001 | `spec/ADRs/ADR-RUNTIME-001-supl-ownership.md` | SUPL Ownership | aktiv | erweitert ADR-014 | — | Standort außerhalb Schema (F-02, aufgenommen) |
| ADR-020 | `docs/engineering/ADR-020-PIPELINE-STAGES-ADOPTION.md` | Pipeline Stages Adoption | aktiv | erweitert ADR-005 | — | außerhalb `spec/` (F-02, aufgenommen) |
| ADR-021 | `docs/engineering/ADR-021-AGENT-DETECTION-FORMALIZATION.md` | Agent Detection Formalization | aktiv | erweitert ADR-001/ADR-006 | — | außerhalb `spec/` (F-02, aufgenommen) |
| ADR-022 | `spec/ADR-022-muscal2-hybrid.md` | MUSCAL 2.0 Hybrid-Architektur (MC-015) | **DRAFT/PROPOSED** | keine (Entwurf) | — | D-010 vs D-001 Migrationspfad (Registry §D, MEDIUM) |
| ADR-023 | `spec/ADR-023-cognitive-kernel.md` | Cognitive Kernel + Authoritative Runtime (Edge) | **DRAFT/PROPOSED** | keine (Entwurf) | — | — |
| ADR-024 | `spec/ADR-024-agent-architecture.md` | Agent-Architektur-Prinzipien P1–P5 | **DRAFT/PROPOSED** | keine (Entwurf) | — | — |
| ADR-025 | `spec/ADR-025-cognitive-compiler.md` | Cognitive Compiler (Prompts als Programme) + RFC-Serie | **DRAFT/PROPOSED** | keine (Entwurf) | — | D-013 vs D-014 Scope-Abgrenzung (LOW) |

## Plan-Dokumente (keine ADRs)

| ID | Standort | Status | Hinweis |
|----|----------|--------|---------|
| ADR-014-IMPLEMENTATION_PLAN_v1.0 | `docs/governance/ADR-014-IMPLEMENTATION_PLAN_v1.0.md` | superseded | durch v1.1 abgelöst |
| ADR-014-IMPLEMENTATION_PLAN_v1.1 | `docs/governance/ADR-014-IMPLEMENTATION_PLAN_v1.1.md` | aktiv | gültiger Umsetzungsplan |

## Historische ADRs (Referenz, keine Autorität)

| ID | Standort | Hinweis |
|----|----------|---------|
| ADR-001…006 | `archive/history/adrs/ADR-001..006.md` | Vorversionen der kanonischen ADR-001…006; Autorität nach D-025 bei den kanonischen Dateien |

## Template

Neue ADRs folgen dem Format:

```markdown
# ADR-NNN: Titel

**Status:** PROPOSED  
**Date:** YYYY-MM-DD  

## Context
## Decision
## Migration Plan
## Consequences
## Compliance Check
```
