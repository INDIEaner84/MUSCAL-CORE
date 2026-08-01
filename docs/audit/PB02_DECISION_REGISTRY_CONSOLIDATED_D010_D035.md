# PB-02 — Decision Registry Konsolidierung D-010 bis D-035

**Phase:** Phase B · **Block:** PB-02 (Chat → Decision Registry Consolidation)
**Datum:** 2026-08-01 · **Modus:** READ-MOSTLY (Dokumentation, kein Code)
**Quelle:** `KNOWLEDGE_FOUNDATION/audit/DECISION_REGISTRY.md` (Sektionen A–C)
**Anforderung:** Statuswerte ausschließlich: IMPLEMENTED · DOCUMENTED · PLANNED · ABANDONED · CONFLICTING · UNKNOWN

> Diese Datei überführt die Registry-Tabellen in das erweiterte 10-Feld-Format.
> Sie ersetzt nichts, ergänzt nichts an Entscheidungsinhalten — nur Struktur
> und Status-Normalisierung. Registry bleibt autoritativ für D-001…D-042.

---

## A. Architecture Decisions (D-010 … D-018)

### D-010
- **Titel:** MUSCAL 2.0 — Hybrid-Architektur gewinnt MC-015-Turnier (durable execution + hierarchisches Multi-Agenten-Modell + event-driven verification)
- **Quelle:** S2 `MUSCAL 2.0 Architektur-Turnier` (2026-07-25)
- **Datum:** 2026-07-25
- **Kategorie:** Architecture (future)
- **Status:** PLANNED
- **Evidence:** S2-Chat 25.07 (chat-only); kein Repo-Artefakt; MC-015-Referenz in Registry §E („No documented MC-015 → ADR conversion")
- **Betroffene Dateien:** UNKNOWN — keine (chat-only)
- **ADR-Verknüpfung:** keine vorhanden; ADR-022 als Phase-B-Entwurf geplant (G3-Plan §3.4)
- **Konflikte:** D-010 vs D-001 (MUSCAL 2.0 Multi-Agent vs Single-Agent-Kernel) — MEDIUM, Migrationspfad undefiniert (Registry §D)

### D-011
- **Titel:** Cognitive Kernel + Authoritative Runtime auf Edge-Hardware (signed actions, verified event store)
- **Quelle:** S2 `Cognitive Kernel Proposal` (2026-07-25)
- **Datum:** 2026-07-25
- **Kategorie:** Architecture (future)
- **Status:** PLANNED
- **Evidence:** S2-Chat 25.07 (chat-only)
- **Betroffene Dateien:** UNKNOWN — keine (chat-only)
- **ADR-Verknüpfung:** keine; ADR-023 als Phase-B-Entwurf geplant (G3-Plan §3.4)
- **Konflikte:** keine registriert

### D-012
- **Titel:** Agent-Architektur-Prinzipien P1–P5 (Modularity, Specialization, Observability, Replaceability, Human Sovereignty)
- **Quelle:** S2 `MUSCAL Agent Architecture` (2026-07-30)
- **Datum:** 2026-07-30
- **Kategorie:** Architecture (future)
- **Status:** PLANNED
- **Evidence:** S2-Chat 30.07 (Spec-Draft, chat-only)
- **Betroffene Dateien:** UNKNOWN — keine (chat-only)
- **ADR-Verknüpfung:** keine; ADR-024 als Phase-B-Entwurf geplant (G3-Plan §3.4)
- **Konflikte:** keine registriert

### D-013
- **Titel:** Prompts als deklarative kognitive Programme (Cognitive Compiler v1.0)
- **Quelle:** S2 `MUSCAL Compiler Spezifikation` (2026-07-30)
- **Datum:** 2026-07-30
- **Kategorie:** Architecture (future)
- **Status:** PLANNED
- **Evidence:** S2-Chat 30.07 (chat-only)
- **Betroffene Dateien:** UNKNOWN — keine (chat-only)
- **ADR-Verknüpfung:** keine; ADR-025 als Phase-B-Entwurf geplant (G3-Plan §3.4)
- **Konflikte:** D-013 vs D-014 — LOW (Compiler-Spec implementierungsorientiert vs RFC-Serie implementierungsunabhängig; unterschiedliche Scopes, Registry §D)

### D-014
- **Titel:** Formale Spezifikation als RFC-Serie (implementierungsunabhängig, no code)
- **Quelle:** S2 `formale Spezifikation` (2026-07-29)
- **Datum:** 2026-07-29
- **Kategorie:** Specification
- **Status:** PLANNED
- **Evidence:** S2-Chat 29.07 (chat-only)
- **Betroffene Dateien:** UNKNOWN — keine (chat-only)
- **ADR-Verknüpfung:** keine
- **Konflikte:** D-014 vs D-013 — LOW (unterschiedliche Scopes, s.o.)

### D-015
- **Titel:** E3.2 Trust Boundary Closure — 9 Bypasses geschlossen (7 CLOSED, 1 MITIGATED B-07), OVERRIDE-067…073
- **Quelle:** S2 `E3.2 Trust Boundary Abschluss`, `docs/engineering/D-E3.2-001-*`, `spec/OVERRIDE.md`
- **Datum:** 2026-07-23
- **Kategorie:** Security / Architecture
- **Status:** IMPLEMENTED
- **Evidence:** `docs/engineering/D-E3.2-001-TRUST-BOUNDARY-CLOSURE.md`, OVERRIDE.md-Einträge OVERRIDE-067…073 (committet)
- **Betroffene Dateien:** `docs/engineering/D-E3.2-001-*`, `docs/engineering/D-E3.2-002-FINAL-CLOSURE.md`, `spec/OVERRIDE.md`
- **ADR-Verknüpfung:** ADR-014-tool-runtime.md (Governance-Link, E3.2 CONFIRMED CLOSED, 9 Bypasses, 824 passed)
- **Konflikte:** keine offenen

### D-016
- **Titel:** MC-TC-004 ARB Decision — CERTIFIED (33/33 Kriterien, 431/431 Tests, 14/16 Invarianten)
- **Quelle:** `docs/audit/MC-TC-004_ARB_DECISION.md`, S2 31.07
- **Datum:** 2026-07-30
- **Kategorie:** Certification
- **Status:** IMPLEMENTED
- **Evidence:** `docs/audit/MC-TC-004_ARB_DECISION.md` (committet in Audit-Welle 392734e, 2026-08-01)
- **Betroffene Dateien:** `docs/audit/MC-TC-004_*` (10 Artefakte, 30.07)
- **ADR-Verknüpfung:** ADR-014 (Unified Tool Runtime — verifiziert durch Certification)
- **Konflikte:** keine offenen

### D-017
- **Titel:** MC-TC-007 — CONDITIONAL GO; Graph-OS-Layer nicht zertifiziert; 2 P0-Blocker (P0-1 Graph-OS Reconstruction, P0-2 Watchdog-Persistenz)
- **Quelle:** S2 `MUSCAL CORE Audit Status` (31.07, chat-only) + `docs/audit/MC-TC-007-*`
- **Datum:** 2026-07-31
- **Kategorie:** Certification
- **Status:** DOCUMENTED
- **Evidence:** `docs/audit/MC-TC-007_STATUS_ZUSAMMENFASSUNG.md` (28.07), `MC-TC-007-FULL-REALITY-CLOSURE-CERTIFICATION.md` (27.07), `MC-TC-007-TRUST-GOVERNANCE-CERTIFICATION.md` (30.07, NO-GO)
- **Betroffene Dateien:** `docs/audit/MC-TC-007-*`, `docs/PROJECT_STATE.md` (P0-Sektion, 01.08)
- **ADR-Verknüpfung:** keine
- **Konflikte:** D-017 (CONDITIONAL GO) vs PROJECT_STATE „READY WITH RISKS" (20.07) — HIGH; durch G2 §G doc-level RESOLVED (PROJECT_STATE 01.08 aktualisiert); P0-Mitigation bleibt operativer offener Punkt

### D-018
- **Titel:** ADR-014 — Unified Tool Runtime Konsolidierung (finalisiert DRAFT → ACCEPTED)
- **Quelle:** `spec/ADR-014-tool-runtime.md` (28.07, finalisiert 01.08)
- **Datum:** 2026-07-28 (finalisiert 2026-08-01)
- **Kategorie:** Architecture
- **Status:** DOCUMENTED
- **Evidence:** `spec/ADR-014-tool-runtime.md` (Status ACCEPTED, Governance-Links), Commit a39f545
- **Betroffene Dateien:** `spec/ADR-014-tool-runtime.md`, `docs/engineering/D-E3.0.2-006-TOOL-RUNTIME-CONSOLIDATION.md`, `docs/governance/ADR-014-IMPLEMENTATION_PLAN_v1.1.md`
- **ADR-Verknüpfung:** (selbst) ADR-014; erweitert durch ADR-API-001 (Dual Runtime), ADR-RUNTIME-001 (SUPL Ownership)
- **Konflikte:** D-018 PROPOSED (PROJECT_STATE 20.07) vs modifizierte ADR-Datei (28.07) — MEDIUM; durch G2 §G RESOLVED (D-038, ACCEPTED)

---

## B. Governance Decisions (D-020 … D-025)

### D-020
- **Titel:** Core-Dateien IMMUTABLE; Schreibzugriff nur via OVERRIDE + `--allow-core-write`
- **Quelle:** SESSION_RULES.md, `spec/IMMUTABILITY_CONTRACT.md`
- **Datum:** 2026-07-06
- **Kategorie:** Governance
- **Status:** IMPLEMENTED
- **Evidence:** Pre-Commit-Hook `guards/pre_commit_hook.py` aktiv; `override_052_is_active()` == True (Governance-Validierung G2, 01.08)
- **Betroffene Dateien:** `spec/OVERRIDE.md`, `guards/*`, `.pre-commit-config.yaml`
- **ADR-Verknüpfung:** ADR-007 (Core Immutability — Write Guard Policy)
- **Konflikte:** D-020 vs 29 modifizierte Core-Dateien (D-022-Violation) — CRITICAL; durch G2 RESOLVED (22 adjudiziert + 6 retroaktiv sanktioniert, D-037/D-038)

### D-021
- **Titel:** Verpflichtender SESSION_HANDOVER für jede Session mit Dateiänderungen
- **Quelle:** SESSION_RULES.md, HANDOVER_TEMPLATE.md
- **Datum:** 2026-07-11
- **Kategorie:** Governance
- **Status:** IMPLEMENTED
- **Evidence:** Nach PB-01-Backfill 17/17 eindeutige Sessions mit Handover (`docs/session_handovers/`); Commit c29c8b8
- **Betroffene Dateien:** `docs/session_handovers/HANDOVER_*.md` (17), `docs/SESSION_REGISTRY.md`
- **ADR-Verknüpfung:** keine
- **Konflikte:** D-021 („jede Session") vs 28.–31.07 ohne Handover — HIGH; durch PB-01 RESOLVED (Backfill)

### D-022
- **Titel:** Autoritätshierarchie: Git History → CHANGE_JOURNAL → SESSION_REGISTRY
- **Quelle:** CHANGE_JOURNAL.md
- **Datum:** 2026-07-12
- **Kategorie:** Governance
- **Status:** DOCUMENTED
- **Evidence:** SESSION_REGISTRY.md „Priorität der Wahrheit"; Verstoß (197 uncommitted) historisch, durch G2-Exekution aufgelöst (15 Commits, HEAD 70f630e → c29c8b8)
- **Betroffene Dateien:** `docs/CHANGE_JOURNAL.md`, `docs/SESSION_REGISTRY.md`
- **ADR-Verknüpfung:** keine
- **Konflikte:** D-022 (Kette) vs uncommitted State — CRITICAL; RESOLVED durch G2-Adjudikation + Phasen-A/B-Commits

### D-023
- **Titel:** HDR-001 (Architecture Council) — READY FOR HUMAN DECISION, blockiert HDR-002…004
- **Quelle:** `docs/PROJECT_STATE.md`
- **Datum:** 2026-07-20
- **Kategorie:** Governance
- **Status:** DOCUMENTED
- **Evidence:** PROJECT_STATE.md HDR-001-Eintrag; unverändert seit 20.07 (kein Fortschritt)
- **Betroffene Dateien:** `docs/PROJECT_STATE.md`
- **ADR-Verknüpfung:** keine
- **Konflikte:** HDR-001 ungelöst — Blocker für HDR-002…004 (keine Eskalation)

### D-024
- **Titel:** `simulation_mode: bool` → `ExecutionMode`-Enum (MC-TC-003B Override)
- **Quelle:** `spec/OVERRIDE.md` (Codebase-Root)
- **Datum:** 2026-07-25
- **Kategorie:** Governance
- **Status:** IMPLEMENTED
- **Evidence:** OVERRIDE.md-Eintrag (MC-TC-003B), committet
- **Betroffene Dateien:** `spec/OVERRIDE.md`
- **ADR-Verknüpfung:** keine
- **Konflikte:** keine registriert

### D-025
- **Titel:** ADR-Autorität: Baseline-Dokumente > Historische Dokumente
- **Quelle:** SESSION_RULES.md §HISTORICAL DOCUMENTS
- **Datum:** 2026-07-20
- **Kategorie:** Governance
- **Status:** IMPLEMENTED
- **Evidence:** SESSION_RULES.md (Autoritätskette Prio 1–6); wird in PB-03 zu v2.0 ausgebaut
- **Betroffene Dateien:** `.opencode/SESSION_RULES.md`
- **ADR-Verknüpfung:** ADR-007 (Supersession-Regel: historische ADRs ohne Autorität)
- **Konflikte:** keine registriert

---

## C. Roadmap / Strategy Decisions (D-030 … D-035)

### D-030
- **Titel:** Nächster Meilenstein nach E3.5.1: E3.6 Knowledge Distillation
- **Quelle:** S2 `Reality Closure Review` (27.07)
- **Datum:** 2026-07-27
- **Kategorie:** Roadmap
- **Status:** PLANNED
- **Evidence:** S2-Chat 27.07 (chat-only); PROJECT_STATE E3.6-Referenz (D-031-Hinweis)
- **Betroffene Dateien:** UNKNOWN — keine (chat-only)
- **ADR-Verknüpfung:** keine
- **Konflikte:** keine registriert

### D-031
- **Titel:** Reality-Score 55/100 als Produktionsreife-Indikator (nicht Qualitätsurteil)
- **Quelle:** S2 `Reality Closure Review` (27.07)
- **Datum:** 2026-07-27
- **Kategorie:** Evaluation
- **Status:** DOCUMENTED
- **Evidence:** S2-Chat 27.07; **aktualisiert:** G2-Re-Messung 2026-08-01 → Overall 61.0 (G2_EXECUTION_VALIDATION_REPORT.md §4)
- **Betroffene Dateien:** `KNOWLEDGE_FOUNDATION/audit/G2_EXECUTION_VALIDATION_REPORT.md`
- **ADR-Verknüpfung:** keine
- **Konflikte:** keine registriert (Score-Historie: 55 (27.07) → 61 (01.08), kein Widerspruch)

### D-032
- **Titel:** MUSCAL → agentengetriebene Selbstentwicklung („MUSCAL entwickelt sich durch Agenten")
- **Quelle:** S2 `Agenten-Orchestrierung` (21.07)
- **Datum:** 2026-07-21
- **Kategorie:** Strategy
- **Status:** PLANNED
- **Evidence:** S2-Chat 21.07 (chat-only, Vision)
- **Betroffene Dateien:** UNKNOWN — keine (chat-only)
- **ADR-Verknüpfung:** keine
- **Konflikte:** keine registriert

### D-033
- **Titel:** Closed-Source-Strategie: nur Plugins veröffentlichen
- **Quelle:** S2 `Closed-Source Projektplan` (23.07)
- **Datum:** 2026-07-23
- **Kategorie:** Strategy
- **Status:** PLANNED
- **Evidence:** S2-Chat 23.07 (chat-only)
- **Betroffene Dateien:** UNKNOWN — keine (chat-only)
- **ADR-Verknüpfung:** keine
- **Konflikte:** keine registriert

### D-034
- **Titel:** Benchmark-Framework: MUSCAL vs LangChain / AutoGen / CrewAI
- **Quelle:** S2 `Benchmark Framework Planung` (29.07)
- **Datum:** 2026-07-29
- **Kategorie:** Evaluation
- **Status:** PLANNED
- **Evidence:** S2-Chat 29.07 (chat-only)
- **Betroffene Dateien:** UNKNOWN — keine (chat-only)
- **ADR-Verknüpfung:** keine
- **Konflikte:** keine registriert

### D-035
- **Titel:** SLM-Datenstrategie für Spezialisierungs-Effizienz
- **Quelle:** S2 `Datenstrategie für SLM` (29.07)
- **Datum:** 2026-07-29
- **Kategorie:** Strategy
- **Status:** PLANNED
- **Evidence:** S2-Chat 29.07 (chat-only)
- **Betroffene Dateien:** UNKNOWN — keine (chat-only)
- **ADR-Verknüpfung:** keine
- **Konflikte:** keine registriert

---

## Status-Summary (Normalisierung)

| Status | Entscheidungen |
|--------|----------------|
| IMPLEMENTED | D-015, D-016, D-020, D-021, D-024, D-025 (6) |
| DOCUMENTED | D-017, D-018, D-022, D-023, D-031 (5) |
| PLANNED | D-010, D-011, D-012, D-013, D-014, D-030, D-032, D-033, D-034, D-035 (10) |
| ABANDONED | — (0) |
| CONFLICTING | — (0; Konflikte als Felder dokumentiert, G2-Resolutionen verlinkt) |
| UNKNOWN | — (0; Betroffene-Dateien-Feld = UNKNOWN bei chat-only Entscheidungen) |

*Normalisierung: Registry-Statusausdrücke („planned (chat-only, no ADR)", „implemented (not in git)", „conflicting") wurden auf die erlaubten 6 Statuswerte abgebildet; Konflikt-Informationen wandern in das Feld „Konflikte".*

---

*Evidenz: KNOWLEDGE_FOUNDATION/audit/DECISION_REGISTRY.md (98 Zeilen, D-001…D-042 inkl. G2-Erweiterungen), G2_EXECUTION_VALIDATION_REPORT.md, docs/audit/MC-TC-00x-Artefakte, docs/session_handovers/ (17 Dateien), git log (HEAD c29c8b8).*
