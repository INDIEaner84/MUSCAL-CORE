# POST_ARB_EXECUTION_PLAN

- Datum: 02.08.2026
- Zweck: Ausführungsplan NACH den Human/ARB-Entscheidungen (Vorbereitungs-Artefakt; read-only — **kein Ausführungsschritt wird heute gestartet**; keine Implementierung, keine Commits)
- Gültigkeit: Der Plan tritt erst nach Protokollierung der Entscheidungen (PROJECT_STATE + DECISION_REGISTRY, durch Entscheider/Governance) in Kraft
- Basis: KF5_IMPLEMENTATION_READINESS_MAP.md, ARCHITECTURE_DECISION_IMPACT_GRAPH.md, RC1/RC2-Briefe, ADR_REVIEW_PACKET.md, RC6_MEASUREMENT_GATE_CHECKLIST.md, DECISION_CLOSURE_PACKAGE §RC-6
- Status: **created, not committed (external KF layer)**

---

## Phase 1 — Human Decisions Completed

| Schritt | Aktivität | Ergebnis-Kriterium | Quelle |
|---------|-----------|--------------------|--------|
| 1.1 | RC-1: P0-1/P0-2-Optionen A–D je P0 wählen; Frist festlegen | Entscheidung + Frist protokolliert in PROJECT_STATE + DECISION_REGISTRY | G7-01 („Welche Option … und welche Frist gilt?") |
| 1.2 | RC-2: HDR-001-Option A–D wählen (inkl. Auflagen bei B) | PROJECT_STATE-HDR-Tabelle → DECIDED; D-023-Update | HDR-001_DECISION_RECORD §7 |
| 1.3 | RC-3: FL-01a/D-042-Freigabe (ARB) | D-042-Status (ACCEPTED/DEFERRED) | GLOBAL_STATE_ARCHITECTURE_DECISION_DRAFT; G5 RC-3 |
| 1.4 | RC-4a: ADR-Review-Runde ansetzen (ARB) | Review-Protokoll je ADR (Status-Empfehlung) | ADR_REVIEW_MATRIX Protokoll 1–4 |
| 1.5 | RC-5: DOC-Auftrag (F-03, v0.8, D-033…35-Plan-Docs, TC-H3) | Aufgaben-Zuweisung (DOC-Klasse, G4.5 §7) | §RC-5; KF3-M-2 |
| 1.6 | Registrierung aller Ergebnisse | DECISION_REGISTRY/05-Foundation-Spiegel aktualisiert | G7-01 Paket-Hinweis; KF4_Completion §4 |

## Phase 2 — ADR Synchronization

| Schritt | Aktivität | Bedingung | Quelle |
|---------|-----------|-----------|--------|
| 2.1 | ADR-022…025: Status-Urteile der Review-Runde übernehmen (nur durch Review-Instanz) | RC-4a-Protokoll liegt vor | ADR_REVIEW_MATRIX Protokoll 3/4 |
| 2.2 | ADR-INDEX + ADR-Dateien synchronisieren | Status-Empfehlung je ADR | G6-01; ADR_INDEX |
| 2.3 | REFERENCE_GRAPH-DRAFT-Knoten (Doc 04/14) bei ACCEPTED aktualisieren | ADR-Status final | KF3-Queue §RC-4a |
| 2.4 | Projekt-Bezugs-Dokumente: PROJECT_STATE-ADR-Tabelle, ARCHITECTURE.md/Baseline bei ACCEPTED | Konsistenz mit SESSION_RULES-Prio 2/3 | SOURCE_OF_TRUTH_MAP FINDING A1 |
| 2.5 | Registry-D-Spiegel (D-010…D-014): CHAT_ONLY-Markierung erst bei Repo-Beleg entfernen | G6-04-Regel | 05_DECISION_REGISTRY §F |

## Phase 3 — Implementation

| Schritt | Aktivität | Constraint | Quelle |
|---------|-----------|------------|--------|
| 3.1 | **RC-1b (falls A/B)**: `_force_fail_orphan()` um EventStore.append() ergänzen (via EventStoreAdapter); Option B: Dedup-Marker | features/-Pfad; MC-TC-006-Replay-Matrix-Prüfung VOR Code | KF5-Map §3; G7-01 P0-2 |
| 3.2 | **RC-1a (falls A)**: Rebuild-Service-Plugin (features/graph_rebuild/), Replay-basiert; Boot-Phase-K-Anbindung; kein graph.py-Write | D-006; graph.py nur public API | KF5-Map §2; G7-01 P0-1 |
| 3.3 | **RC-1a/R-1b (falls D/C)**: Governance-/Doku-Umsetzung (Freeze → DEPRECATED; DEFERRED-Markierung; ADR-022-Item) | Doku-only | G7-01 |
| 3.4 | **RC-3 (falls Freigabe)**: Test-Fixture-Fix (test-only) + D-042-Dokumentation | test-only; Baseline 470 unangetastet | D-040/D-041/D-042 |
| 3.5 | **RC-5**: F-03-Prüfung; v0.8-Manual-Generierung (Census/Reconciliation-Daten); D-033…35-Plan-Docs; TC-H3-Header (nur mit Inhalts-Mandat) | DOC-Klasse; keine Löschung (F-03-Regel) | §RC-5; KF5-Map §6 |
| 3.6 | Session-Handover + Pre-Write-Check je Änderung | `guards.write_guard.validate_write(path)`; D-021 | AGENTS.md; SESSION_RULES v2.0 |

## Phase 4 — Testing

| Schritt | Aktivität | Ergebnis-Kriterium | Quelle |
|---------|-----------|--------------------|--------|
| 4.1 | Rebuild-/Persistenz-/Dedup-/Audit-Tests implementieren (je gewählter Option) | neue Tests grün; FL-01a-Fixtures berücksichtigt | KF5-Map §2.6/§3.6 |
| 4.2 | Regression: Baseline 470 (D-041); MC-TC-007 Phase L 384/384 | keine Baseline-Verletzung ohne dokumentierte Kalibrierung | D-041; MC-TC-007 |
| 4.3 | Replay-Determinismus (MC-TC-006-Suite) nach EventStore-Änderungen | deterministisch, ±0 | MC-TC-006 |
| 4.4 | Dokument-Validierung RC-5 (v0.8-Zahlen vs. Census; Referenz-Markierungen) | Zahlen-Konsistenz (TF-06-Kontradiktion auflösen) | MASTER_INDEX TF-06 |
| 4.5 | Testzahlen-Bericht mit verifizierter Quelle publizieren | keine Kontradiktion (0/547/812/431/384-Fall) | MASTER_INDEX TF-06 |

## Phase 5 — Measurement Gate RC-6

| Schritt | Aktivität | Bedingung | Quelle |
|---------|-----------|-----------|--------|
| 5.1 | Voraussetzungen prüfen: RC-1 ✅, RC-2 ✅, RC-4a ✅ (ADR-Review abgeschlossen), RC-5 ✅ (Dokumentationsreste bewertet) | alle 4 erfüllt | RC6_MEASUREMENT_GATE_CHECKLIST §2 |
| 5.2 | Formale Re-Messung M1–M5 nach G6-Recheck-Protokoll (unweighted avg, MASTER_INDEX §2) | formel-konsistent zu Audit/G2/G4/G5/G6 | 18_METRIC_REGISTRY §6; G6 §2 |
| 5.3 | Messwerte versionieren (Audit-ID + Datum) | Kette Audit→G2→G4→G4.5→G5→G6→RC-6 | 18_METRIC_REGISTRY §6-4 |
| 5.4 | Gate-Bewertung durch Gate-Gremium (GO/NO-GO je Ergebnis) — **nicht durch diesen Agenten** | Gremium-Entscheidung | DECISION_CLOSURE_PACKAGE §RC-6; G4.5/G7-04 |
| 5.5 | Ergebnisse protokollieren (PROJECT_STATE, Registry, Knowledge-Layer) | Traceability | G6 §4 |

## Cross-Phase Regeln (verbindlich)

| Regel | Quelle |
|-------|--------|
| Kein Schritt beginnt ohne dokumentierte Entscheidung (Phase-1-Gate) | POST_ARB-Plan Präambel |
| Keine Core-Änderung ohne ARCHITECTURE CHANGE + OVERRIDE-Pfad | SESSION_RULES v2.0 VIOLATION HANDLING |
| Keine Score-Berechnung außerhalb formeller Gate-Re-Messung | 18_METRIC_REGISTRY §6-1 |
| CHAT_ONLY/PLANNED bleibt bis Repo-Beleg | G6-04 |
| Handover-Pflicht je Session mit Änderungen | D-021 |

## Validation

- Read-only-Vorbereitung: keine Ausführung, keine Implementierung, keine Commits, keine Entscheidung, keine Score-Prognose; alle Schritte mit Quelle und Ergebnis-Kriterium.
- Der Plan trifft keine Optionen-Wahl (RC-Optionen bleiben Entscheider-Sache; Szenarien in KF5_IMPLEMENTATION_READINESS_MAP §7 ungewählt).
