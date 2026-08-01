# ADR-025: Cognitive Compiler — Prompts als deklarative kognitive Programme

**Status:** PROPOSED (DRAFT — nicht akzeptiert, keine Umsetzung)
**Date:** 2026-08-01
**Source:** DECISION_REGISTRY D-013 (S2 `MUSCAL Compiler Spezifikation`, 2026-07-30, chat-only, C2) + D-014 (S2 `formale Spezifikation`, 2026-07-29, chat-only, C2)
**Prepared by:** G4.5 Consolidation Agent (B2)

## Context

Zwei verwandte Chat-Entscheidungen existieren **nur im Chat**:

- **D-013** (30.07): Prompts als deklarative kognitive Programme
  (Cognitive Compiler v1.0) — implementierungsorientiert.
- **D-014** (29.07): Formale Spezifikation als RFC-Serie,
  implementierungsunabhängig (no code).

Registry §D: D-013 vs D-014 = LOW, unterschiedliche Scopes.

## Decision

**PENDING — keine Entscheidung getroffen.** Dieser Entwurf dokumentiert beide
Richtungen und ihre Abgrenzung:

- **Compiler-Vision (D-013):** Prompt → deklaratives Programm → ausführbar.
- **RFC-Serie (D-014):** formale, implementierungsunabhängige Spezifikationen.

**Abgrenzungsvorschlag (kein Beschluss):** D-014 (RFC) spezifiziert *was*
(kognitive Programme als Konzept), D-013 (Compiler) *wie* (Umsetzung);
D-014 hat Vorrang bei Konflikten (Spezifikation vor Implementierung).

## Migration Plan

Unbestimmt — kein Code im Repo. Anschlussfähigkeit an ADR-001 (Compiler-
Pipeline im Kernel) und MPIR-Compiler-Pipeline (M-0.6 §17) zu prüfen.

## Consequences

- Offen: Verhältnis des Cognitive Compiler zur bestehenden
  Kernel-Compiler-Pipeline (ADR-001 APPLIED).
- Offen: RFC-Serien-Governance (Nummerierung, Autoritätsstufe).

## Compliance Check

- Kein Code-Anteil; reine Decision-Record-Dokumentation.
- Keine automatische Akzeptierung (Anforderung G4.5-B2).

## Open Questions

1. Ist der Cognitive Compiler eine Erweiterung von ADR-001 oder eine neue Pipeline?
2. RFC-Serie: Zuständigkeit, Format, Veröffentlichungsprozess?
3. D-014-Abgrenzung: bestätigen oder verwerfen?
