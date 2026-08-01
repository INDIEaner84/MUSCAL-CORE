# ADR_REVIEW_MATRIX — ADR-022…025 Review-Vorbereitung

**Gate:** G7-03 · **Date:** 2026-08-01 · **Modus:** READ/WRITE (docs/audit/)
**Zweck:** Prüfmatrix für die ARB-Review-Runde (RC-4a) — **keine Statusänderung**; alle ADRs bleiben PROPOSED (DRAFT).
**Referenz:** G6_01_ADR_CLOSURE_PREPARATION.md, DECISION_CLOSURE_PACKAGE §RC-4, spec/ADR-022…025, ADR-INDEX.md

---

## Übersicht

| ADR | Vollständigkeit (6/6) | Offene Fragen | Abhängigkeiten | Konflikte mit Architektur | Review-Status |
|-----|------------------------|---------------|----------------|---------------------------|---------------|
| ADR-022 MUSCAL 2.0 Hybrid | ✅ | 3 (in-Datei) + 6 (G6-01-Kategorien) | ADR-001 (Kernel), ADR-005 (Pipeline), ADR-006 (Graph), D-030 (E3.6-Roadmap) | **D-010 vs D-001** (Migrationspfad, MEDIUM); ADR-001 APPLIED vs Hybrid-Multi-Agent | NICHT GESTARTET |
| ADR-023 Cognitive Kernel | ✅ | 3 + 6 | ADR-014 (UTR), ADR-008 (Deployment), ADR-EVENT-001 (EventStore Boundary) | MC-TC-007-Trust-Governance-NO-GO (Governance↔EventStore-Disconnect) | NICHT GESTARTET |
| ADR-024 Agent P1–P5 | ✅ | 3 + 6 | ADR-021 (Agent Detection), ADR-022 (Multi-Agent), ADR-001 (Pipeline) | **P5 Human Sovereignty** vs ApprovalManager-Auto-Approve (MC-TC-007-NO-GO); P3 vs RuntimeObservability-ZERO-Caller-Finding | NICHT GESTARTET |
| ADR-025 Cognitive Compiler | ✅ | 3 + 6 | ADR-001 (Compiler-Pipeline im Kernel), MPIR/MREIL (M-0.6 §17, Referenz), ADR-022 (Compiler im Hybrid-Kontext) | **D-013 vs D-014** (Scope-Abgrenzung, LOW); ADR-001-Pipeline vs neuer Compiler-Pfad (nur Design-Abgleich) | NICHT GESTARTET |

## Detail-Offene Fragen (je ADR — aus Datei + G6-01)

| ADR | Datei-OQ | G6-01-Kategorien (fehlend) |
|-----|----------|-----------------------------|
| ADR-022 | Migrationspfad ADR-001→Hybrid?; Verhältnis ADR-023/024?; Turnier-Kriterien? | Akzeptanzkriterien, Owner, Zeitplan, Budget, Rückwärtskompatibilität, Review-Prozess |
| ADR-023 | Autorität vs ADR-014?; Edge-Scope?; Signierungs-Schema? | dito |
| ADR-024 | P1–P5-Autorisierung?; vs ADR-001?; Observability-Kriterien? | dito |
| ADR-025 | vs ADR-001-Pipeline?; RFC-Governance?; D-014-Abgrenzung? | dito |

## Abhängigkeits-Graph (für Review)

```
ADR-022 ─┬─> ADR-001 (Kernel)  ── entscheidet Pipeline-/Compiler-Fragen
         ├─> ADR-005 (Pipeline)
         └─> ADR-006 (Graph)
ADR-023 ──> ADR-014 (UTR) + ADR-EVENT-001 + ADR-008 (Edge-Deployment)
ADR-024 ──> ADR-021 (Agent Detection) + ADR-022 + ADR-007 (P5/Authority)
ADR-025 ──> ADR-001 (Compiler) + MPIR/MREIL-Referenz
Alle 4 ───> D-030 (E3.6-Meilenstein) + Trust-Governance-NO-GO (MC-TC-007, 30.07)
```

## Konflikt-Bewertung (für Review)

| Konflikt | Severity | Anmerkung |
|----------|----------|-----------|
| D-010 vs D-001 (ADR-022) | MEDIUM | Kernfrage des Reviews: Migrationspfad oder Koexistenz |
| ADR-023 vs Trust-Governance-NO-GO | MEDIUM | Cognitive-Kernel-Anspruch (signed actions) kollidiert mit fehlender Governance-Persistenz |
| P5 vs Auto-Approve (ADR-024) | MEDIUM | erfordert Klarstellung: gilt P5 für MUSCAL-2.0-Agenten oder auch heute? |
| D-013 vs D-014 (ADR-025) | LOW | Abgrenzung RFC vs Compiler — Review bestätigt oder verfeinert |

## Review-Protokoll (für RC-4a)

1. ARB beantwortet je ADR die Datei-OQs (3) + nimmt G6-01-Kategorien als Template-Anforderungen an.
2. Konflikt-Urteile je Zeile (bestätigen / verwerfen / ergänzen).
3. **Ergebnis → Status-Empfehlung** (PROPOSED-final / DEPRECATED / ACCEPTED) — Entscheidung durch ARB/Human, nicht durch diesen Agenten.
4. Ergebnis-Protokoll in ADR_INDEX + ADR-Dateien (nur durch Review-Instanz).

---

*G7-03 erstellt — Prüfmatrix ohne Statusänderung; alle ADRs bleiben PROPOSED (DRAFT).*
