# KNOWLEDGE_FOUNDATION_MAPPING — Audit-Artefakte → 20-Document Plan

**Phase:** Phase B · **Block:** PB-05 · **Datum:** 2026-08-01
**Modus:** READ-MOSTLY (Mapping, keine Migration)
**Referenz:** `KNOWLEDGE_FOUNDATION/audit/MASTER_INDEX.md` (Phase C: „start the 20-document Knowledge Foundation plan (using this audit as its source basis)"), `G3_PHASE_B_EXECUTION_PLAN.md` §4.1

> Doc-Nummern folgen der G3-Plan-Zuordnung (Doc 00…12; weitere Doc 13–19 sind
> noch nicht zugeordnet — siehe unten „fehlende Daten").

---

## 1. Audit-Artefakte → KF-Dokumente

| Audit Artifact (KNOWLEDGE_FOUNDATION/audit/) | KF Dokument | Status | fehlende Daten |
|----------------------------------------------|-------------|--------|----------------|
| MASTER_INDEX.md | Doc 00 (Master Index / Metriken) | ✅ vollständig | — |
| AUDIT_SCOPE.md | Doc 01 (Overview, Methodik, Confidence-Modell) | ✅ vollständig | — |
| REPOSITORY_CENSUS.md | Doc 02 (Repository Index) | ⚠️ teilweise | Git-History-abhängige Zahlen (Änderungen seit 01.08) |
| SOURCE_OF_TRUTH_MAP.md | Doc 03 (Source-of-Truth Map) | ⚠️ teilweise | Re-Run nach PB-03 (Autoritätskette v2.0, 8 Ebenen) |
| REFERENCE_GRAPH.md | Doc 04 (Knowledge Graph) | ⚠️ teilweise | Neue Knoten: SESSION_RULES v2.0, Handovers 28.–31.07, ADR_CANONICAL_MAP |
| DECISION_REGISTRY.md | Doc 05 (Decision Registry) | ⚠️ erweitert | PB-02-Konsolidierung (D-010…D-035, 10-Feld-Format) in KF-Registry übertragen |
| CHAT_CODE_DOC_RECONCILIATION.md | Doc 06 (Chat-Code-Doc Reconciliation) | ✅ vollständig | — |
| TECHNICAL_MANUAL_CONFLICT_REPORT.md | Doc 07 (Manual Conflict) | ✅ vollständig | — |
| PHASE_A_REMEDIATION_PLAN.md, G2_ADJUDICATION_REPORT.md, G2_EXECUTION_VALIDATION_REPORT.md, G3_PHASE_B_EXECUTION_PLAN.md, PHASE_A_EXECUTION_RESULT.md, PA03_07_ADJUDICATION_DISPOSITION.md, GIT_PRE_COMMIT_STATE.md | Doc 08 (Remediation & Governance-Historie) | ✅ vollständig | Phase-B-Ergebnisse (PB-01…PB-06) einpflegen |
| SESSION_CONTINUITY_AUDIT.md | Doc 09 (Session Continuity) | ⚠️ veraltet | Score 41/100 → Re-Run nach PB-01 (Backfill) + PB-03 (Checklist); Ziel >75 |
| FL01A_FLAKINESS_REGISTER.md (in-repo: `MUSCAL CORE/docs/audit/`) | Doc 10 (Test Governance) | ✅ vollständig | — |
| CONCEPT_EVOLUTION_MAP.md | Doc 11 (Temporal Analysis) | ✅ vollständig | — |
| — (fehlt) | Doc 12 (Governance Ops — WORK_QUEUE/ACTIVE_TASKS-Synopse) | ❌ fehlt | Synthese aus `docs/governance/` + Override-Registry |
| — (fehlt) | Doc 13–19 (offene KF-Dokumente) | ❌ fehlt | Themenvorschläge: ADR-Index-Struktur, Bridge-Handover-Klassifikation, E3.x-Meilenstein-Log, Flakiness-Fix-Entscheidung (D-040/D-042), P0-Entscheidungslog |

## 2. Phase-B-Artefakte (neu, in-repo) → KF-Dokumente

| Phase-B Artifact (MUSCAL CORE/) | KF Dokument | Status | fehlende Daten |
|---------------------------------|-------------|--------|----------------|
| docs/session_handovers/HANDOVER_S-2026-07-28/30/31-001.md | Doc 09 (Session Continuity) | ✅ erstellt | — |
| docs/audit/PB02_DECISION_REGISTRY_CONSOLIDATED_D010_D035.md | Doc 05 (Decision Registry) | ✅ erstellt | Übertrag in KF-Datei (nur Verweis statt Duplikat) |
| .opencode/SESSION_RULES.md (v2.0) | Doc 03 (Source-of-Truth), Doc 09 | ✅ erstellt | — |
| docs/audit/ADR_CANONICAL_MAP.md | Doc 04 (Knowledge Graph), Doc 08 | ✅ erstellt | INDEX-Aktualisierung (F-01…F-03) nach G4 |
| docs/audit/PB02_* → Verweis | Doc 05 | ✅ | — |

## 3. Zuordnungspflicht (Vorgehen Phase C)

1. 20-Doc-Plan startet NUR nach Gate G4 (alle 5 Metriken >75).
2. KF-Dokumente referenzieren Audit-Artefakte (keine Duplikation); Audit-Bestand bleibt Read-Only-Referenz.
3. Fehlende Daten aus Spalte 3 werden während Phase C aus den in-repo-Quellen (docs/audit/, docs/engineering/, docs/governance/) extrahiert.
4. Confidence-Modell [C0–C4] gilt für alle KF-Dokumente (AUDIT_SCOPE §5).

---

*Methode: Abgleich des 17-Datei-Audit-Inventars (KNOWLEDGE_FOUNDATION/audit/) mit der G3-Plan-Zuordnung (Doc 00–12) + Phase-B-Neuartefakte (Commits c29c8b8, accd4bc, 6056f47, a977091).*
