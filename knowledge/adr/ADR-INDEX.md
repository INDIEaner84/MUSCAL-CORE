# MUSCAL Architecture Decision Records — Kanonische Übersicht

**Version:** v2.0 (M3, 2026-08-02) · **Migration:** MUSCAL-KNOWLEDGE-MIGRATION-001
**Kanonische Ablage:** `knowledge/adr/` (M3-Konsolidierung)
**Referenz:** ADR_CANONICAL_MAP (docs/audit, F-01…F-05), KNOWLEDGE_CONSOLIDATION_PLAN.md §2.3
> **Hinweis:** Dieser Index wird ab M4 aus dem YAML-Frontmatter der ADRs generiert (keine Handpflege mehr; F-01-Schutz). Vorläufig manuell gepflegt.

## Status Definitions

- **DRAFT** — Entwurf, Entscheidung ausstehend (keine Autorität)
- **PROPOSED** — Vorgeschlagen, noch nicht umgesetzt
- **ACCEPTED** — Akzeptiert, Umsetzung begonnen
- **APPLIED** — Umsetzung abgeschlossen
- **DEPRECATED** — Nicht mehr gültig
- **SUPERSEDED** — Durch neueres ADR ersetzt

## Kanonische Tabelle (ADR-ID | Standort | Status | Autorität | Supersession | Konflikte)

| ID | Standort (knowledge/adr/) | Titel | Status | Autorität | Supersession | Konflikte |
|----|---------------------------|-------|--------|-----------|--------------|-----------|
| ADR-001 | `ADR-001-kernel.md` | Kernel Runtime — Single Pipeline Authority | APPLIED | kanonisch | — | — |
| ADR-002 | `ADR-002-memory.md` | Memory — GraphMemory als Standard-Interface | ACCEPTED (Ph1-4 ✅) | kanonisch | — | — |
| ADR-003 | `ADR-003-events.md` | Event System — EventBus als Standard | APPLIED | kanonisch | — | — |
| ADR-004 | `ADR-004-plugins.md` | Plugin System — Hook-Based Extensions | ACCEPTED | kanonisch | — | — |
| ADR-005 | `ADR-005-pipeline.md` | Pipeline Architecture — Monolithic Data Flow | ACCEPTED | kanonisch | — | — |
| ADR-006 | `ADR-006-graph.md` | Graph/Sphere — Event-Driven Execution Graph | ACCEPTED | kanonisch | — | — |
| ADR-007 | `ADR-007-immutability.md` | Core Immutability — Write Guard Policy | ACCEPTED | kanonisch (Write Guard Policy) | — | — |
| ADR-008 | `ADR-008-deployment.md` | Deployment Runtime — Supervisor Container Model | ACCEPTED | kanonisch | — | — |
| ADR-009 | `ADR-009-observability.md` | Observability Foundation | ACCEPTED | kanonisch | — | — |
| ADR-010 | `ADR-010-sqlite.md` | SQLite Consolidation — Unified Single Database | APPLIED | kanonisch | — | — |
| ADR-011 | `ADR-011-verification.md` | Verification Layer Architecture | ACCEPTED | kanonisch | — | — |
| ADR-012 | `ADR-012-event-persistence.md` | Event Persistence — Audit Log + Replay | APPLIED | kanonisch | — | — |
| ADR-013 | `ADR-013-pipeline.md` | Feature Plugin Migration Path (historisch, fehlbezeichnet) | **SUPERSEDED** | historisch | superseded by ADR-007 | ADR-007-Identitäts-Duplikat (behoben, d5f5ce7) |
| ADR-014 | `ADR-014-tool-runtime.md` | Unified Tool Runtime | **ACCEPTED** (Datei-Stand 01.08) | kanonisch | — | historisch: PROPOSED vs Datei (D-018, G2 RESOLVED) |
| ADR-API-001 | `ADR-API-001-dual-runtime.md` | Dual Runtime API | aktiv | erweitert ADR-014 | — | — |
| ADR-EVENT-001 | `ADR-EVENT-001-eventstore-boundary.md` | EventStore Boundary | aktiv | erweitert ADR-010/ADR-012 | — | — |
| ADR-RUNTIME-001 | `ADR-RUNTIME-001-supl-ownership.md` | SUPL Ownership | aktiv | erweitert ADR-014 | — | — |
| ADR-020 | `ADR-020-PIPELINE-STAGES-ADOPTION.md` | Pipeline Stages Adoption | aktiv | erweitert ADR-005 | — | — |
| ADR-021 | `ADR-021-AGENT-DETECTION-FORMALIZATION.md` | Agent Detection Formalization | aktiv | erweitert ADR-001/ADR-006 | — | — |
| ADR-022 | `ADR-022-muscal2-hybrid.md` | MUSCAL 2.0 Hybrid-Architektur (MC-015) | **DRAFT/PROPOSED** | keine (Entwurf) | — | D-010 vs D-001 (Registry §D, MEDIUM) |
| ADR-023 | `ADR-023-cognitive-kernel.md` | Cognitive Kernel + Authoritative Runtime (Edge) | **DRAFT/PROPOSED** | keine (Entwurf) | — | — |
| ADR-024 | `ADR-024-agent-architecture.md` | Agent-Architektur-Prinzipien P1–P5 | **DRAFT/PROPOSED** | keine (Entwurf) | — | — |
| ADR-025 | `ADR-025-cognitive-compiler.md` | Cognitive Compiler (Prompts als Programme) + RFC-Serie | **DRAFT/PROPOSED** | keine (Entwurf) | — | D-013 vs D-014 (LOW) |

## Audit-Kontext-ADRs (NICHT kanonisch — Nummernkollision)

| ID | Standort | Hinweis |
|----|----------|---------|
| MC-TC-003A ADR-011…016 | `docs/audit/MC-TC-003A_ADR_PACKAGE.md` | Audit-eigene Serie (Trust Core: Authoritative Event Store, Canonical Execution Identity, Orthogonal Execution Mode, Unified Verification, Evidence vs Claim, Identity Generation). **M3-Entscheidung:** NICHT in die kanonische Serie übernommen; bleiben kontextualisierte Audit-Artefakte (kein Nummern-Reuse). |

## Historische ADRs (Referenz, keine Autorität)

| ID | Standort | Hinweis |
|----|----------|---------|
| ADR-001…006 | `archive/history/adrs/ADR-001..006.md` | Vorversionen der kanonischen ADR-001…006; Autorität nach D-025 bei den kanonischen Dateien (ARCHIVED). |

## Deprecated

| Element | Standort | Ersetzt durch |
|---------|----------|---------------|
| `specs/adrs/IMPLEMENTATION_STATUS.md` | specs/adrs/ (M3-DEPRECATED) | `knowledge/adr/ADR-INDEX.md` |
| `specs/templates/RFC_TEMPLATE.md` | specs/templates/ | `knowledge/adr/ADR_TEMPLATE.md` |
| `spec/ADR-*.md` (Altorte) | spec/, spec/ADRs/, docs/engineering/ | Redirect-Stubs auf `knowledge/adr/` (bis Gate M6) |

## Template

Neue ADRs: `knowledge/adr/ADR_TEMPLATE.md` (Felder: id, title, status, date, owner, decision_ids, affected_modules, dependencies, supersedes, superseded_by, review_status, confidence, provenance).
