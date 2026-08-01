# ADR-023: Cognitive Kernel + Authoritative Runtime (Edge)

**Status:** PROPOSED (DRAFT — nicht akzeptiert, keine Umsetzung)
**Date:** 2026-08-01
**Source:** DECISION_REGISTRY D-011 (S2 `Cognitive Kernel Proposal`, 2026-07-25, chat-only, C2)
**Prepared by:** G4.5 Consolidation Agent (B2)

## Context

Ein Cognitive-Kernel-Vorschlag (25.07, Chat-basiert) beschreibt ein
Authoritative Runtime auf Edge-Hardware mit signed actions und verified
event store. Die Entscheidung existiert **nur im Chat**
(D-011: planned, chat-only).

## Decision

**PENDING — keine Entscheidung getroffen.** Dieser Entwurf dokumentiert den
Stand. Kernelemente des Vorschlags (D-011):

- Cognitive Kernel als Autorisierungs-Schicht.
- Authoritative Runtime auf Edge-Hardware.
- Signierte Aktionen (signed actions).
- Verifizierter Event Store (anschlussfähig an MC-TC-004/006-Zertifizierungen).

## Migration Plan

Unbestimmt — kein Code im Repo; Verhältnis zu ADR-014 (Unified Tool Runtime)
und ADR-EVENT-001 (EventStore Boundary) zu klären.

## Consequences

- Offen: Hardware-Anforderungen, Sicherheitsmodell, Verhältnis zu
  MC-TC-007-Trust-Governance-Findings (NO-GO: Governance nicht persistent).

## Compliance Check

- Kein Code-Anteil; reine Decision-Record-Dokumentation.
- Keine automatische Akzeptierung (Anforderung G4.5-B2).

## Open Questions

1. Autorität im Verhältnis zu ADR-014 (UToolRuntime) und Trust-Governance-NO-GO?
2. Edge-Scope: welche Laufzeit-Umgebung (vgl. ADR-008 Deployment)?
3. Signierungs-Schema und Schlüsselverwaltung — Design offen.
