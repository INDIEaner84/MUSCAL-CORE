# G3_PHASE_B_EXECUTION_PLAN — Mission-Control Readiness 61 → >75

**Audit-ID:** MUSCAL-KRA-2026-08-01 · **Gate:** G3 (Planning) · **Date:** 2026-08-01
**Mode:** Mission-Control Governance Planner · **Status:** PLAN ONLY — no execution
**Reference:** G2_EXECUTION_VALIDATION_REPORT.md §4 (Metriken), PHASE_A_REMEDIATION_PLAN.md, MASTER_INDEX.md
**Current readiness:** 61.0/100 (M1: 78, M2: 72, M3: 55, M4: 45, M5: 55)

---

## 1. Handover-Backfill Strategie

### 1.1 Fehlende Session-Übergaben

**Evidenz:** 14 Handovers in `docs/session_handovers/`, letzter `HANDOVER_S-2026-07-27-001.md`. SESSION_REGISTRY führt 18 Sessions (bis 31.07); Sessions 28.–31.07 haben **keine Handover-Dateien**. Die Audit-Welle (MC-TC-004-Zertifizierung 30.07, MC-TC-007-Status 31.07) ist nur über `docs/audit/` + S2-Chats rekonstruierbar.

| Session (registry) | Datum | Inhalt (Evidence) | Handover vorhanden |
|--------------------|-------|-------------------|--------------------|
| S-2026-07-28-001 | 28.07 | MC-TC-007 Status Zusammenfassung (`docs/audit/MC-TC-007_STATUS_ZUSAMMENFASSUNG.md`, mtime 28.07) | ❌ |
| S-2026-07-30-001 | 30.07 | MC-TC-004 Certification + ARB Decision (10 Audit-Dateien, mtime 30.07) | ❌ |
| S-2026-07-31-001 | 31.07 | MC-TC-007 Reality Closure / CONDITIONAL GO (S2-Chat 31.07 + `MC-TC-007-TRUST-GOVERNANCE-CERTIFICATION.md` 30.07) | ❌ |
| (Bridge-Sessions 28.–29.07) | 28–29.07 | `docs/bridge/handovers/handover_20260728T*.md|yaml` (≈160 Dateien) | ⚠️ Bridge-Format, nicht SESSION_HANDOVER-Format |

### 1.2 Chat → Decision Registry Mapping (Backfill-Quellen)

| Chat (S2, 17.–31.07) | Decision-IDs | Registry-Status | Phase-B-Aktion |
|----------------------|--------------|-----------------|----------------|
| MUSCAL 2.0 Architektur-Turnier (25.07) | D-010 | C (Roadmap, chat-only) | ADR-Entwurf MC-015 → ADR-022 |
| Cognitive Kernel Vorschlag (25.07) | D-011 | C (chat-only) | ADR-Entwurf ADR-023 |
| Agent Architecture Spec (30.07) | D-012 | C (chat-only) | ADR-Entwurf ADR-024 |
| Compiler Spezifikation (30.07) | D-013/D-014 | C (chat-only) | ADR-Entwurf ADR-025 (Abgrenzung zu D-013) |
| Benchmark Framework (29.07) | D-034 | C | Plan-Dokument in `docs/governance/` |
| SLM-Datenstrategie (29.07) | D-035 | C | Plan-Dokument |
| Closed-Source-Projektplan (23.07) | D-033 | C | Governance-Doku |
| Reality Closure Review (27.07) | D-030/D-031 | C | PROJECT_STATE-Anreicherung (E3.6) |
| Agenten-Orchestrierung (21.07) | D-032 | C | Strategie-Doku |

### 1.3 Priorisierung

| Prio | Item | Grund | Aufwand |
|------|------|-------|---------|
| P1 | Backfill S-2026-07-28/30/31-001 Handovers (aus Audit-Artefakten + S2) | Schließt Continuity-Lücke; Basis für alles andere (M3) | S |
| P2 | Registry-Verifikation: 18 Sessions ↔ 14 Handovers abgleichen | Aufdeckt weitere Lücken (z.B. S-2026-07-11-002 ohne Handover?) | S |
| P3 | Bridge-Handover (docs/bridge/handovers/) als eigene Kategorie klassifizieren + Referenz im SESSION_RULES | Format-Konflikt auflösen, kein Backfill nötig (automatisch erzeugt) | S |
| P4 | Chat→ADR-Entwürfe (1.2-Tabelle): je Chat 1 ADR-Entwurf + DECISION_REGISTRY-Verknüpfung | Knowledge Coverage M5 | M |

**Erfolgsmessung:** 3/3 Handovers backfilled, 0 Registry-Einträge ohne Handover-Referenz.

---

## 2. SESSION_RULES Konsolidierung

### 2.1 Aktuelle Autoritätskette (Ist-Zustand, 129 Zeilen)

| Prio | Dokument | Pfad | Problem |
|------|----------|------|---------|
| 1 | Project State | `docs/PROJECT_STATE.md` | ✅ aktuell (01.08) |
| 2 | Technical Baseline | `docs/TECHNICAL_BASELINE.md` | ⚠️ stale (12.07) |
| 3 | ADRs | `spec/ADR-*.md` | ⚠️ unvollständig (ADR-020/021 in docs/engineering/, ADR-API/EVENT/RUNTIME in spec/ADRs/) |
| 4 | Historical ADRs/RFCs | `archive/history/adrs/*`, `archive/history/rfcs/*` | ✅ Referenz |
| 5 | Architecture | `docs/ARCHITECTURE.md` | ⚠️ stale (12.07) |
| 6 | README | `README.md` | ⚠️ Inhalt prüfen |
| — | `docs/audit/` (MC-TC-002…007) | **NICHT in Kette** | ❌ neueste Wahrheit unerreichbar (SESSION_CONTINUITY_AUDIT M-1) |
| — | `docs/session_handovers/` | **NICHT in Kette** | ❌ Continuity-Quelle fehlt |
| — | `docs/engineering/D-*.md` | **NICHT in Kette** | ❌ E3.x-Entscheidungen unsichtbar |
| — | `docs/governance/` (ADR-014-Pläne, WORK_QUEUE…) | **NICHT in Kette** | ❌ teilweise |

### 2.2 Fehlende Informationen

1. **Audit-Lesepfad** — `docs/audit/MC-TC-*` als Quelle für den neuesten Zertifizierungsstand (ab 27.07 neueste Wahrheit).
2. **Session-Continuity-Pflicht** — Backfill-Anforderung: „Jede Session MIT Audit-/Cert-Artefakten MUSS SESSION_REGISTRY + ggf. Handover aktualisieren".
3. **TASK_BOARD-Verweis** — SESSION_RULES referenziert `docs/TASK_BOARD.md`; Datei existiert nicht (nur `docs/governance/ACTIVE_TASKS.md`/`WORK_QUEUE.md`) → toter Link.
4. **AGENTS.md-Migrationshinweis** — verweist auf SESSION_RULES, „nach der nächsten Migration ersetzt" → Migration abschließen (AGENTS.md = kurze Zusammenfassung, SESSION_RULES = vollständige Regeln; Status klären).
5. **Hook/Guards-Referenz** — Pre-Commit-Hook + OVERRIDE-052-Prozess ist in SESSION_RULES nicht beschrieben.
6. **Verifikations-Framework** — Abschnitt verweist auf `docs/VERIFICATION_FRAMEWORK_PLAN.md` etc.; Existenz prüfen.

### 2.3 Zielstruktur (Vorschlag)

```
# MUSCAL CORE — OpenCode Session Rules (v2.0, Phase-B-Version)
1. Projektstatus      → docs/PROJECT_STATE.md              (Prio 1)
2. Zertifizierungsstand → docs/audit/MC-TC-*.md             (Prio 2 NEU — neueste Wahrheit)
3. Technische Baseline  → docs/TECHNICAL_BASELINE.md        (Prio 3)
4. ADRs (kanonisch)     → spec/ADR-*.md + spec/ADRs/        (Prio 4, konsolidiert nach §3)
5. Engineering-Entscheidungen → docs/engineering/D-*.md     (Prio 5 NEU)
6. Historische ADRs/RFCs → archive/history/adrs|rfcs        (Prio 6, Referenz)
7. Architektur          → docs/ARCHITECTURE.md             (Prio 7)
8. README               → README.md                        (Prio 8)
# Session-Continuity-Abschnitt (NEU)
  - SESSION_REGISTRY-Pflicht, Handover-Format, Backfill-Regel
# Governance-Referenz (NEU)
  - Pre-Commit-Hook, OVERRIDE.md-Registry, OVERRIDE-052-Pfad, DECISION_REGISTRY
# Fehlerbehebung
  - TASK_BOARD-Verweis → docs/governance/ACTIVE_TASKS.md/WORK_QUEUE.md
  - AGENTS.md-Migrationsstatus klären
```

---

## 3. ADR-Konsolidierung

### 3.1 Bestandsaufnahme (4+1 Standorte)

| Standort | Inhalt | Status |
|----------|--------|--------|
| `spec/ADR-001..014` (15 Dateien + INDEX) | Kanonische Entscheidungen ADR-001…014 | **KANONISCH** |
| `spec/ADRs/` (3 Dateien) | ADR-API-001, ADR-EVENT-001, ADR-RUNTIME-001 | ❌ Duplikat-Container (Phase-1A-Wave, committet 1c4a1e7) |
| `specs/adrs/` (1 Datei) | IMPLEMENTATION_STATUS.md | ❌ toter Ordner (leerer Adressat) |
| `archive/history/adrs/` (6 Dateien) | ADR-001…006 (historische Versionen) | ✅ Referenz |
| `docs/engineering/` (ADR-020, ADR-021) | Pipeline-Stages, Agent-Detection | ❌ außerhalb der Kette |

### 3.2 Aktive vs historische ADRs

| Kategorie | ADRs | Hinweis |
|-----------|------|---------|
| **Aktiv (kanonisch)** | ADR-001…012, ADR-014 (ACCEPTED) | ADR-007 Core Immutability — Kern der Governance |
| **Aktiv, falsch platziert** | ADR-020, ADR-021 (docs/engineering/), ADR-API-001, ADR-EVENT-001, ADR-RUNTIME-001 (spec/ADRs/) | Verschieben/verlinken nach kanonischem Schema |
| **Historisch** | ADR-001…006 in archive/history/ (Vorgängerversionen) | Referenz, keine Autorität |
| **Superseded** | ADR-013 (Feature Plugin Migration Path — SUPERSEDED by ADR-007) | ✅ Index korrekt, Datei-Hinweis ergänzt (a39f545) |
| **Fehlbezeichnet (behoben)** | ADR-013-pipeline.md (war ADR-007-Inhalt) | ✅ fixiert (d5f5ce7) |

### 3.3 Duplikate

| Duplikat | Quelle | Aktion |
|----------|--------|--------|
| ADR-013/ADR-007 (Inhalt) | spec/ADR-013-pipeline.md vs ADR-007-immutability.md | ✅ bereinigt; historischen Verweis im INDEX belassen |
| ADR-API/EVENT/RUNTIME-001 | spec/ADRs/ (3 Dateien) | **Konsolidierung:** in ADR-INDEX aufnehmen ODER nach `spec/ADR-015…017` umbenennen; nur EIN Standort |
| specs/adrs/IMPLEMENTATION_STATUS.md | verwaister Ordner | Status klären (Inhalt prüfen → Inhalt übertragen, Ordner als Referenz markieren) |
| ADR-014-IMPLEMENTATION_PLAN_v1.0/v1.1 | docs/governance/ | bewusst (Plan vs ADR), v1.0 als superseded markieren |

### 3.4 Supersession Mapping (Ziel-Übersicht)

```
ADR-013 (Feature Plugin Migration Path, historisch)
  └─ SUPERSEDED BY → ADR-007 (Core Immutability — Write Guard Policy)

ADR-001 (Kernel Pipeline Authority)
  └─ erweitert durch → ADR-005 (Pipeline Architecture), ADR-021 (Agent Detection)

ADR-010 (SQLite Consolidation)
  └─ erweitert durch → ADR-012 (Event Persistence), ADR-EVENT-001 (EventStore Boundary)

ADR-014 (Unified Tool Runtime) ACCEPTED
  └─ erweitert durch → ADR-API-001 (Dual Runtime), ADR-RUNTIME-001 (SUPL Ownership)

[Phase B neu] ADR-022 (MC-015 MUSCAL 2.0) ← Turnier-Chat D-010
[Phase B neu] ADR-023 (Cognitive Kernel) ← D-011
[Phase B neu] ADR-024 (Agent Architecture Spec) ← D-012
[Phase B neu] ADR-025 (Cognitive Compiler Spec) ← D-013/D-014
```

---

## 4. Knowledge Foundation Integration

### 4.1 Audit-Artefakte → 20-Doc-Plan Zuordnung

| Audit-Artefakt (KNOWLEDGE_FOUNDATION/audit/) | Fließt ein in (20-Doc-Plan) | Beitrag |
|----------------------------------------------|------------------------------|--------|
| AUDIT_SCOPE.md | Doc 01 (Overview), Methodik | Scope + Confidence-Modell |
| REPOSITORY_CENSUS.md | Doc 02 (Repository Index) | Basis-Inventar |
| SOURCE_OF_TRUTH_MAP.md | Doc 03 (Source-of-Truth Map) | Autoritätsmatrix + Staleness |
| CONCEPT_EVOLUTION_MAP.md | Doc 11 (Temporal Analysis) | Konzept-Entwicklung |
| REFERENCE_GRAPH.md | Doc 04 (Knowledge Graph) | Node/Edge-Modell (~120 Knoten) |
| CHAT_CODE_DOC_RECONCILIATION.md | Doc 06 (Chat-Code-Doc Reconciliation) | 43 Chats, 20 Claims |
| TECHNICAL_MANUAL_CONFLICT_REPORT.md | Doc 07 (Manual Conflict) | 3-Wege-Diff |
| DECISION_REGISTRY.md | Doc 05 (Decision Registry) | D-001…D-042 |
| SESSION_CONTINUITY_AUDIT.md | Doc 09 (Session Continuity) | Rekonstruktions-Score |
| MASTER_INDEX.md | Doc 00 (Master Index) | Metriken + Findings |
| PHASE_A_REMEDIATION_PLAN.md / G2_* | Doc 08 (Remediation Log) | Governance-Historie |
| FL01A_FLAKINESS_REGISTER.md (in-repo) | Doc 10 (Test Governance) | Flakiness-Register |

### 4.2 In-Repo-Artefakte → 20-Doc-Plan

| In-Repo | Beitrag |
|---------|---------|
| docs/audit/MC-TC-002…007 | Doc 09 (Certification Status) — Wahrheitsquelle |
| docs/engineering/D-E3.x-* | Doc 05 (Engineering Decisions) |
| spec/OVERRIDE.md (rekonstruiert) | Doc 08 (Override Registry) |
| docs/governance/ (ACTIVE_TASKS, WORK_QUEUE…) | Doc 12 (Governance Ops) |

### 4.3 Vorgehen

1. Phase B schließt die in §1–3 identifizierten Lücken (Backfill, ADR, SESSION_RULES).
2. 20-Doc-Plan startet ERST nach Readiness >75 (Gate gemäß MASTER_INDEX §4).
3. Audit-Dokumente sind dann „validierte Quellen" — keine Duplikation, Referenzierung.

---

## 5. Risiken

| # | Risiko | Beschreibung | Gegenmaßnahme | Restrisiko |
|---|--------|--------------|---------------|------------|
| R1 | **Governance Drift** | SESSION_RULES bleibt 2 Wochen hinter der Realität; neue Sessions lesen alte Kette | §2.3 Zielstruktur als Pflicht-Lesepfad; CI-Check (SESSION_RULES-Referenzen auf Existenz testen) | LOW |
| R2 | **Source-of-Truth-Konflikte** | docs/audit/ (neueste Wahrheit) vs PROJECT_STATE vs TECHNICAL_BASELINE | §2.3 Prio-2-Einstufung + Staleness-Regel („bei Konflikt: MC-TC > PROJECT_STATE > Baseline") | LOW |
| R3 | **Historische Entscheidungen ohne ADR** | EventStore (nur ADR-EVENT-001 in spec/ADRs/), v0.8 (kein ADR-015+), MC-015/Cognitive-Kernel/Chat-Entscheidungen chat-only | §1.2 ADR-Entwürfe (ADR-022…025) + DECISION_REGISTRY-Backfill | MEDIUM (Zeitaufwand) |
| R4 | **ADR-Duplikat-Chaos** | 4+1 Standorte; ADR-020/021 außerhalb; specs/adrs/-Leiche | §3.3/3.4 Konsolidierung mit einem kanonischen Standort | LOW |
| R5 | **Handover-Lücke wiederholt sich** | Governance-Pflichten ohne Durchsetzung (29 M-Dateien-Fall war Folge davon) | §2.3 Session-Continuity-Pflicht; Pre-Commit-Hook-Erweiterung (Registry-Check) als Phase-B-Option | MEDIUM |
| R6 | **Flakiness-Blockade** | 19 flaky Tests → CI-Wiederholbarkeit; Baseline-Rekalibrierung könnte wieder driften | FL-01a-Fix (Fixtures) in Phase B aufnehmen; Recalibrierungs-Dokumentation (470er-Baseline als Referenz) | MEDIUM |

---

## 6. Erfolgskriterien (Definition of Done Phase B)

| Kriterium | Zielwert | Messung |
|-----------|----------|---------|
| **Session Continuity (M3)** | **>75** (aktuell 55) | SESSION_CONTINUITY_AUDIT re-run: Rekonstruktions-Score je Ziel >75; 3/3 Backfill-Handovers vorhanden; Registry ↔ Handover-Abgleich 0 Lücken |
| **Source-of-Truth eindeutig** | 1 Autorität je Domäne, kein Konflikt | SOURCE_OF_TRUTH_MAP re-run: 7 Domänen je genau 1 Autorität; Konfliktliste (D-017…) geschlossen oder explizit delegiert |
| **ADR-Struktur eindeutig** | 1 kanonischer Standort, 0 Duplikate, Supersession-Kette vollständig | §3.4-Mapping 100% im ADR-INDEX; specs/adrs/-Leiche aufgelöst; ADR-020/021 integriert; ADR-022…025 (oder PENDING-Marker) vorhanden |
| **Mission-Control Readiness** | **>75** (aktuell 61) | Metriken M1–M5 neu berechnet (M3 ≥75 zwingend, M5 ≥70, M2 ≥80, M1 ≥80, M4 ≥70) |
| Zusatz: Governance-Kette getestet | SESSION_RULES-Zielstruktur verifiziert (Existenz aller referenzierten Dokumente) | Script-Check: 100% Referenzen auflösbar |
| Zusatz: Flakiness dokumentiert | FL-01a-Register aktuell; Fix-Entscheidung (D-040/D-042) als Phase-B-Item | Register + ADR-022-Referenz |

**Gate nach Phase B:** Re-Messung aller 5 Metriken + dieser Checkliste → bei ≥75: Freigabe für 20-Doc-Plan (Knowledge Foundation Integration §4).

---

## Anhang: Empfohlene Phase-B-Arbeitsschritte (Reihenfolge, je Artefakt)

1. **PB-01** Handover-Backfill (3 Handovers aus Audit-Artefakten + S2-Chats) → `docs/session_handovers/` + SESSION_REGISTRY + Commit
2. **PB-02** SESSION_RULES v2.0 (Zielstruktur §2.3) + TASK_BOARD-Verweis-Fix + AGENTS.md-Migrationsabschluss
3. **PB-03** ADR-Konsolidierung (§3.3/3.4): INDEX-Erweiterung, ADR-020/021-Integration, specs/adrs/-Auflösung, ADR-014-IMPLEMENTATION_PLAN_v1.0 als superseded markieren
4. **PB-04** Chat→ADR-Entwürfe ADR-022…025 (PENDING-Status) + DECISION_REGISTRY-Verknüpfung
5. **PB-05** Re-Messung Metriken + SOURCE_OF_TRUTH_MAP/SESSION_CONTINUITY_AUDIT re-run
6. **PB-06** Readiness-Gate-Report (>75?) → Freigabe 20-Doc-Plan

*Aufwandsschätzung: PB-01 S · PB-02 S · PB-03 M · PB-04 M · PB-05 S · PB-06 S. Alles DOC/GOV-Klasse — keine Code-Änderungen.*

---

*Plan erstellt 2026-08-01 (read-only, keine Ausführung). Evidenz: SESSION_RULES.md (129 Z.), Handover-Inventar (14), SESSION_REGISTRY (18 Sessions), ADR-Inventar (5 Standorte), DECISION_REGISTRY D-010…D-035, G2_EXECUTION_VALIDATION_REPORT §4.*
