# FOUNDATION_SOURCE_BINDING — Audit-Artefakte → Foundation-Dokumente

**Gate:** KF-02 · **Date:** 2026-08-01 · **Modus:** Struktur & Mapping
**Referenz:** KF-Charter (Confidence), 20_DOC_IMPLEMENTATION_MAP (Doc-Nummern), PB-05
**Regel:** 1-zu-n-Zuordnung erlaubt; jedes Foundation-Dokument referenziert seine Quellen über diese Tabelle (kein Kopieren).

---

## 1. KF-Audit-Artefakte (KNOWLEDGE_FOUNDATION/audit/)

| Audit-Artefakt | → Foundation-Dokument(e) | Verwendung |
|----------------|--------------------------|------------|
| AUDIT_SCOPE.md | Doc 01 | Methodik komplett |
| REPOSITORY_CENSUS.md | Doc 02, Doc 14 | Zahlen, Struktur |
| SOURCE_OF_TRUTH_MAP.md | Doc 03 | Autoritäts-Matrix |
| REFERENCE_GRAPH.md | Doc 04 | Knoten/Edges |
| DECISION_REGISTRY.md | Doc 05, Doc 16 | D-001…042 |
| CHAT_CODE_DOC_RECONCILIATION.md | Doc 06 | Chat-Claims |
| TECHNICAL_MANUAL_CONFLICT_REPORT.md | Doc 07 | Konflikte |
| SESSION_CONTINUITY_AUDIT.md | Doc 09 | Continuity-Score |
| CONCEPT_EVOLUTION_MAP.md | Doc 11 | Evolution |
| MASTER_INDEX.md | Doc 00, Doc 18 | Metriken, Verzeichnis |
| PHASE_A_REMEDIATION_PLAN / EXECUTION_RESULT | Doc 08 | Phase A |
| PA03_07_ADJUDICATION_DISPOSITION | Doc 08 | Adjudikation |
| GIT_PRE_COMMIT_STATE.md | Doc 08, Doc 02 | Baseline-Zustand |
| G2_ADJUDICATION_REPORT / EXECUTION_VALIDATION | Doc 08, Doc 18 | G2-Gate |
| G3_PHASE_B_EXECUTION_PLAN | Doc 08, Doc 09 | Plan + Backfill |
| G4_MEASUREMENT_REPORT / G4_DECISION_GATE | Doc 08, Doc 18 | G4-Gate |
| G4_5_EXECUTION_RESULT | Doc 08 | G4.5 |
| G5_FINAL_READINESS_REPORT | Doc 08, Doc 18, Doc 16 | G5 + Blocker |
| DECISION_CLOSURE_PACKAGE | Doc 16 | RC-1…6 |
| GLOBAL_STATE_ARCHITECTURE_DECISION_DRAFT | Doc 10, Doc 16 | ADR-042-Vorschlag |

## 2. In-Repo-Artefakte (MUSCAL CORE/)

| In-Repo-Artefakt | → Foundation-Dokument(e) | Verwendung |
|------------------|--------------------------|------------|
| docs/audit/MC-TC-002…007 (55 Cert-Docs) | Doc 15 | Zertifizierungen |
| docs/audit/FL01A_FLAKINESS_REGISTER.md | Doc 10 | Flakiness |
| docs/audit/PB02_DECISION_REGISTRY_CONSOLIDATED | Doc 05 | Konsolidierung |
| docs/audit/ADR_CANONICAL_MAP.md | Doc 13 | ADR-Übersicht |
| docs/audit/TECHNICAL_MANUAL_AUTHORITY_MAP.md | Doc 07 | Autoritätsbereiche |
| docs/audit/MANUAL_RECONCILIATION_FINAL.md | Doc 07 | Resolutionen |
| docs/audit/TECHNICAL_MANUAL_v0.8_SCOPE.md | Doc 14 | Zahlen + Abgrenzung |
| docs/audit/TC_H3_CLOSURE.md | Doc 07 | TC-H3-Matrix |
| docs/audit/G6_04_REGISTRY_COMPLETION.md | Doc 05, Doc 19 | D-033…035 |
| docs/audit/G6_READINESS_RECHECK.md | Doc 18 | Re-Messung |
| docs/audit/G7_01_RC1_DECISION_BRIEFS.md | Doc 15, Doc 16 | P0-Briefe |
| docs/governance/HDR-001_DECISION_RECORD.md | Doc 16 | HDR-Brief |
| docs/audit/ADR_REVIEW_MATRIX.md | Doc 13 | Review-Vorbereitung |
| docs/audit/KNOWLEDGE_FOUNDATION_GATE.md | Doc 00 | Gate-Bewertung |
| spec/ADR-INDEX.md + ADR-001…025 | Doc 13, Doc 14 | ADR-Basis |
| spec/OVERRIDE.md (1.541 Z.) | Doc 12 | Override-Registry |
| .opencode/SESSION_RULES.md (v2.0) | Doc 03, Doc 09 | Kette + Checklist |
| docs/session_handovers/ (17) | Doc 09 | Handovers |
| docs/PROJECT_STATE.md | Doc 03, Doc 15, Doc 16 | Zustand + P0 + HDR |
| docs/engineering/D-*.md | Doc 05, Doc 14 | E3.x-Entscheidungen |
| docs/governance/ (WORK_QUEUE, ACTIVE_TASKS, …) | Doc 12 | Governance Ops |

## 3. Abdeckungs-Check

| Foundation-Doc | Quellen gedeckt? | offene Quellen |
|----------------|------------------|----------------|
| Doc 00–14, 18 | ✅ vollständig | — |
| Doc 15 | ⚠️ Zertifikate ja; **P0-Status unentschieden** (RC-1) | RC-1-Entscheidung |
| Doc 16 | ⚠️ Unterlagen ja; **Entscheidungen offen** (RC-1/RC-2) | Human Decisions |
| Doc 17 | ⚠️ Laufzeit-Artefakte vorhanden; **Governance-Beschluss fehlt** | Bridge-Regel |
| Doc 19 | ⚠️ Lücken dokumentiert; **D-033…035-Plan-Docs fehlen** | RC-5 |

**Kernaussage:** 15/20 Dokumente haben 100 % Quellenbindung; 5 Dokumente
(15, 16, 17, 19, 12-P2) warten auf Entscheidungen/Docs — keine davon ist P1.

---

*KF-02 erstellt — Source-Binding, keine Inhalte.*
