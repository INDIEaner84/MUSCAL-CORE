# 16 — Blocker Registry Foundation

- Datum: 02.08.2026
- Typ: Foundation-Dokument (read-only; keine Priorität neu erfunden, keine Statusänderung)
- Quellen: G4_DECISION_GATE (B1…B7, G4.5), G5_FINAL_READINESS_REPORT (RC-1…RC-3, R1…R3), DECISION_CLOSURE_PACKAGE (RC-1…RC-6), ADR_REVIEW_MATRIX (G7-03), PROJECT_STATE (P0-1/P0-2, 01.08), HDR-001_DECISION_RECORD, FL01A_FLAKINESS_REGISTER, GLOBAL_STATE_ARCHITECTURE_DECISION_DRAFT, G7-01/G7-02, KF1_COMPLETION_AUDIT

## 1 Purpose

Vollständige, quellenpflichtige Registrierung aller aktuellen Projekt-Blocker (B1…B7, RC-1…RC-6, P0-1, P0-2, HDR-001, FL-01a) mit Status, Owner, Blocker-Typ, Evidence und Wirkung. Status wörtlich aus Quellen übernommen; keine Neubewertung.

## 2 Scope

- Aufgenommen: alle Blocker mit Quelle (Gate-Bedingungen B1…B7; Release-Blocker RC-1…RC-6; P0-1/P0-2; HDR-001; FL-01a).
- Nicht aufgenommen: bereits erledigte Bedingungen ohne Restwirkung (B1/B2); Details ohne Statusrelevanz.

## 3 Blocker Model

- **Typen (aus Quellen, nicht neu definiert):** Entscheidung (Human/ARB), Freigabe (ARB), Dokumentation (DOC), Fix (Test).
- **Owner (belegt):** B1–B4 DOC/Governance-Konsolidierung; B5/B7 ARB; B6 Human (G4.5 §7). RC-1 ARB; RC-2 Human; RC-3 ARB/DOC (G5 §RC).
- **Status-Vokabular (wörtlich):** PENDING HUMAN, HUMAN REQUIRED, NOT STARTED, offen, Deferred, NOT READY, ausstehend.

## 4 Gate-Bedingungen B1…B7 (G4.5)

| ID | Bedingung | Status (unverändert) | Owner | Typ | Evidence |
|---|---|---|---|---|---|
| B1 | ADR-INDEX: ADR-014 ACCEPTED; ADR-013-Supersession konsistent | erledigt | DOC | Doku | G4.5 B1; ADR_CANONICAL_MAP F-01 |
| B2 | 5 ADRs in INDEX (ADR-API-001, ADR-EVENT-001, ADR-RUNTIME-001, ADR-020, ADR-021) | erledigt | DOC | Doku | G4.5 B2; ADR_CANONICAL_MAP F-02 |
| B3 | ADR-022…025-Entwürfe (PENDING→DRAFT) + D-033…D-035-Plan-Dokumente | teilweise: ADR-Entwürfe DRAFT im Repo (PB-04, a977091); Plan-Docs offen | DOC/ARB | Doku/Entscheidung | ADR_REVIEW_MATRIX (DRAFT), G7-01 (Plan-Docs hängen an P0-Entscheidung) |
| B4 | Manuals-Triple konsolidieren + specs/adrs/-Leiche (F-03) auflösen | offen | DOC | Doku | G4.5 B4; F-03 (G6-01); TC-H3 → RC-5 |
| B5 | P0-1 (Graph-OS) / P0-2 (Watchdog) — Option wählen oder ARCHITECTURE CHANGE deklarieren | **PENDING HUMAN** | ARB | Entscheidung | G4.5 B5; PROJECT_STATE 01.08; G7-01 (Optionen A–D) |
| B6 | HDR-001 Human Decision | **HUMAN REQUIRED** | Human | Entscheidung | G4.5 B6; HDR-001 (20.07); G7-02 (Optionen A–D) |
| B7 | FL-01a-Fix-Entscheidung (D-040/D-042) | Deferred → Fix/Freigabe offen | ARB | Fix/Freigabe | G4.5 B7; GLOBAL_STATE_ARCHITECTURE_DECISION_DRAFT |

## 5 Release-Blocker RC-1…RC-6

| ID | Blocker | Status | Owner | Typ | Evidence | Blockiert |
|---|---|---|---|---|---|---|
| RC-1 | P0-1/P0-2-Entscheidung (B5) | PENDING HUMAN | ARB | Entscheidung | PROJECT_STATE 01.08, G7-01 (Optionen A–D), DECISION_CLOSURE_PACKAGE §RC-1 | D-033…D-035-Plan-Docs; Doc 15/16-Statusfestlegung P0; M4-Re-Messung (RC-6) |
| RC-2 | HDR-001 Human Decision (B6) | HUMAN REQUIRED | Human | Entscheidung | G7-02 (Optionen A–D), DECISION_CLOSURE_PACKAGE §RC-2 | HDR-002…004 (3 HDRs seit 20.07); M4-Re-Messung (RC-6) |
| RC-3 | FL-01a-Fix + Global-State-ADR (D-042) | Freigabe offen (kein ACCEPTED) | ARB/DOC | Freigabe | FL01A_FLAKINESS_REGISTER, GLOBAL_STATE_ARCHITECTURE_DECISION_DRAFT, G5 RC-3 | Baseline-Stabilität (19 flaky / 2.343…2.347) |
| RC-4a | ADR-022…025-Readiness-Review | **NICHT GESTARTET** | ARB | Freigabe | ADR_REVIEW_MATRIX (G7-03), DECISION_CLOSURE_PACKAGE §RC-4 (NOT READY: Turnier-Primärquelle fehlt) | ADR-Akzeptanz (04/14-Aufbau-Klausel) |
| RC-5 | M4-Restpunkte: F-03 (specs/adrs), D-033…D-035-Plan-Docs, v0.8-Manual (TC-H3), KIR-Repo-Status | offen | DOC/ARB | Doku/Entscheidung | G5 RC-5 (Statusliste), DECISION_CLOSURE_PACKAGE §RC-5 | Doc 19 KG-01/KG-05/KG-10; v0.8-Autorität |
| RC-6 | Finale Gate-Checkliste + Re-Messung M1…M5 | ausstehend bis RC-1/RC-2 | ARB | Messung | DECISION_CLOSURE_PACKAGE §RC-6, G6-05, Doc 18 §2 | Score-Fortschritt >75 formell |

## 6 P0-Probleme

### P0-1 — Graph-OS Reconstruction (PA-08)

- Zustand: GraphState/SphereState rein in-memory, kein Rebuild-Mechanismus (MC-TC-007 Phase H ❌ FAIL); Produktions-Restart-Risiko (G5 R1, HIGH).
- Evidence: MC-TC-007 (H), G4.5 B5, DECISION_CLOSURE_PACKAGE §RC-1 (Optionen A–D; Option A = Rebuild-Service aus `stored_events` als ARCHITECTURE CHANGE über features/-Plugin-Pfad, D-006-konform).
- Status: PENDING HUMAN (RC-1); keine Entscheidung getroffen.

### P0-2 — Watchdog-Event-Persistenz (PA-09)

- Zustand: Watchdog erkennt Orphans, persistiert aber keine Events in EventStore (MC-TC-007 Phase F ⚠️ PASS*); Lücke dokumentiert.
- Evidence: features/monitoring/execution_watchdog.py:96-119 (DECISION_CLOSURE_PACKAGE §RC-1); MC-TC-007 (F).
- Status: PENDING HUMAN (RC-1); Optionen A–D offen (A = `_force_fail_orphan()` persistiert über `EventStore.append()`, features/-Pfad, nicht CORE).

## 7 HDR-001 — Manual Authority

- Registriert: 20.07 (docs/governance/HDR-001_DECISION_RECORD.md); Referenz D-023 (DECISION_REGISTRY).
- Problem: Manual-Autorität (M-0.7) ohne formale Entscheidung; 3 Folge-HDRs (HDR-002…004) seit 20.07 blockiert (G5 R2, HIGH).
- Evidence: HDR-001-Datei, G7-02 (Optionen A–D), G5 B6/RC-2.
- Status: **HUMAN REQUIRED** (RC-2); keine Entscheidung getroffen.

## 8 FL-01a — Flakiness (19 order-dependent Failures)

- Zustand: 19 von 23 Pytest-Failures reproduzierbar order-dependent (2× voll: 23 failed / 2.343 passed / 1 skipped; Einzelsuite 177/177, 176+1); nach FL-01b-Fix: 19 flaky / 2.347 passed / 1 skipped (G2-Exekution, d5f5ce7-Regressions-Report).
- Root-Cause: globale Singletons — `features/tools/tools.py:9-24` (`_UTR`, set_global_utr), `features/tool_runtime/tool_runtime.py:37-42` (Timeout), `tool_runtime.py:28-42` (Event-Store-Pfad) — ohne Test-Reset (GLOBAL_STATE_ARCHITECTURE_DECISION_DRAFT §1, G2 §FL-01a C1).
- Betroffen: tests/test_worker.py (6), test_tool_runtime_phase3.py (6), test_specialized_cu_phase5.py (3), test_runtime_convergence.py (2), test_pipeline_phase4.py (1), test_phase6_production_readiness.py (1) (G2 §FL-01a).
- Entscheidungsentwurf D-042: Optionen A (Test-Fixtures, empfohlen) / B (DI, CORE-Kollision) / C (DI-Container) — keine Akzeptierung ohne Human/ARB (DECISION_CLOSURE_PACKAGE §RC-3).
- Status: Fix-Entscheidung offen (RC-3, D-040).

## 9 Validation

- Read-only: keine Datei verändert, keine Priorität neu erfunden, keine Statusänderung, keine ADR-Akzeptierung, kein Code.
- Alle Blocker mit Quelle (G4.5/G5/Closure-Package/G7/Artefakte); Status wörtlich übernommen (PENDING HUMAN, HUMAN REQUIRED, NICHT GESTARTET, offen, Deferred).
- Konsistenz: RC-Nummern und Inhalte deckungsgleich mit Doc 12 §8, Doc 19 (KG-16/KG-17/KG-14/KG-06); B5/B6/B7-Verknüpfung RC-1/RC-2/RC-3 identisch (G5).
- Keine Widersprüche; offene Punkte nur mit Quelle (Turnier-Primärquelle fehlt → RC-4a).
