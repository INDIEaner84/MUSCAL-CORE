# KF5_IMPLEMENTATION_READINESS_MAP

- Datum: 02.08.2026
- Zweck: Implementierungs-Readiness-Analyse für alle offenen Entscheidungen (RC-1a, RC-1b, RC-2, RC-4a, RC-5) + Implementierungs-Szenarien je RC (Optionen A/B/C, **keine Auswahl**) — read-only; keine Implementierung, keine Codeänderung, keine Commit-Erzeugung, keine Entscheidung
- Basis: RC1_FINAL_DECISION_BRIEF.md, RC2_HDR001_FINAL_DECISION_BRIEF.md, ADR_REVIEW_PACKET.md, KF3_DECISION_QUEUE.md, DECISION_CLOSURE_PACKAGE.md, G7-01/G7-02, DECISION_REGISTRY (D-001…D-042), 05/16/18-Foundation-Dokumente, SESSION_RULES v2.0, Code-Befunde (ReplayService, EventStoreAdapter, execution_watchdog.py, graph.py, features/-Inventar)
- Status: **created, not committed (external KF layer)**

---

## 1. Methodik

- Status/Aussagen nur mit Quelle (C0/C1/C2 wie in Quellen belegt).
- Code-Befunde mit Datei:Zeile belegt; Kern-Evidenz: `features/replay/replay_service.py` (ReplayService: replay_all/replay_topic/replay_since), `features/events/event_adapter.py:75-85` (EventStoreAdapter.append_writer_event → EventStore.append), `features/monitoring/execution_watchdog.py:96-119` (nur publish), `graph.py:45ff` (GraphState, CORE/immutable), `features/supl/graph_boundary.py` (SUPL-Node-/Edge-Typen).
- Constraint: **D-006** — alle Erweiterungen als Plugins in `features/`; Core (graph.py etc.) IMMUTABLE (SESSION_RULES v2.0; IMMUTABILITY_CONTRACT); Verletzung → ARCHITECTURE CHANGE + OVERRIDE-Pfad (D-020).

## 2. RC-1a — Graph-OS Persistence/Reconstruction (P0-1)

### 2.1 Current Implementation State

| Aspekt | Befund | Quelle |
|--------|--------|--------|
| GraphState | in-memory: `nodes: dict`, `edges: list`, `_node_counter`, `active_focus_node`, `_update_stream`; Events via `_push_event(EVENT_NODE_CREATED/EDGE_CREATED/…)` | graph.py:45ff (C0) |
| Persistenz | Graph-Events (NODE_CREATED, EDGE_CREATED …) WERDEN in `stored_events` persistiert (EventStore-Layer) | MC-TC-007_STATUS_ZUSAMMENFASSUNG.md:67 (C0) |
| Rücklese-/Rebuild-Code | **existiert nicht** — kein Code, der Graph-Events zurückliest | MC-TC-007 Phase H ❌ FAIL (C0); DECISION_CLOSURE_PACKAGE §RC-1 |
| Replay-Infrastruktur | `features/replay/replay_service.py` (ReplayService.replay_all/replay_topic/replay_since) vorhanden, zertifiziert (MC-TC-006, deterministisch) | Code (C0); MC-TC-006 (C1) |
| Boot | Boot-Wiring nur `features/boot/utr_wiring.py`; Boot-Matrix „Phase K" ist dokumentiert (MC-TC-007-Cert §Phase K, 6 Boot-Pfade), **kein Boot-Phasen-Rebuild-Code im Repo** | Code-Inventar (C0); MC-TC-007-Cert (C1) |
| Core-Grenze | graph.py = CORE, IMMUTABLE — kein Core-Write erlaubt; Rebuild nur via public GraphState-API (add_node/update_node/add_edge) oder Boundary-Layer | SESSION_RULES v2.0; IMMUTABILITY_CONTRACT (C0) |

### 2.2 Missing Components

| Fehlende Komponente | Funktion | Platzierung (D-006) | Bezug |
|---------------------|----------|---------------------|-------|
| Graph-Rebuild-Service | stored_events → GraphState-Rekonstruktion beim Boot | neues Plugin `features/graph_rebuild/` (Vorschlag, nicht gewählt) | G7-01 P0-1 Option A |
| Boot-Phasen-Integration | Anbindung an Boot-Matrix Phase K (Reihenfolge: DB/EventStore → Replay → Rebuild → Restore) | `features/boot/` (Erweiterung) | G7-01 Option A; MC-TC-007-Cert §Phase K |
| Event-Mapping | Graph-Events → GraphState-API (Topic-Mapping NODE_CREATED/EDGE_CREATED/NODE_UPDATED → add_node/update_node/add_edge) | Rebuild-Service selbst | graph.py:77/124; features/supl/graph_boundary.py |
| Rekonstruktions-Validierung | Rebuild-Ergebnis vs. Event-Log (Anzahl Knoten/Kanten, Reihenfolge) | Test-Suite | MC-TC-006-Replay-Matrix (C1) |
| Freeze-Korrektur-Doku | GRAPH_OS_ARCHITECTURE_FREEZE v1.0 „ALL P0 BLOCKERS RESOLVED" Widerspruch auflösen (bei jeder Option) | docs/audit + PROJECT_STATE | G7-01; MC-TC-007 (C0) |

### 2.3 Dependencies

- EventStore/`stored_events`-Topic-Struktur (MC-TC-004 zertifiziert: 33/33, 431/431 Tests) — Rebuild liest daraus (D-008: EventBus/EventStore/AuditLog nicht verschmelzen).
- ReplayService als Basis oder Analogie (MC-TC-006: Replay deterministisch).
- D-006 (features/-Pflicht), D-020 (Core-Immutability; bei Annäherung an Core → ARCHITECTURE CHANGE-Deklaration).
- RC-6: RC-1a-Entscheidung ist Mess-Voraussetzung (notwendig, nicht hinreichend) (§RC-6-M4; KF3-H-1).
- RC-1-Option D: ADR-022 (MUSCAL 2.0) als Roadmap-Aufnahme (G7-01).

### 2.4 Estimated Implementation Impact

| Option (G7-01) | Impact | Aufwand (Quelle) |
|----------------|--------|-------------------|
| A (Rebuild-Service) | neues Plugin; Boot-Integration; Rebuild-Tests; Baseline-Erweiterung; FL-01a-Fläche wächst (eigene Fixtures) | M–L (DECISION_CLOSURE_PACKAGE §RC-1; ohne Zeitplan-Bindung) |
| B (DEFERRED + Watchdog-Fix) | nur Doku/Governance + P0-2-Teil | S–M |
| C (Scope-Boundary) | ADR-Dokumentation + PROJECT_STATE-Update; kein Code | S |
| D (Roadmap-Item) | Freeze v1.0 → DEPRECATED; ADR-022-Referenz; kein Code heute | S |

### 2.5 Files Affected

| Datei | Typ | Änderungsart (je Option) |
|-------|-----|---------------------------|
| features/graph_rebuild/* (neu, nur Option A) | Feature | neu |
| features/boot/utr_wiring.py | Feature | Option A: Boot-Reihenfolge erweitern (oder neues Boot-Modul) |
| graph.py | CORE | **nicht anfassen** (IMMUTABLE); nur public API konsumieren |
| features/monitoring/execution_watchdog.py | Feature | Option B: P0-2-Teil (siehe RC-1b) |
| spec/ADR-022-muscal2-hybrid.md | Doku | Option D: Rebuild-Item-Aufnahme |
| GRAPH_OS_ARCHITECTURE_FREEZE_v1.0.md, PROJECT_STATE.md, DECISION_REGISTRY | Doku | alle Optionen: Freeze-Widerspruch/Status |
| docs/audit/MC-TC-007-* | Doku | Phase H-Befund-Aktualisierung nach Umsetzung |

### 2.6 Tests Affected

- Neu (Option A): Rebuild-Tests (Replay→Rekonstruktion), Boot-Integrationstests, Konsistenz (Log vs. Graph), FL-01a-Fixtures.
- Betroffen (Option A): tests/test_graph.py (32 Testfunktionen) — Regression durch Rebuild-Pfad; tests/supl/test_gate1_production_wiring.py, tests/supl/test_supl_event_integration.py (Boot-Wiring).
- Baseline: 470 (D-041, EXPECTED_TOTAL) — Erweiterung nur mit dokumentierter Kalibrierung; MC-TC-007 Phase L-Stand 384/384 als Regressionsbasis.

### 2.7 Rollback Complexity

| Option | Rollback |
|--------|----------|
| A | niedrig–mittel: Plugin-Dir entfernen (D-006-Pfad), Boot-Wiring entkoppeln; keine Core-Änderung → kein Core-Rollback |
| B/C/D | trivial (Doku-Commits reversibel) |

## 3. RC-1b — Watchdog EventStore Persistence (P0-2)

### 3.1 Current Implementation State

| Aspekt | Befund | Quelle |
|--------|--------|--------|
| Watchdog | `ExecutionWatchdog._force_fail_orphan()` publiziert nur `EXECUTION_FAILED` via `event_bus.publish(...)`; kein `EventStore.append()` | features/monitoring/execution_watchdog.py:96-119 (C0) |
| Status | MC-TC-007 Phase F ⚠️ PASS* (Stern = Persistenzlücke) | MC-TC-007_STATUS_ZUSAMMENFASSUNG.md:71-76 (C0) |
| Folge-Finding | C03: derselbe Orphan wird mehrfach erkannt (keine Dedup-Persistenz) | G7-01 (C1) |
| Persistenz-Infrastruktur | `features/events/event_adapter.py:75-85` EventStoreAdapter (writer_to_eventstore → EventStore.append, seq-Rückgabe) vorhanden | Code (C0) |
| Core-Grenze | features/monitoring/ ist NICHT CORE (G7-01; D-006-konform) | G7-01 (C0) |

### 3.2 Missing Components

| Fehlende Komponente | Funktion | Platzierung |
|---------------------|----------|-------------|
| Watchdog→EventStore-Rückkanal | EXECUTION_FAILED zusätzlich über EventStore.append() persistieren (via EventStoreAdapter) | features/monitoring/execution_watchdog.py (Erweiterung) |
| Dedup-Marker (Option B) | Dedup-Semantik im EventStore (C03-Fix) | EventStore-Topic/Marker-Feld + Watchdog-Check |
| Audit-only-Kanal (Option D) | Watchdog-Erkennungen in eigenes Audit-Log (außerhalb EventStore) | features/monitoring/ |
| Replay-Matrix-Prüfung | Event-Doppelpersistenz-Risiko gegen MC-TC-006-Matrix bewerten (vor Option A/B) | Test-/Prüf-Artefakt |

### 3.3 Dependencies

- EventStore.append-Signatur (D-009: verifiziert vor Integration; Bridge-Callback-Mismatch-Historie).
- EventBus/EventStore/AuditLog-Trennung (D-008) — Watchdog-Persistenz muss in EventStore, nicht AuditLog.
- MC-TC-006-Replay-Matrix (Replay-Determinismus; neue Events dürfen Replay nicht brechen).
- D-006 (features/-Pflicht — erfüllt, features/monitoring/ ist Feature).
- RC-6 (Mess-Voraussetzung, wie RC-1a).

### 3.4 Estimated Implementation Impact

| Option (G7-01) | Impact | Aufwand (Quelle) |
|----------------|--------|-------------------|
| A (Persistenz) | 1 Datei erweitert; Persistenz-Tests; Baseline-Erweiterung | S (DECISION_CLOSURE_PACKAGE §RC-1) |
| B (Persistenz+Dedup) | wie A + Dedup-Semantik + Dedup-Test (C03) | S–M |
| C (DEFERRED) | DEFERRED-Markierung; keine Code-Änderung | S |
| D (Audit-only) | Audit-Kanal + Format-Tests | S (Feature-lite) |

### 3.5 Files Affected

| Datei | Typ | Änderungsart |
|-------|-----|--------------|
| features/monitoring/execution_watchdog.py:96-119 | Feature | Option A/B: zusätzlicher append; Option D: Audit-Schreibpfad |
| features/events/event_adapter.py | Feature | ggf. Wiederverwendung (keine Änderung nötig, vorhandener Adapter) |
| Test-Dateien (Watchdog/Persistenz) | Test | neue Tests (Persistenz, Dedup, Audit-Format) |
| DECISION_REGISTRY / ADR-Record | Doku | Option B: „ADR-042-ähnliches Record" (G7-01) |
| MC-TC-007-Doku | Doku | F→voll PASS dokumentieren (Option A/B) |

### 3.6 Tests Affected

- Neu: Persistenz-Tests (Event im stored_events nach Orphan-Fail), Dedup-Test (C03), Audit-Format-Tests (Option D).
- Betroffen: tests mit Watchdog-Bezug (test_phase1c_e2e_reality_integrity.py, test_phase1a_canonical_event.py, test_phase1b_execution_context.py, tests/supl/test_gate1_production_wiring.py, tests/supl/test_supl_event_integration.py).
- Replay-Regression: MC-TC-006-Suite (neue Topic-Daten müssen deterministisch bleiben).

### 3.7 Rollback Complexity

- niedrig: 1 Feature-Datei + Tests; keine Core-Berührung; Revert ohne Seiteneffekte (D-006-Pfad).

## 4. RC-2 — HDR-001 Architecture Council

### 4.1 Current Implementation State

| Aspekt | Befund | Quelle |
|--------|--------|--------|
| Status | HUMAN REQUIRED; READY FOR HUMAN DECISION seit 20.07; HDR-002…004 blockiert (9 Dependencies) | HDR-001_DECISION_RECORD; PROJECT_STATE:116-119; D-023 |
| Code-Impact | **kein Code-Impact** — reine Governance-Entscheidung (Architecture Council = Gremium, kein Modul) | HDR-001_DECISION_RECORD §1 |

### 4.2 Missing Components (nach Entscheidung)

| Fehlende Komponente | Funktion |
|---------------------|----------|
| Projektleitungs-Eintrag: PROJECT_STATE-HDR-Tabelle → DECIDED | Status-Dokumentation (HDR-001_DECISION_RECORD §7) |
| DECISION_REGISTRY D-023-Update | „resolved" mit Entscheidungsdatum/Option |
| HDR-002…004-Startrampen | Agenten-Rollen (PMGA, Master Coding AI, Requirements) mit Evidence-Pflicht (C0/C1) — Option B-Auflagen |
| ggf. Arbeitsregeln/Checklisten für Folge-HDRs | Auflagen-Katalog (Option B) |

### 4.3 Dependencies

- D-023 (Registry), PROJECT_STATE (Prio 1), SESSION_RULES-Autoritätskette (D-022/D-025).
- M2-Eingangsgröße HDR-001-Status (18_METRIC_REGISTRY §2 M2; §RC-6-M2).
- RC-6 (Mess-Voraussetzung).
- Kein Code-/Test-/Architektur-Impact (keine Dateien im Kernel/features betroffen).

### 4.4 Estimated Implementation Impact

- Nur Dokumentation/Governance: PROJECT_STATE (1 Tabelle), Registry (1 Eintrag), ggf. neue Agenten-Rollen-Doku. Aufwand: S (Doku-only). Keine Test-Auswirkung.

### 4.5 Files Affected

| Datei | Änderungsart |
|-------|--------------|
| docs/PROJECT_STATE.md (HDR-Tabelle) | Status → DECIDED |
| KNOWLEDGE_FOUNDATION/audit/DECISION_REGISTRY.md (D-023) | Update |
| docs/SESSION_RULES.md bzw. .opencode/SESSION_RULES.md | ggf. HDR-Rollen-Autorität (nur bei Option A/B mit Auflagen) |
| docs/governance/HDR-001_DECISION_RECORD.md | Entscheidungs-Eintrag (durch Human/ARB) |

### 4.6 Rollback Complexity

- trivial (Doku-Commits); Governance-Statusänderungen dokumentiert reversibel.

## 5. RC-4a — ADR-022…025 Review

### 5.1 Current Implementation State

| Aspekt | Befund | Quelle |
|--------|--------|--------|
| ADR-Dateien | spec/ADR-022…025 (PROPOSED/DRAFT, committet a977091) | Code/Doku (C0) |
| Status | NICHT GESTARTET; NOT READY (Turnier-Primärquelle fehlt; Migrationsbewertung fehlt; Security Model; Trust-Governance-Interaktion; RFC-Process) | DECISION_CLOSURE_PACKAGE §RC-4; KF3-M-4 |
| Basis-Entscheidungen | D-010…D-014: PLANNED, CHAT_ONLY, C2 — unverändert | 05_DECISION_REGISTRY §A |
| Review-Struktur | ADR_REVIEW_MATRIX (G7-03) mit Prüfmatrix + Review-Protokoll | ADR_REVIEW_MATRIX.md (lesbar, 57 Z.) |
| Architektur-Bezug | ADR-001 APPLIED (Single Pipeline Authority) — Konflikt D-010 vs D-001 (Migrationspfad, MEDIUM) | ADR-022; 05_DECISION_REGISTRY |

### 5.2 Missing Components (Review-Input)

| Fehlend | für | Quelle |
|---------|-----|--------|
| Turnier-Primärquelle (MC-015-Chat 25.07) im Repo | ADR-022 (Treffer-Kriterien) | §RC-4; KF3-L-9 |
| Migrationsbewertung ADR-001→Hybrid | ADR-022 | §RC-4 |
| Sicherheitsmodell-Spezifikation (signed actions, Schlüsselverwaltung) | ADR-023 | §RC-4; KF3-M-4 |
| Trust-Governance-Interaktion (P5 vs Auto-Approve, NO-GO-Bezug) | ADR-024 | §RC-4; KF3-M-4; MC-TC-007-TRUST-GOVERNANCE |
| RFC-Process-Definition (Zuständigkeit/Format/Freigabe) | ADR-025 | §RC-4; KF3-M-4 |
| G6-01-Kategorien (Akzeptanzkriterien, Owner, Zeitplan, Budget, Rückwärtskompatibilität, Review-Prozess) je ADR | alle 4 | ADR_REVIEW_MATRIX |

### 5.3 Dependencies

- ADR-001/005/006 (ADR-022), ADR-014/008/ADR-EVENT-001 (ADR-023), ADR-021/022/007 (ADR-024), ADR-001/MPIR (ADR-025), D-030 (alle) — siehe ADR_REVIEW_PACKET.md.
- G6-01 (formal 6/6-Vollständigkeit), G7-03 (Matrix), G4.5-B2 (keine Auto-Akzeptierung).
- Kein Code-Impact bis ACCEPTED-Status (dann Folge-Dokumente/Architektur-Docs Doc 04/14-DRAFT-Knoten).

### 5.4 Estimated Implementation Impact

| Status-Ausgang (durch ARB) | Impact |
|----------------------------|--------|
| PROPOSED-final | kein Code; ADR-INDEX/Datei-Statusupdate |
| DEPRECATED | kein Code; Supersession-Doku |
| ACCEPTED | Folge-Architektur-Dokumente (Doc 04/14), ADR-INDEX, PROJECT_STATE; M4-K2-Wirkung bei Re-Messung; Design-Arbeit erst in Planung (MUSCAL 2.0) |

### 5.5 Files Affected (nach Review, abhängig vom ARB-Urteil)

| Datei | Änderungsart |
|-------|--------------|
| spec/ADR-022…025.md | Status/Inhalt (nur durch Review-Instanz, ADR_REVIEW_MATRIX-Protokoll 4) |
| spec/ADR-INDEX.md | Status-Spiegel |
| docs/audit/ADR_REVIEW_MATRIX.md | Review-Ergebnis-Protokoll |
| PROJECT_STATE.md, DECISION_REGISTRY (D-010…D-014) | Status-Mirror (CHAT_ONLY-Markierung bleibt bis Repo-Beleg) |
| KNOWLEDGE_FOUNDATION (REFERENCE_GRAPH-DRAFT-Knoten, Doc 04/14) | Knoten-Status bei ACCEPTED |

### 5.6 Tests Affected

- Keine bis zur Umsetzung von MUSCAL-2.0-Designs; ACCEPTED erzeugt keinen Code → keine Teständerung; M4-K2-Wirkung nur über formale Re-Messung (keine Score-Berechnung hier).

### 5.7 Rollback Complexity

- Doku-Rollback trivial; bei ACCEPTED: ADR-Status-Revision dokumentiert möglich (D-018-Präzedenz: ADR-014 DRAFT→ACCEPTED über G2).

## 6. RC-5 — Documentation Consolidation

### 6.1 Current Implementation State

| Item | Befund | Quelle |
|------|--------|--------|
| F-03 specs/adrs/-Leiche | verwaister Ordner (IMPLEMENTATION_STATUS.md, Inhalt ungeprüft) | §RC-5; G6-01 |
| v0.8-Manual | fehlt (CHANGELOG_v0.8 existiert; kein Manual) | §RC-5; MASTER_INDEX TF-02 |
| D-033…D-035-Plan-Docs | PLANNED + CHAT_ONLY (C2), kein Repo-Artefakt, kein Plan-Doc | G6-04; 05_DECISION_REGISTRY §C |
| TC-H3-Supersession-Hinweise | PARTIAL (Rangfolge in TECHNICAL_MANUAL_AUTHORITY_MAP; Header-Hinweise fehlen in 3 Manuals) | §RC-5; TC_H3_CLOSURE |
| KIR-Repo-Status | = KG-01 (Wissenslücke, G7 §4) — kein RC-5-Punkt | KF3-M-3 |

### 6.2 Missing Components

| Fehlend | Funktion | Platzierung |
|---------|----------|-------------|
| F-03-Inhaltsprüfung | IMPLEMENTATION_STATUS.md prüfen → referenzieren oder Referenz-Markierung (keine Löschung) | docs/audit + docs/engineering-Schema |
| v0.8-Manual | Generierung aus Census/Reconciliation-Daten (verbindliche Zahlen; Implementiert/Geplant-Abgrenzung) | docs/ (Phase C, DOC) |
| D-033…035-Plan-Dokumente | je 1 Plan-Doc (Closed-Source, Benchmark, SLM-Datenstrategie) | docs/governance/ (Phase C, DOC) |
| TC-H3-Header-Hinweise | Rangfolge-Hinweise in 3 Manuals (Inhaltsänderung — außerhalb dieses Mandats) | Manuals (Phase C) |

### 6.3 Dependencies

- TECHNICAL_MANUAL_CONFLICT_REPORT (TC-Konflikte C1/C2/H1), TC_H3_CLOSURE (3 RESOLVED/2 PARTIAL/3 OPEN), REPOSITORY_CENSUS (1.209 Dateien, 611 py/77.376 LOC) als Zahlen-Basis.
- B5/B6 (v0.8/TC-H3-Klärung), G4.5 §7 (B1–B4 DOC-only).
- **Keine** automatische Abhängigkeit von RC-1 (KF3-M-2-Korrektur); kein Human-Entscheidungsbedarf (PLANNED + CHAT_ONLY bleibt).
- M4/M5-Eingangsgrößen (18_METRIC_REGISTRY §2 M4/M5) — Wirkung nur via formale Re-Messung.

### 6.4 Estimated Implementation Impact

- Doku-only (DOC-Klasse); Aufwand S–M je Item; keine Code-/Test-Änderung. v0.8-Manual: Generierung aus vorhandenen Daten (Census/Reconciliation), keine neuen Messungen.

### 6.5 Files Affected

| Datei | Änderungsart |
|-------|--------------|
| specs/adrs/IMPLEMENTATION_STATUS.md | prüfen → Referenz-Markierung oder docs/engineering-Referenz (keine Löschung) |
| docs/TECHNICAL_MANUAL_v0.8.md (neu) | Generierung |
| docs/governance/D-033_*PLAN.md, D-034_*PLAN.md, D-035_*PLAN.md (neu) | je Plan-Dokument |
| 3 Manual-Header (v0.5/v0.6/v0.7) | TC-H3-Rangfolge-Hinweise (Inhaltsänderung — außerhalb dieses Mandats) |
| 18_METRIC_REGISTRY, G6-04 | Referenz-Update (nicht Score) |

### 6.6 Tests Affected

- keine Code-Tests; nur Dokument-Validierungsprüfungen (v0.8-Zahlen vs. Census).

### 6.7 Rollback Complexity

- trivial (Doku-Commits; keine Löschung — F-03-Regel).

## 7. Implementierungs-Szenarien je RC (Task 3 — **keine Auswahl**)

Legende: A = Minimal change · B = Recommended engineering approach (neutral formuliert) · C = Long-term MUSCAL-Architektur.

### RC-1a (P0-1 Graph-OS)

| Sz. | Ansatz | Charakteristik | Risiko-Notiz |
|-----|--------|----------------|--------------|
| A | Freeze-Korrektur + DEFERRED-Dokumentation; nur Watchdog-Teil fixen | kein Rebuild-Code; Governance-Doku | Restart-Verlust bleibt (R1) |
| B | Rebuild-Service-Plugin (features/graph_rebuild/) auf Basis ReplayService + EventStoreAdapter; Boot-Phase-K-Anbindung; Rebuild-Tests + FL-01a-Fixtures | voller Rebuild-Pfad; erfüllt MC-TC-007 Phase H | Core-Immutabilität (graph.py nur via public API); Replay-Integration |
| C | Rebuild als MUSCAL-2.0-Item (ADR-022-Design); Freeze v1.0 → DEPRECATED; kein Code heute | Roadmap-Integration; Architektur-Kohärenz mit D-010-Hybrid | Verlust bis MUSCAL 2.0 akzeptiert |

### RC-1b (P0-2 Watchdog)

| Sz. | Ansatz | Charakteristik | Risiko-Notiz |
|-----|--------|----------------|--------------|
| A | `_force_fail_orphan()` zusätzlich EventStore.append (Option A) | minimaler Persistenz-Rückkanal | Event-Doppelpersistenz → MC-TC-006-Prüfung |
| B | Persistenz + Dedup-Marker in einem Schritt (Option B, adressiert C03) | kombiniert; einzige Option mit C03-Wirkung (Faktenlage G7-01) | Dedup-Semantik sorgfältig definieren |
| C | DEFERRED dokumentieren (Watchdog Session-only) | Governance-only | C03 bleibt; Alarme wiederholen sich |

### RC-2 (HDR-001)

| Sz. | Ansatz | Charakteristik | Risiko-Notiz |
|-----|--------|----------------|--------------|
| A | Annehmen ohne Auflagen (Option A) | Kette sofort voll aktiv | Auflagenlosigkeit ohne Review-Risiko (Record-Zitat) |
| B | Annehmen mit Auflagen (Option B: MC-TC-004-Bedingungen, Evidence-Pflicht C0/C1, P0-Frist) | kontrollierte Freigabe; Risk-arm (Record-Zitat) | Evidence-Pflicht = Doku-Aufwand |
| C | Ablehnen bis nach RC-1 (Option C) | Status quo; HDR-Deadlock hält | Governance-Verzögerung; M2-Rest bleibt |

### RC-4a (ADR-022…025)

| Sz. | Ansatz | Charakteristik | Risiko-Notiz |
|-----|--------|----------------|--------------|
| A | Review auf Basis vorhandener Dateien; Status-Empfehlung PROPOSED-final/DEPRECATED (keine Akzeptanz) | minimal; klärt M4-K2 | ungelöste Input-Lücken (Primärquelle etc.) bleiben dokumentiert |
| B | Review + Input-Vervollständigung (Primärquelle, Migrationsbewertung, Security Model, RFC-Process, Trust-Governance-Interaktion) → belastbare Status-Urteile | vollständiger Review-Pfad (KF3-M-4) | Input-Beschaffbarkeit (L-9: Klärung offen) |
| C | ADR-022…025 als Phase-B-Design-Rahmen für MUSCAL 2.0 (D-010…D-014-CHAT_ONLY bleibt) | Langfrist-Integration; keine Akzeptanz heute | unverbindliche Richtung bis Akzeptanz |

### RC-5 (Doku-Konsolidierung)

| Sz. | Ansatz | Charakteristik | Risiko-Notiz |
|-----|--------|----------------|--------------|
| A | F-03-Inhaltsprüfung + Referenz-Markierung; TC-H3-Header-Hinweise | kleinste Doku-Schritte | v0.8 bleibt fehlend |
| B | v0.8-Manual-Generierung aus Census/Reconciliation + D-033…035-Plan-Docs | vollständige M4/M5-Restbearbeitung (DOC-Klasse) | Zahlen-Konsistenz (Census) sicherstellen |
| C | Manual-Triple-Konsolidierung im MUSCAL-2.0-Manual-Rahmen (ADR-022-Bezug) | Langfrist-Kanon | außerhalb RC-6-Zyklus |

## 8. Cross-Cutting Constraints

| Constraint | Quelle |
|------------|--------|
| Keine Core-Änderung ohne ARCHITECTURE CHANGE + OVERRIDE-Pfad (D-006/D-020; `--allow-core-write`-Flag) | SESSION_RULES v2.0 |
| Pre-Write-Check: `guards.write_guard.validate_write(path)` vor jedem Schreibzugriff | AGENTS.md |
| Override-052-Registry (nur guards/**, .github/**, .pre-commit-config.yaml) | SESSION_RULES v2.0 |
| CHAT_ONLY bleibt CHAT_ONLY; PLANNED bleibt PLANNED (G6-04) | 05_DECISION_REGISTRY §F |
| Baseline 470 (D-041); Testzahlen nur mit verifizierter Quelle (TF-06-Kontradiktion beachten) | D-041; MASTER_INDEX TF-06 |
| Session-Handover-Pflicht bei jeder Session mit Änderungen (D-021) | SESSION_RULES v2.0 |

## 9. Validation

- Read-only: keine Implementierung, keine Empfehlungs-Auswahl (Szenarien A/B/C ohne Wahl), keine Entscheidung, keine Statusänderung, keine Score-Berechnung.
- Alle Aussagen mit Quelle; Code-Befunde mit Datei:Zeile; Aufwandsangaben (S/M/L) wörtlich aus DECISION_CLOSURE_PACKAGE §RC-1.
- Widerspruchsfrei zu KF3/KF4-Artefakten (M-2: D-033…035 ≠ RC-1; M-3: KIR = KG-01; H-1: RC-6-Mess-Gate).
