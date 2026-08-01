# ADR-022: MUSCAL 2.0 Hybrid-Architektur (MC-015)

**Status:** PROPOSED (DRAFT — nicht akzeptiert, keine Umsetzung)
**Date:** 2026-08-01
**Source:** DECISION_REGISTRY D-010 (S2 `MUSCAL 2.0 Architektur-Turnier`, 2026-07-25, chat-only, C2)
**Prepared by:** G4.5 Consolidation Agent (B2)

## Context

Das MC-015-Architektur-Turnier (25.07, Chat-basiert) wählte eine Hybrid-Architektur
für MUSCAL 2.0: durable execution + hierarchisches Multi-Agenten-Modell +
event-driven verification. Die Entscheidung existiert **nur im Chat**
(D-010: planned, chat-only, no ADR) und ist im Repository nicht sichtbar.

Der aktuelle Stand ist ein Single-Agent-Kernel (D-001-Pfad, ADR-001 APPLIED).
Ein Migrationspfad zwischen D-010 und D-001 ist nicht definiert
(Registry §D: MEDIUM — migration path undefined).

## Decision

**PENDING — keine Entscheidung getroffen.** Dieser Entwurf dokumentiert den
Stand und die Optionen; eine Akzeptierung erfordert eine ARB/Governance-
Entscheidung mit Migrationsbewertung.

- Turnier-Sieger (D-010): Hybrid aus durable execution, hierarchischem
  Multi-Agenten-Modell, event-driven verification.
- Alternative: Fortführung des Single-Agent-Kernels (D-001-Pfad).

## Migration Plan

Unbestimmt — Migrationspfad ist Teil der offenen Fragen. Kein Code-Pfad
existiert für MUSCAL 2.0 im Repo.

## Consequences

- Offen: Scope, Zeitplan, Kompatibilität mit ADR-001/ADR-005/ADR-006.
- Konflikt D-010 vs D-001 bleibt bestehen, bis eine Entscheidung fällt.

## Compliance Check

- Kein Code-Anteil; reine Decision-Record-Dokumentation.
- Keine automatische Akzeptierung (Anforderung G4.5-B2).

## Open Questions

1. Migrationspfad von ADR-001 (Single-Pipeline) zu Hybrid — wer entscheidet?
2. Verhältnis zu ADR-024 (Agent-Architektur-Prinzipien) und ADR-023 (Cognitive Kernel)?
3. Treffer-Kriterien des Turniers dokumentieren (Quelle: S2-Chat 25.07, nicht im Repo).
