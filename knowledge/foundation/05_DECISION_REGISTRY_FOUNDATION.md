# 05_DECISION_REGISTRY_FOUNDATION.md

**Doc:** KF-1/05 · **Date:** 2026-08-02 · **Layer:** STRUCTURED KNOWLEDGE (konsolidiert)
**Sources:** KNOWLEDGE_FOUNDATION/audit/DECISION_REGISTRY.md (autoritativ, D-001…D-042), `docs/audit/PB02_DECISION_REGISTRY_CONSOLIDATED_D010_D035.md` (10-Feld-Normalisierung), `docs/audit/G6_04_REGISTRY_COMPLETION.md` (D-033…035-Verifikation), G2_ADJUDICATION_REPORT (D-036…042)
**Modus:** Extraktion/Ordnung aus vorhandener Evidence — **keine Interpretation, keine neuen Entscheidungen**
**Status-Vokabular:** IMPLEMENTED · DOCUMENTED · PLANNED · ABANDONED · CONFLICTING · UNKNOWN (+ CHAT_ONLY-Markierung, unverändert beibehalten)
**Regel (G6-04):** CHAT_ONLY bleibt CHAT_ONLY — keine Statusänderung ohne neue Evidence.

---

## A. Architecture Decisions (D-001 … D-018)

| ID | Titel | Datum | Quelle | Status | Evidence | Supersession | Implementierungsbezug |
|----|-------|-------|--------|--------|----------|--------------|----------------------|
| D-001 | Execution-Graph-Compiler statt MCXF-Interpreter (MAS-0301, Ziel <50ms) | 2026-07-04 | DECISIONS.md, `spec/ADR-001-kernel.md`, `archive/history/rfcs/MAS-0301.md` | IMPLEMENTED | C0 | keine; Konflikt mit D-010 (Migrationspfad offen) | Kernel-Pfad ADR-001; Execution Graph im Kernel (Root-`*.py`-Kern) |
| D-002 | 7-Schichten-Architektur (L0 Storage – L6 Frontend), 4 Sub-Kernel + System-Spine-Validierung | 2026-07-04 | DECISIONS.md, `spec/ADR-002-memory.md` | IMPLEMENTED | C0 | keine | ADR-002; Memory-Layer implementiert |
| D-003 | Capability-First-Routing (Tasks vs Capabilities, nicht Modellnamen) | 2026-07-04 | DECISIONS.md, `spec/ADR-003-events.md`, MAS-0001 | IMPLEMENTED | C0 | keine | ADR-003; Event-Routing |
| D-004 | Lazy-Initialisierung ersetzt Modul-Level-Import-Seiteneffekte | 2026-07-06 | DECISIONS.md | IMPLEMENTED | C0 | keine | Kernel-Boot-Änderung 06.07 |
| D-005 | Graph/Memory/Event-Bounding (5000/10000 Knoten-Kanten, 10000 Rows, 50000 Events) | 2026-07-06 | DECISIONS.md | IMPLEMENTED | C0 | keine | Bounding-Limits im Kernel |
| D-006 | Alle Erweiterungen als Plugins in `features/`; Core immutable | 2026-07-06 | DECISIONS.md, IMMUTABILITY_CONTRACT.md | IMPLEMENTED | C0 | keine; Konflikt D-006/D-022 (CRITICAL) durch G2 RESOLVED (D-037/D-038) | AGENTS.md-Plugin-Contract; 42 Plugin-Dirs |
| D-007 | Verifikations-Layer als Plugin (`features/event_sourcing/`), NICHT Core | 2026-07-11 | DECISIONS.md, `spec/ADR-011-verification.md` | IMPLEMENTED | C0 | keine | ADR-011; features/event_sourcing/ |
| D-008 | EventBus/EventStore/AuditLog semantische Trennung (nicht verschmelzen) | 2026-07-21 | S2 `Reconciliation Report Bewertung` | IMPLEMENTED (EventStore existiert) | C1 | keine | EventStore-Layer (E3.2, 19./20.07) |
| D-009 | EventStore.append()-Signatur vor Integration verifizieren (Bridge-Callback-Mismatch) | 2026-07-21 | S2 `Reconciliation Report Bewertung` | IMPLEMENTED (validated) | C1 | keine | Bridge-Callback; verifiziert |
| D-010 | MUSCAL 2.0: Hybrid-Architektur gewinnt MC-015 (durable execution + hierarchisches Multi-Agenten + event-driven verification) | 2026-07-25 | S2 `MUSCAL 2.0 Architektur-Turnier` (chat-only) | PLANNED (**CHAT_ONLY**) | C2 | keine vorhandene; Konflikt D-010 vs D-001 MEDIUM (Migrationspfad offen) | UNKNOWN — keine Dateien; ADR-022 als Phase-B-Entwurf (G3-Plan §3.4) |
| D-011 | Cognitive Kernel + Authoritative Runtime auf Edge-Hardware (signed actions, verified event store) | 2026-07-25 | S2 `Cognitive Kernel Proposal` (chat-only) | PLANNED (**CHAT_ONLY**) | C2 | keine | UNKNOWN; ADR-023 als Phase-B-Entwurf (G3-Plan §3.4) |
| D-012 | Agent-Architektur-Prinzipien P1–P5 (Modularity, Specialization, Observability, Replaceability, Human Sovereignty) | 2026-07-30 | S2 `MUSCAL Agent Architecture` (chat-only, Spec-Draft) | PLANNED (**CHAT_ONLY**) | C2 | keine | UNKNOWN; ADR-024 als Phase-B-Entwurf (G3-Plan §3.4) |
| D-013 | Prompts als deklarative kognitive Programme (Cognitive Compiler v1.0) | 2026-07-30 | S2 `MUSCAL Compiler Spezifikation` (chat-only) | PLANNED (**CHAT_ONLY**) | C2 | keine; Konflikt D-013 vs D-014 LOW (unterschiedliche Scopes) | UNKNOWN; ADR-025 als Phase-B-Entwurf (G3-Plan §3.4) |
| D-014 | Formale Spezifikation als RFC-Serie (implementierungsunabhängig, no code) | 2026-07-29 | S2 `formale Spezifikation` (chat-only) | PLANNED (**CHAT_ONLY**) | C2 | keine | UNKNOWN |
| D-015 | E3.2 Trust-Boundary-Closure: 9 Bypasses geschlossen (7 CLOSED, 1 MITIGATED B-07), OVERRIDE-067…073 | 2026-07-23 | S2 `E3.2 Trust Boundary Abschluss`, `docs/engineering/D-E3.2-001-*`, `spec/OVERRIDE.md` | IMPLEMENTED | C1 | keine offenen | `docs/engineering/D-E3.2-001-TRUST-BOUNDARY-CLOSURE.md`, `D-E3.2-002-FINAL-CLOSURE.md`, OVERRIDE-067…073 (committet); ADR-014-Governance-Link |
| D-016 | MC-TC-004 ARB Decision: CERTIFIED (33/33 Kriterien, 431/431 Tests, 14/16 Invarianten) | 2026-07-30 | `docs/audit/MC-TC-004_ARB_DECISION.md`, S2 31.07 | IMPLEMENTED | C1 | keine | `docs/audit/MC-TC-004_*` (10 Artefakte, 30.07; committet 392734e, 01.08); ADR-014 verifiziert |
| D-017 | MC-TC-007: CONDITIONAL GO — Graph-OS-Layer nicht zertifiziert; 2 P0-Blocker (P0-1, P0-2) | 2026-07-31 | S2 `MUSCAL CORE Audit Status` (chat-only) + `docs/audit/MC-TC-007-*` | DOCUMENTED | C2 (Status-Statement chat), C1 (Artefakte) | Konflikt vs PROJECT_STATE „READY WITH RISKS" HIGH — **G2 §G doc-level RESOLVED** (PROJECT_STATE 01.08, d5f5ce7); P0-Mitigation bleibt operativ offen | `docs/audit/MC-TC-007-*`, PROJECT_STATE-P0-Sektion (01.08) |
| D-018 | ADR-014: Unified Tool Runtime Konsolidierung | 2026-07-28 (finalisiert 01.08) | `spec/ADR-014-tool-runtime.md` | DOCUMENTED | C1 | Statuskonflikt PROPOSED vs Datei MEDIUM — **durch D-038 finalisiert (ACCEPTED)** | `spec/ADR-014-tool-runtime.md` (a39f545), `D-E3.0.2-006-TOOL-RUNTIME-CONSOLIDATION.md`, `ADR-014-IMPLEMENTATION_PLAN_v1.1.md`; erweitert durch ADR-API-001, ADR-RUNTIME-001 |

## B. Governance Decisions (D-020 … D-025)

| ID | Titel | Datum | Quelle | Status | Evidence | Supersession | Implementierungsbezug |
|----|-------|-------|--------|--------|----------|--------------|----------------------|
| D-020 | Core-Dateien IMMUTABLE; Schreibzugriff nur via OVERRIDE + `--allow-core-write` | 2026-07-06 | SESSION_RULES.md, `spec/IMMUTABILITY_CONTRACT.md` | IMPLEMENTED | C0 | keine; Konflikt D-020 vs 29 Core-Dateien CRITICAL — durch G2 RESOLVED (D-037/D-038) | `guards/pre_commit_hook.py`, `spec/OVERRIDE.md`; ADR-007 (Write Guard Policy); `override_052_is_active()==True` (G2-Validierung 01.08) |
| D-021 | Verpflichtender SESSION_HANDOVER je Session mit Änderungen | 2026-07-11 | SESSION_RULES.md, HANDOVER_TEMPLATE.md | IMPLEMENTED | C1 | Konflikt „keine Handovers 28.–31.07" HIGH — durch PB-01-Backfill RESOLVED (17/17, c29c8b8) | `docs/session_handovers/HANDOVER_*.md` (17), SESSION_REGISTRY.md |
| D-022 | Autoritätshierarchie: Git History → CHANGE_JOURNAL → SESSION_REGISTRY | 2026-07-12 | CHANGE_JOURNAL.md | DOCUMENTED | C0 | Verstoß (197 uncommitted) historisch — durch G2-Exekution + Phasen-Commits RESOLVED (HEAD 70f630e → c29c8b8) | `docs/CHANGE_JOURNAL.md`, `docs/SESSION_REGISTRY.md` |
| D-023 | HDR-001 (Architecture Council) — READY FOR HUMAN DECISION, blockiert HDR-002…004 | 2026-07-20 | `docs/PROJECT_STATE.md` | DOCUMENTED | C1 | keine — ungelöst seit 20.07 (RC-2, Blocker) | PROJECT_STATE.md-HDR-001-Eintrag; Decision-Record `docs/governance/HDR-001_DECISION_RECORD.md` (G7-02, Optionen A–D) |
| D-024 | `simulation_mode: bool` → `ExecutionMode`-Enum (MC-TC-003B Override) | 2026-07-25 | `spec/OVERRIDE.md` (Codebase-Root) | IMPLEMENTED | C1 | keine | OVERRIDE.md-Eintrag MC-TC-003B (committet) |
| D-025 | ADR-Autorität: Baseline-Dokumente > Historische Dokumente | 2026-07-20 | SESSION_RULES.md §HISTORICAL | IMPLEMENTED | C0 | keine | `.opencode/SESSION_RULES.md` (Prio-Kette; v2.0 PB-03); ADR-007-Supersession-Regel |

## C. Roadmap / Strategy Decisions (D-030 … D-035)

| ID | Titel | Datum | Quelle | Status | Evidence | Supersession | Implementierungsbezug |
|----|-------|-------|--------|--------|----------|--------------|----------------------|
| D-030 | Nächster Meilenstein nach E3.5.1: E3.6 Knowledge Distillation | 2026-07-27 | S2 `Reality Closure Review` (chat-only) | PLANNED (**CHAT_ONLY**) | C2 | keine | UNKNOWN — keine Dateien |
| D-031 | Reality-Score 55/100 als Produktionsreife-Indikator (nicht Qualitätsurteil) | 2026-07-27 | S2 `Reality Closure Review` (chat-only); G2-Re-Messung 01.08 | DOCUMENTED | C2 (Score-Herkunft), C0 (G2-Re-Messung) | Score aktualisiert: 55 (27.07) → **61.0 (01.08, G2_EXECUTION_VALIDATION_REPORT §4)** — kein Widerspruch | `KNOWLEDGE_FOUNDATION/audit/G2_EXECUTION_VALIDATION_REPORT.md` |
| D-032 | MUSCAL → agentengetriebene Selbstentwicklung („MUSCAL entwickelt sich durch Agenten") | 2026-07-21 | S2 `Agenten-Orchestrierung` (chat-only, Vision) | PLANNED (**CHAT_ONLY**) | C2 | keine | UNKNOWN |
| D-033 | Closed-Source-Strategie: nur Plugins veröffentlichen | 2026-07-23 | S2 `Closed-Source Projektplan` (chat-only) | PLANNED (**CHAT_ONLY**) | C2 | keine; **G6-04 verifiziert: kein Repo-Artefakt** | UNKNOWN; Plan-Doc offen (RC-5) |
| D-034 | Benchmark-Framework: MUSCAL vs LangChain / AutoGen / CrewAI | 2026-07-29 | S2 `Benchmark Framework Planung` (chat-only) | PLANNED (**CHAT_ONLY**) | C2 | keine; **G6-04 verifiziert: kein Repo-Artefakt** | UNKNOWN; Plan-Doc offen (RC-5) |
| D-035 | SLM-Datenstrategie für Spezialisierungs-Effizienz | 2026-07-29 | S2 `Datenstrategie für SLM` (chat-only) | PLANNED (**CHAT_ONLY**) | C2 | keine; **G6-04 verifiziert: kein Repo-Artefakt** | UNKNOWN; Plan-Doc offen (RC-5) |

## D. Adjudication Decisions (D-036 … D-042, G2-Gate)

| ID | Titel | Datum | Quelle | Status | Evidence | Supersession | Implementierungsbezug |
|----|-------|-------|--------|--------|----------|--------------|----------------------|
| D-036 | G2-01: C1 EventStore/Replay-Cluster (4 Dateien) SANCTIONED — Certification als Entscheidungs-Record | 2026-08-01 | G2_ADJUDICATION_REPORT.md G2-01 | IMPLEMENTED | C1 | keine | Cluster committet (G2-Exekution); MC-TC-004/006 als Record |
| D-037 | G2-02: C2 Phase-1A Execution-Identity-Cluster (7 Dateien) SANCTIONED-CONDITIONAL; OVERRIDE.md-Truth-Correction | 2026-08-01 | G2_ADJUDICATION_REPORT.md G2-02 | IMPLEMENTED | C1 | keine | Cluster committet; OVERRIDE.md korrigiert |
| D-038 | G2-03/04/06: C3 UTR (5), C4 Phase-1b (4), 6 Sweep-Dateien SANCTIONED; ADR-014 finalisiert DRAFT → **ACCEPTED** | 2026-08-01 | G2_ADJUDICATION_REPORT.md G2-03/04/06 | IMPLEMENTED | C1 | **supersedes D-018-Statuskonflikt** (D-018 → ACCEPTED) | Dateien committet; ADR-014 aktualisiert |
| D-039 | G2-05/07: OVERRIDE.md aus Baseline + Phase-1A-Welle + Truth-Correction rekonstruiert; OVERRIDE-052-Mechanismus wiederhergestellt | 2026-08-01 | G2_ADJUDICATION_REPORT.md G2-05/07 | IMPLEMENTED | C0 | schließt D-020-Implementierungslücke (OVERRIDE-Registry) | `spec/OVERRIDE.md` (rekonstruiert, 1.541 Z.) |
| D-040 | FL-01a: 19 reihenfolge-abhängige flaky Tests NICHT gefixt — Register; Root-Cause globale Singletons (`tools._UTR`, `set_global_utr`, `set_global_event_store`); Fixture-Fix deferred | 2026-08-01 | G2_ADJUDICATION_REPORT.md FL-01a | DOCUMENTED (open) | C1 | keine | `FL01A_FLAKINESS_REGISTER.md`; Test-Suite (19 flaky / 2.347 passed / 1 skipped) |
| D-041 | FL-01b: 4 deterministische Baseline-Drift-Fehler — EXPECTED_TOTAL auf verifizierte Reconciliation-Zahlen neu kalibriert (test-only) | 2026-08-01 | G2_ADJUDICATION_REPORT.md FL-01b | IMPLEMENTED | C0 | keine | Baseline 470 (18/18 grün, test-only-Commits) |
| D-042 | Global-State-Ownership-ADR als Phase-B-Follow-up (Singleton-Policy `_UTR`/Event-Store-Globals) | 2026-08-01 | G2_ADJUDICATION_REPORT.md FL-01a → D | PLANNED | C2 | keine — Nachfolger von D-040 (Fix-Basis) | Entwurf `GLOBAL_STATE_ARCHITECTURE_DECISION_DRAFT` (KF-Schicht, RC-6); ARB-Freigabe offen |

## E. Nicht registrierte IDs (Wissens-Lücken, keine Erfindung)

| ID | Befund | Quelle |
|----|--------|--------|
| D-019 | **kein Registry-Eintrag** — ID-Lücke | DECISION_REGISTRY (keine Zeile) |
| D-026 … D-029 | **keine Registry-Einträge** — ID-Lücken | DECISION_REGISTRY (keine Zeilen) |

| Gap | Evidence | Implication |
|-----|----------|-------------|
| Kein ADR für EventStore/ReplayService-Einführung | `spec/ADRs/ADR-EVENT-001-eventstore-boundary.md` existiert nur dort, nicht in kanonischem `spec/`-Set | ADR-Nummerierungs-Inkonsistenz |
| Kein ADR für v0.8 (CHANGELOG_v0.8.md, kein ADR-015+) | CHANGELOG_v0.8.md | Versionierungs-Gap |
| Keine dokumentierte MC-015→ADR-Konvertierung | S2 25.07 | Architektur-Richtung repo-unsichtbar |
| MKSD (MUSCAL Kernel Specification Document) explizit fehlend | S2 `Spezifikation offen` 28.07 | Spec-Gap bestätigt |

## F. Status-Summary (Normalisierung unverändert)

| Status | Entscheidungen |
|--------|----------------|
| IMPLEMENTED | D-001…D-009, D-015, D-016, D-020, D-021, D-024, D-025, D-036, D-037, D-038, D-039, D-041 (20) |
| DOCUMENTED | D-017, D-018, D-022, D-023, D-031, D-040 (6) |
| PLANNED | D-010, D-011, D-012, D-013, D-014, D-030, D-032, D-033, D-034, D-035, D-042 (11) |
| ABANDONED | — (0) |
| CONFLICTING | — (0; Konflikte als Felder dokumentiert, G2-Resolutionen verlinkt) |
| UNKNOWN | — (0; „Betroffene Dateien" = UNKNOWN bei chat-only) |
| **CHAT_ONLY-Markierung** | D-010, D-011, D-012, D-013, D-014, D-030, D-031 (Score-Quelle), D-032, D-033, D-034, D-035 (11) |

## G. Validierung

| Prüfpunkt | Ergebnis |
|-----------|----------|
| Nur vorhandene IDs/Daten | ✅ D-001…D-018, D-020…D-025, D-030…D-042 extrahiert; fehlende IDs (D-019, D-026…029) als Lücken gelistet, nicht erfunden |
| Keine Interpretation | ✅ Titel/Datum/Status/Quelle wörtlich aus Registry + PB-02 + G6-04 |
| Keine neuen Entscheidungen | ✅ keine ID/Datum/Status neu gesetzt |
| CHAT_ONLY bleibt CHAT_ONLY | ✅ 11 Einträge unverändert markiert (G6-04-Regel) |
| Supersession nur mit Beleg | ✅ nur G2-Resolutionen (D-038 finalisiert D-018; D-039 schließt D-020-Lücke; D-042 Nachfolger von D-040) |
| Implementierungsbezug nur mit Datei-/Commit-Beleg | ✅ Dateipfade + Commits (c29c8b8, 392734e, a39f545, d5f5ce7, 70f630e) aus Quellen |

---

*Erstellt aus DECISION_REGISTRY.md (autoritativ) + PB-02 + G6-04 + G2-Report. Kein neues Wissen; Registry bleibt autoritativ für D-001…D-042.*
