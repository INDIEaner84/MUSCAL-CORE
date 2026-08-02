# ADR-024: Agent-Architektur-Prinzipien P1–P5

**Status:** PROPOSED (DRAFT — nicht akzeptiert, keine Umsetzung)
**Date:** 2026-08-01
**Source:** DECISION_REGISTRY D-012 (S2 `MUSCAL Agent Architecture`, 2026-07-30, chat-only, C2)
**Prepared by:** G4.5 Consolidation Agent (B2)

## Context

Eine Agent-Architektur-Spezifikation (30.07, Chat-basiert, Spec-Draft)
definiert fünf Architektur-Prinzipien. Die Entscheidung existiert **nur im
Chat** (D-012: planned, spec draft chat-only).

## Decision

**PENDING — keine Entscheidung getroffen.** Prinzipien-Portfolio aus D-012:

| P | Prinzip | Kurzbedeutung |
|---|---------|---------------|
| P1 | **Modularity** | Agenten als austauschbare, gekapselte Module |
| P2 | **Specialization** | spezialisierte Agenten je Domäne/Kapazität |
| P3 | **Observability** | vollständig beobachtbare Agenten-Aktivität |
| P4 | **Replaceability** | jeder Agent ersetzbar ohne Systemeingriff |
| P5 | **Human Sovereignty** | menschliche Kontrolle bleibt letzte Instanz |

## Migration Plan

Unbestimmt — kein Code im Repo; Bezug zu ADR-021 (Agent Detection
Formalization) und ADR-022 (MUSCAL 2.0 Multi-Agent) zu klären.

## Consequences

- P5 (Human Sovereignty) kollidiert potenziell mit der in MC-TC-007
  Trust Governance festgestellten Auto-Approve-Struktur (ApprovalManager,
  features/tools/approval.py) — kein Konflikt im Code, aber Governance-Gap.

## Compliance Check

- Kein Code-Anteil; reine Decision-Record-Dokumentation.
- Keine automatische Akzeptierung (Anforderung G4.5-B2).

## Open Questions

1. Verbindliche Definition von P1–P5 — wer autorisiert?
2. Verhältnis zu ADR-001 (Single Pipeline Authority) — ersetzt oder erweitert?
3. Prüfverfahren für P3 (Observability) — anknüpfend an RuntimeObservability-ZERO-Caller-Finding (MC-TC-007)?
