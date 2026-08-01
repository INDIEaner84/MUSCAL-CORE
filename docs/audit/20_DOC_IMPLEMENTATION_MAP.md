# 20_DOC_IMPLEMENTATION_MAP — Dokumentenplan

**Gate:** KF-01 · **Date:** 2026-08-01 · **Modus:** Struktur & Mapping (keine Volltexte)
**Referenz:** KNOWLEDGE_FOUNDATION_CHARTER.md (Statusklassen, Confidence), PB-05-Mapping (Doc 00–12), KNOWLEDGE_FOUNDATION_GATE (G7-04)

**Priorität:** P1 = sofort baubar · P2 = nach Review/Entscheidung · P3 = nachgelagert

---

## Dokumente 00–19

| Doc | Ziel | Quellen | vorhandene Audit-Artefakte | fehlende Informationen | Abhängigkeiten | Priorität |
|-----|------|---------|---------------------------|------------------------|----------------|-----------|
| **00** Master Index & Governance-Übersicht | Navigations-/Verantwortungs-Karte der Foundation | G2…G7-Reports, PB-05 | MASTER_INDEX.md, G2_EXECUTION_VALIDATION_REPORT, G5, G6-RECHECK | finale Metrik-Werte nach SB-1/2 | alle Docs | P1 |
| **01** Audit Scope & Methodik | Methodik, Confidence-Modell, Layers | AUDIT_SCOPE.md | AUDIT_SCOPE.md (vollständig) | — | — | P1 |
| **02** Repository Index & Census | Zahlen-Inventar (Census) | Census, G6-02-Scope | REPOSITORY_CENSUS.md (vollständig) | Bridge-Artefakt-Governance (104) | — | P1 |
| **03** Source-of-Truth Map | Autoritäten je Domäne | SESSION_RULES v2.0, Authority-Map | SOURCE_OF_TRUTH_MAP.md | M3-Stale-Docs (BASELINE/ARCHITECTURE-Update optional) | KF-Charter | P1 |
| **04** Knowledge Graph | Node/Edge-Referenz | REFERENCE_GRAPH.md | REFERENCE_GRAPH.md (~120 Knoten) | neue Knoten (SESSION_RULES v2.0, ADR-022…25, Handovers) | Doc 13, KF-02 | P2 |
| **05** Decision Registry (konsolidiert) | alle Entscheidungen D-001…042 + Statusklassen | DECISION_REGISTRY, PB-02, G6-04 | DECISION_REGISTRY.md, PB02-Consolidation, G6_04 | D-033…035-Plan-Docs (RC-5) | Doc 16 | P1 |
| **06** Chat-Code-Doc Reconciliation | Chat-Claims ↔ Repo-Abgleich | CHAT_CODE_DOC_RECONCILIATION | CHAT_CODE_DOC_RECONCILIATION.md (43 Chats, 20 Claims) | S2-Primärquellen (nicht im Repo) | — | P1 |
| **07** Manual Conflict & Authority | 3-Wege-Konflikt + Autoritätsbereiche | TC-Report, B3/B4-Artefakte | TECHNICAL_MANUAL_CONFLICT_REPORT, AUTHORITY_MAP, RECONCILIATION_FINAL | v0.8-Erzeugung (Phase C) | Doc 14 | P1 |
| **08** Remediation & Gate-Historie | Phase A→G7-Verlauf | PHASE_A_RESULT, G2…G7-Artefakte | alle G2–G7-Files (vollständig) | — | Doc 00 | P1 |
| **09** Session Continuity & Handover | Continuity-Status, 17 Handovers | SESSION_REGISTRY, Handover-Dir | SESSION_CONTINUITY_AUDIT, G3-Plan §1 | S-07-31-Detail (UNKNOWN bleibt) | — | P1 |
| **10** Test Governance & Baseline | Suite-Zustand, FL-01a/b, Baseline 470 | FL01A-Register, Reconciliation-Test | FL01A_FLAKINESS_REGISTER, PB-02 (D-040/41) | FL-01a-Fixture-Fix-Entscheidung (RC-3/D-042) | Doc 16 | P1 |
| **11** Temporal Analysis | Konzept-Evolution über Zeit | CONCEPT_EVOLUTION_MAP | CONCEPT_EVOLUTION_MAP.md (vollständig) | — | — | P1 |
| **12** Governance Ops | WORK_QUEUE/ACTIVE_TASKS/Overrides | docs/governance/, OVERRIDE.md | OVERRIDE.md (rekonstruiert), G6-Artefakte | TASK_BOARD-Sync, Bridge-Governance | Doc 00 | P2 |
| **13** ADR-Index & Supersession-Karte | kanonische ADR-Übersicht | ADR_CANONICAL_MAP, ADR-INDEX | ADR_CANONICAL_MAP.md, ADR-INDEX (B1), ADR-022…25-DATEIEN | RC-4a-Review-Ergebnis | Doc 05 | P1 |
| **14** Architektur-Landkarte (implementiert) | L0–L6 nur implementierte Systeme | v0.8-Scope (G6-02), ADRs | G6-02-Scope, ADR-001…014 | v0.8-Manual (nicht nötig für Map — Census reicht) | Doc 07 | P2 |
| **15** Zertifizierungs-Register | MC-TC-002…007 + P0-Status | docs/audit/MC-TC-*, PROJECT_STATE | 55 In-Repo-Cert-Docs, G5-Report | **P0-1/P0-2-Entscheidung (RC-1)** | Doc 16 | P2 |
| **16** Blocker- & Entscheidungs-Register | alle offenen Blocker mit Owner | DECISION_CLOSURE_PACKAGE, G7-01/02 | G7_01-Briefs, HDR-001-RECORD, G5 §3 | **RC-1/RC-2-Entscheidungen** | — | P2 |
| **17** Bridge-/Artefakt-Governance | handover_*.md|yaml-Klassifikation | docs/bridge/handovers/ | (Laufzeit-Artefakte, nicht committet) | Governance-Beschluss (M1-Rest) | P3 |
| **18** Metrik-Register | M1–M5-Formeln + Verlauf | MASTER_INDEX, G4/G5/G6-Messungen | G4_MEASUREMENT, G5_FINAL, G6_RECHECK (vollständig) | Re-Messung nach SB-1/2 | Doc 00 | P1 |
| **19** Wissens-Lücken-Register | chat-only + UNKNOWN-Punkte | Registry §E, G6-04, Handover 31.07 | G6_04_REGISTRY_COMPLETION, PB-02 | D-033…035-Plan-Docs, S-07-31-Detail | Doc 05 | P2 |

## Zusammenfassung

| Klasse | Docs | Anzahl |
|--------|------|--------|
| P1 — sofort baubar | 00, 01, 02, 03, 05, 06, 07, 08, 09, 10, 11, 13, 18 | 13 |
| P2 — nach Review/Entscheidung | 04, 12, 14, 15, 16, 19 | 6 |
| P3 — nachgelagert | 17 | 1 |

**13/20 Dokumente sind ohne ausstehende Entscheidungen baubar** — die
Entscheidungs-Abhängigkeit (Doc 15/16) blockiert keine P1-Dokumente.

---

*KF-01 erstellt — Implementierungs-Map, keine Volltexte.*
