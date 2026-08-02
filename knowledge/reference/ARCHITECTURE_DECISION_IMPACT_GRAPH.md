# ARCHITECTURE_DECISION_IMPACT_GRAPH

- Datum: 02.08.2026
- Zweck: Modellierung der Abhängigkeitskette Entscheidung → ADR → Code-Module → Tests → Dokumentation; Identifikation kritischer Pfade, versteckter Kopplungen, zirkulärer Abhängigkeiten, Risikokonzentration (read-only; keine Implementierung, keine Entscheidung, keine Score-Berechnung)
- Basis: KF5_IMPLEMENTATION_READINESS_MAP.md, RC1/RC2-Briefe, ADR_REVIEW_PACKET.md, DECISION_CLOSURE_PACKAGE.md, DECISION_REGISTRY (D-001…D-042), Code-Befunde, KF3/KF4-Artefakte
- Status: **created, not committed (external KF layer)**

---

## 1. Graph (Entscheidung → ADR → Code → Tests → Doku)

```
RC-1a (P0-1 Graph-OS)                       RC-1b (P0-2 Watchdog)
   │ Option A: Rebuild-Service                 │ Option A/B: EventStore-Persistenz
   ▼                                           ▼
ADR-006 (Graph/Sphere, ACCEPTED)            ADR-011/012 (Verification/Event Persistence)
ADR-011 (Verification Layer)                ADR-EVENT-001 (EventStore Boundary)
   │                                           │
   ▼                                           ▼
graph.py  (CORE, immutable)                 features/monitoring/execution_watchdog.py:96-119
   │  (public API add_node/update_node/          │
   │   add_edge — kein Core-Write)               ▼
   ▼                                          features/events/event_adapter.py:75-85
features/supl/graph_boundary.py             (EventStoreAdapter → EventStore.append)
features/supl/graph_projection_events.py        │
features/replay/replay_service.py               ▼
   │ (ReplayService: replay_all/topic/since)  EventStore/stored_events (MC-TC-004 CERTIFIED)
   ▼                                           │
Boot-Phase K (features/boot/, MC-TC-007-       ▼
Cert §Phase K — kein Rebuild-Code im Repo)  MC-TC-006-Replay-Matrix (deterministisch)
   │                                           │
   ▼                                           ▼
tests/test_graph.py (32)                    tests/supl/test_gate1_production_wiring.py
tests/supl/test_supl_event_integration.py   tests/… (Watchdog-bezogen, Phase-1a/b/c)
   │                                           │
   ▼                                           ▼
Baseline 470 (D-041) · MC-TC-007 Phase L 384/384 · FL-01a-Fixtures (D-040)

RC-2 (HDR-001) ──► D-023 → PROJECT_STATE-HDR-Tabelle → DECISION_REGISTRY → M2-Eingangsgröße
                    └─► HDR-002…004 (PMGA/Master Coding AI/Requirements) — keine Code-Kante

RC-4a (ADR-022…025) ──► D-010…D-014 (CHAT_ONLY, C2)
   │ ADR-022 ──► ADR-001 (Kernel) / ADR-005 / ADR-006 / D-030
   │ ADR-023 ──► ADR-014 (UTR) / ADR-008 / ADR-EVENT-001
   │ ADR-024 ──► ADR-021 / ADR-022 / ADR-001 / MC-TC-007-TRUST-GOVERNANCE (NO-GO)
   │ ADR-025 ──► ADR-001 / MPIR / D-013 vs D-014
   ▼
spec/ADR-022…025 (DRAFT) → ADR_INDEX → REFERENCE_GRAPH-DRAFT-Knoten (Doc 04/14)
   └─► ACCEPTED ⇒ Folge-Architektur-Dokumente + M4-K2 (nur via Re-Messung)

RC-5 (Doku) ──► specs/adrs/-Leiche (F-03) → docs/engineering-Schema
   │ D-033…035 (PLANNED+CHAT_ONLY) → docs/governance/Plan-Docs
   │ v0.8-Manual ← REPOSITORY_CENSUS / RECONCILIATION-Daten
   │ TC-H3 ← TECHNICAL_MANUAL_AUTHORITY_MAP (3 Manuals)
   └─► M4/M5-Eingangsgrößen (keine RC-1-Kante, KF3-M-2)
```

## 2. Kanten (belegt)

| Kante | Beleg |
|-------|-------|
| RC-1a → ADR-006/ADR-011 | ADR-006 (Graph/Sphere, ACCEPTED) ist Ziel-Architektur; ADR-011 (Verification Layer, features/event_sourcing/) liefert Persistenz-Layer (D-007) |
| RC-1a → graph.py (public API) | graph.py:45ff; CORE immutable — nur add_node/update_node/add_edge konsumierbar (SESSION_RULES v2.0) |
| RC-1a → replay_service | features/replay/replay_service.py (replay_all/topic/since); MC-TC-006 deterministisch |
| RC-1a → Boot Phase K | G7-01 Option A („Anbindung an Boot-Matrix Phase K"); MC-TC-007-Cert §Phase K (6 Boot-Pfade) |
| RC-1b → execution_watchdog.py:96-119 | Code-Befund (nur event_bus.publish, kein append) |
| RC-1b → event_adapter.py:75-85 | EventStoreAdapter.append_writer_event → EventStore.append (vorhandener Rückkanal) |
| RC-1b → MC-TC-006-Replay-Matrix | G7-01 Option A/B („Replay-Relevanz (MC-TC-006-Matrix prüfen)") |
| RC-2 → D-023/PROJECT_STATE | HDR-001_DECISION_RECORD §7; 05_DECISION_REGISTRY §B |
| RC-4a → D-010…D-014 | DECISION_CLOSURE_PACKAGE §RC-4 (NOT READY je ADR) |
| RC-4a → Trust-Governance-NO-GO | MC-TC-007-TRUST-GOVERNANCE-CERTIFICATION (NO-GO; ZERO-Caller; Auto-Approve); ADR-023/024-Consequences |
| RC-5 → Census/Reconciliation | MASTER_INDEX TF-02; TECHNICAL_MANUAL_CONFLICT_REPORT (Zahlen-Basis v0.8) |
| RC-1/2/4a/5 → RC-6 | DECISION_CLOSURE_PACKAGE §RC-6-M4-Messpunkt (RC-1+RC-4+RC-5); G6-Recheck §1-M4 (RC-4a→K2); KF3-H-1 (Mess-Gate) |

## 3. Critical Paths

| Pfad | Kritikalität | Begründung |
|------|--------------|------------|
| RC-1a → Rebuild-Plugin → Replay → Boot → Baseline | **Höchste** | MC-TC-007 Phase H ❌ FAIL; einziger P0 mit Code-Impact; Core-Grenze + Replay-Determinismus (MC-TC-006) müssen gleichzeitig gewahrt bleiben |
| RC-1b → Watchdog-append → EventStore → MC-TC-006-Replay | Hoch | Event-Doppelpersistenz-Risiko; neue Topic-Events müssen Replay deterministisch halten (D-009: append-Signatur verifiziert) |
| RC-4a → ADR-022 (Migrationsbewertung) → ADR-001 | Hoch | Konflikt D-010 vs D-001 (MEDIUM) — blockiert MUSCAL-2.0-Richtungsbindung; Primärquelle fehlt (NOT READY) |
| RC-2 → M2-Eingangsgröße → RC-6 | Mittel | reine Governance-Kante; ohne Human-Entscheidung kein M2/M4-Rest-Abbau (kein Score hier berechnet) |
| RC-5 → v0.8/Census → M4/M5-Eingangsgrößen | Mittel | Doku-only; Zahlen-Kontradiktion TF-06 als Datenqualitäts-Risiko |

## 4. Hidden Coupling (versteckte Kopplungen)

| Kopplung | Beschreibung | Quelle |
|----------|--------------|--------|
| Watchdog → Core-EventBus | `from event_bus import EventPriority` (Core-Import) in features/monitoring/ — Watchdog hängt am Core-Event-System, obwohl Feature | execution_watchdog.py:97 |
| Watchdog → Core-EventBus → Kernel | EXECUTION_FAILED-Topic wird im Kernel-/Verifikationspfad konsumiert — P0-2-Persistenz erweitert Topic-Nutzung | G7-01 P0-2; PA-09 |
| Rebuild → Replay ↔ Execution-Identität | Rebuild liest stored_events; Execution-Identity-Cluster (D-037, Phase-1A) legt Event-Struktur fest — Rebuild muss mit dieser Schreibseite konsistent sein | D-037; 05_DECISION_REGISTRY |
| ADR-024 P5 ↔ Trust-Governance | ApprovalManager-Auto-Approve (features/tools/approval.py:10) — P5-Akzeptanz hängt an Governance-Realität (NO-GO), nicht nur am ADR-Text | MC-TC-007-TRUST-GOVERNANCE; ADR-024 |
| ADR-023 ↔ MC-TC-004/006 | „verified event store" (D-011) setzt auf zertifizierte Layer auf — Akzeptanz impliziert Erweiterung der Zertifizierungs-Scope | ADR-023; D-016 |
| D-010 (MUSCAL 2.0) ↔ ADR-001 | Migrationspfad unbestimmt (Registry §D MEDIUM) — jede MUSCAL-2.0-Arbeit koppelt an die ADR-001-Pipeline-Autorität | ADR-022; 05_DECISION_REGISTRY |
| FL-01a ↔ neue Feature-Tests | Rebuild-/Watchdog-Tests erweitern die flaky-betroffene Fixture-Fläche (globale Singletons) | G7-01 P0-1-Auswirkungen; D-040 |

## 5. Circular Dependencies

| Zirkel | Status | Auflösung |
|--------|--------|-----------|
| ADR-022 ↔ ADR-023 ↔ ADR-024 (wechselseitige Verhältnis-Fragen OQ-2) | offen (Doku-Ebene, keine Code-Schleife) | Review-Reihenfolge im ADR_REVIEW_PACKET; keine gegenseitige Akzeptanz-Bedingung definieren |
| ADR-001 ↔ ADR-022 (Migrationsbewertung braucht ADR-001-Bezug; ADR-022-Status braucht Migrationsbewertung) | dokumentiert (MEDIUM-Konflikt) | Migrationsbewertung als separater Review-Input (KF3-M-4), nicht als ADR-001-Statusänderung |
| RC-6 ↔ RC-1/2/4a/5 (Mess-Gate braucht Entscheidungen; Entscheidungen werden durch Gate gemessen) | **kein echter Zirkel** — H-1-Korrektur: Mess-Gate ist abhängige Größe, Entscheidungsbereitschaft unabhängig | KF3-H-1-Kennzeichnung (Decision Ready ≠ Measurement Ready) |
| D-010 ↔ D-013/D-014 (Hybrid braucht Compiler-Spezifikation; Compiler hängt an Hybrid-Pipeline) | LOW/offen (D-013 vs D-014 LOW) | Scope-Abgrenzung im Review bestätigen/verfeinern (ADR_REVIEW_MATRIX) |

## 6. Risk Concentration

| Zone | Konzentration | Risiko | Quelle |
|------|---------------|--------|--------|
| **Graph-/Event-Pfad (RC-1a+RC-1b)** | hoch — 2 P0-Entscheidungen, gleiche Layer (EventStore/Replay/Boot) | Feature-Interferenz; Replay-Determinismus (MC-TC-006); Core-Grenze | G7-01; MC-TC-006/007 |
| **Trust-Governance (RC-4a: ADR-023/024)** | hoch — 2 ADRs, 1 NO-GO-Befund | Akzeptanz ohne Governance-Basis; Auto-Approve-Bypass bleibt (P0-001…) | MC-TC-007-TRUST-GOVERNANCE §1-3 |
| **M4-K3-Blocker (RC-1/RC-2)** | hoch — 1/4 prozessiert (K3=25) | M4 = 62 limitierend (nur via Re-Messung wirksam) | G6 §2/§3; 18_METRIC_REGISTRY §7 |
| **Manual-/Zahlen-Pfad (RC-5)** | mittel — 3 Manuals, TF-06-Kontradiktion | v0.8-Zahlen falsch → Autoritätsschaden | MASTER_INDEX TF-02/TF-06 |
| **ADR-022-Migrationspfad** | mittel — D-010 vs D-001 | Richtungsunverbindlichkeit bei Umsetzung von MUSCAL 2.0 | Registry §D MEDIUM |

## 7. Empfohlene Prüf-Reihenfolge (keine Entscheidung, nur Modell-Konsequenz)

1. RC-2 (kein Code-Risiko, entblockt Governance-Kette) → 2. RC-1b (kleinster Code-Impact, S) → 3. RC-1a (größter Code-Impact, M–L) → 4. RC-4a (Review vor MUSCAL-2.0-Arbeit) → 5. RC-5 (Doku, parallel möglich) → Re-Messung RC-6.
(Hinweis: Reihenfolge ist Modell-Ableitung aus Aufwand/Risiko, keine GO/NO-GO-Empfehlung und keine Entscheidungs-Empfehlung.)

## 8. Validation

- Read-only: keine Entscheidung, keine Implementierung, keine Score-Berechnung; alle Kanten/Risiken mit Quelle (Datei:Zeile oder Artefakt).
- Konsistenz: deckungsgleich mit KF3_DECISION_DEPENDENCY_GRAPH (RC-Kanten) und KF5_IMPLEMENTATION_READINESS_MAP (§2–§6).
