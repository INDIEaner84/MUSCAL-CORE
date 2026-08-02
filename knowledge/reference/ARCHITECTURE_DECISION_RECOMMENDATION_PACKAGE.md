# ARCHITECTURE_DECISION_RECOMMENDATION_PACKAGE

MUSCAL Chief Architecture Review — Entscheidungsgrundlage RC-1 / RC-2 / RC-4a

- Datum: 02.08.2026
- Rolle: Chief Architecture Review Agent
- Modus: **READ ONLY** — keine Implementierung, keine Commits, keine automatische Entscheidung, keine Empfehlung als Entscheidung; Human bleibt Decision Owner
- Kennzeichnung: [F] FACT · [I] INFERENCE · [H] HYPOTHESIS — technische Aussagen mit `Datei:Zeile` bzw. Artefakt-Referenz
- Evidenz-Basis: EVENT_SOURCING_INTEGRITY_ANALYSIS.md [ESIA], STATE_TRANSITION_EVENT_ANALYSIS.md [STE], ARB_DECISION_SIMULATION_REPORT.md [SIM], RC6_ARCHITECTURE_DECISION_READINESS_REPORT.md [RDY], RC6_FINAL_ARB_DECISION_PACKAGE.md [PKG], DECISION_REGISTRY.md [REG], PROJECT_STATE.md [PST], SESSION_RULES.md [SR], HDR-001_DECISION_RECORD.md [HDR], MC-TC-006/004/007-Artefakte, Code-Stand 02.08.2026
- Status: **created, not committed (external KF layer)**

---

# 1. Event Sourcing Zielarchitektur

> Zielbild-Entwurf als Entscheidungsgrundlage (nicht beschlossen). Alle Elemente sind Vorlagen für einen späteren ADR-XXX, markiert als Entwurf [H]/[I].

## 1.1 Event Schema v2 (Entwurf)

- [F] Aktuelles Schema `stored_events` (Soll-Nullbasis): seq, topic, payload, source, priority, timestamp, event_id UNIQUE, created_at, execution_id, correlation_id, causation_id, execution_mode, execution_state, verification_state, is_replayed, receipt_id, schema_version [F: runtime/event_store.py:50-67].
- [F] Defizite lt. Schema-Assessment: aggregate_id, aggregate_type, metadata, parent_event (nur causation_id als Näherung), logical_time fehlen in `stored_events` [F: ESIA §6].
- [H] Event Schema v2 (Vorschlags-Felder, additive Erweiterung):
  - `aggregate_id` / `aggregate_type` — im Legacy-`events`-Schema bereits vorhanden [F: runtime/database.py:62-63]; Übertrag nach `stored_events` wäre konsistent [I]
  - `metadata` (JSON-Spalte) — für Temporal-Metadaten (E-9), Pruning-Marker (E-4), Focus-Marker (E-5) [I: ESIA E-4/E-5/E-9]
  - `parent_event_id` (optional) — komplementär zu causation_id [I: ESIA §6]
  - `logical_time` (Monotonie-Zähler) — für deterministische Reihenfolge unabhängig von wall-clock [H: ESIA §6]
  - `prev_hash` / `event_hash` — Ketten-Integrität (E-11) [I: ESIA E-11]
  - `schema_version` inkrementieren statt neuer Tabelle (Migration via `_migrate_add_columns`-Muster) [F: runtime/event_store.py:274-303]
- [I] Schema v2 berührt CORE nicht zwingend: EventStore liegt in runtime/, ist Teil des zertifizierten Trust-Cores (MC-TC-004 SANCTIONED) [F: spec/OVERRIDE.md:1523; spec/ADR-EVENT-001] — Änderung wäre klassifizierte Architektur-Änderung mit OVERRIDE-Pflicht [I: SR].

## 1.2 Replay-Garantien (Entwurf)

- [F] Replay existiert: EventStore.replay(cursor, topic, limit) — seq > cursor, ORDER BY seq ASC [F: runtime/event_store.py:305-332]; ReplayService orchestriert Store→Bus [F: features/replay/replay_service.py:22-82]; MC-TC-006 zertifiziert deterministisch [F: PST; MC-TC-006-Artefakt].
- [F] Cursor ist In-Memory (`_last_replayed_seq`), Reset bei Neustart [F: features/replay/replay_service.py:20,84-90] — Garantie „resume ab letztem Stand" fehlt (E-6) [I: ESIA E-6].
- [H] Ziel-Garantien (Vorschlag):
  - G1: Replay ist deterministisch und idempotent (Republish trägt `_replayed`-Marker; Duplikat-append wird suppressiert) [F: runtime/event_store.py:94-95,112-119; features/replay/replay_service.py:92-105]
  - G2: Cursor-Persistenz (E-6) als Voraussetzung für inkrementellen Rebuild [I: ESIA E-6]
  - G3: Replay-Matrix-Prüfung VOR jeder neuen Topic-Event-Nutzung (MC-TC-006-Pflicht) [F: POST_ARB_EXECUTION_PLAN 3.1]
  - G4: Rebuild-Treue-Kennzahl als Test-Kontrakt (struktur≈78 %, zustand≈46 % heute [I: STE §4]) — Zielwert nur durch Human-Beschluss definierbar [I]
- [I] Ohne E-6/E-10 bleibt nur Full-Replay; bei MAX_NODES=5000/MAX_EDGES=10000 [F: graph.py:41-42] und Batch-Limit 100 [F: replay_service.py:28-30] ist Full-Replay derzeit kostenmäßig beherrschbar, aber linear [I: ESIA §7].

## 1.3 Snapshot-Strategie (Entwurf)

- [F] Kein Snapshot-Mechanismus: `_load_snapshot` prüft nur Datei-Existenz [F: muscal_os.py:391-397]; keine Snapshot-Tabelle [F: runtime/database.py:160-174]; `_update_stream` unbegrenzt im Memory [F: graph.py:54,220-223].
- [H] Optionen-Raum (kein Vorschlag, nur Kategorien):
  - Snapshot als Event: periodischer Kompaktions-Event im Event-Log (z. B. `graph.snapshot` mit Vollzustand) [H]
  - Snapshot als parallele Tabelle (analog mcxf_snapshots-Muster [F: runtime/database.py:161-165]) [H]
  - Snapshot als Datei (snapshot_file-Konfiguration existiert bereits [F: muscal_os.py:392]) [H]
- [I] Snapshot ist bei aktuellen Limits optional (E-10 MEDIUM), wird mit Historie/Latenz relevant [I: ESIA E-10, §7].
- [I] Snapshot berührt Trust-Core-Doktrin: Wiederherstellung über Event-Log bleibt Referenzpfad (D-008-konform) [I].

## 1.4 Projection Model (Entwurf)

- [F] Muster-Anker: CQRS-Event-Log-Modell dokumentiert in spec/MC-006-MCPL-TECHNICAL-SPECIFICATION.md:84-86 („Authoritative event store"); GraphState heute de-facto in-memory Projektion + Bus-Spiegel [F: muscal_os.py:365-389].
- [F] `_replaying`-Flag in graph.py:56,226-229 ist vorhanden, aber ungenutzt für Rebuild (kein Rebuild-Service) [F: graph.py:56,220-233; RC1_BRIEF: „kein Rücklese-/Rebuild-Code" (MC-TC-007:67)].
- [H] Projection-Layer (Entwurf): features/-Plugin (z. B. `features/graph_rebuild/` [F: POST_ARB_EXECUTION_PLAN 3.2]), das Store-Events → GraphState.public-API (add_node/update_node/add_edge via graph.emit) spielt; keine Core-Modifikation (D-006) [I].
- [I] Abgrenzung zu ReplayService nötig: ReplayService = Store→Bus-Transport [F: features/replay/replay_service.py:7-14]; Projection = Bus/Store→GraphState-Reader [I: ESIA §8 C].

## 1.5 Migration vom aktuellen Zustand (Entwurf)

- [F] Ist-Zustand: dreigeteilte Event-Landschaft (stored_events canonical, events legacy-derived, audit_log 30d) [F: ESIA §2.1]; Graph-Bus-Spiegel aktiv für 5 Topics [F: muscal_os.py:369-375].
- [I] Migration = additive Schritte (keine Bestands-Konvertierung zwingend):
  1. Schema v2-Felder via `_migrate_add_columns`-Muster (additiv, idempotent) [F: runtime/event_store.py:274-303]
  2. Log-Lücken schließen (E-1…E-5, E-9) — je Entscheidung CORE-Berührung (D-020) oder features/-Projektionsweg [I: ESIA E-1…E-5]
  3. Rebuild-/Projection-Feature (RC-1a-Option A/C) [F: POST_ARB_EXECUTION_PLAN 3.2]
  4. Watchdog-append (RC-1b-Option A/D) via EventStoreAdapter [F: features/events/event_adapter.py:75-85; POST_ARB_EXECUTION_PLAN 3.1]
  5. Legacy-`events`-Tabelle bleibt bestehen (WriterThread derived-Modus [F: runtime/kernel/writer.py:44-46]) — Abschaltung wäre eigene Entscheidung [I]
- [I] Migrationsfenster ist durch Freeze-Politik (FREEZE_POLICY_UPDATE: Core Runtime, Event-Modell, ADR-State) bis ARB vorbereitet [F: FREEZE_POLICY_UPDATE.md].

---

# 2. RC-1 Vergleich — EventStore Truth Model

| Kriterium | A — EventStore Single Truth | B — Dual Truth (GraphState + EventStore) | C — Reconstruction Layer / CQRS Projection |
|-----------|------------------------------|-------------------------------------------|---------------------------------------------|
| **Konsistenz** | [I] eine Wahrheit; GraphState = Projektion; konsistent mit „SINGLE CANONICAL EVENT AUTHORITY" [F: event_store.py:37] und D-008 [F: REG D-008] | [I] heutiger Ist-Zustand [F: muscal_os.py:365-389]; Konsistenz-Semantik fehlt, kein Reconciliation-Invariant [I: ESIA §2.1] | [I] explizite Schicht zwischen Store und GraphState; D-008-konform; Abgrenzung zu ReplayService nötig [I] |
| **Replayfähigkeit** | [F] Replay vorhanden + MC-TC-006-zertifiziert [F: replay_service.py; PST]; Cursor-Persistenz fehlt (E-6) [F] | [I] Replay existiert, aber Live vs. Rebuild divergieren ohne Abgleich [I] | [I] Replay = Layer-Eingang; Layer-Tests gegen Replay-Matrix [I] |
| **Auditierbarkeit** | [I] eine append-only-Spur; Ketten-Hash fehlt (E-11) [I] | [I] zwei Wahrheiten; Audit-Abweichungen ungeprüft [I] | [I] Audit über Store; Layer erzeugt Rebuild-Nachweise [I] |
| **MUSCAL-2.0-Kompatibilität** | [I] passt zum „durable execution"-Sieger (ADR-022 §Context); D-010↔D-001-Pfad offen [F: REG §D] | [I] konfliktär zur Einheitsquelle [I] | [I] Layer als wiederverwendbares Recovery-Modul [I] |
| **Agent Architecture** | [I] einheitliche Wahrheit für Agenten; Session/Checkpoint bleibt bei Runtime [F: COGNITIVE_KERNEL_AUDIT §4] | [I] je Leseweg unterschiedliche Wahrheit möglich [I] | [I] stabiler Layer-Kontrakt als Agenten-Schnittstelle [I] |
| **Risiko** | [I] mittel: Log-Lücken (E-1…E-5) begrenzen Rebuild-Treue; Pruning-Marker zwingend (E-4) [I] | [I] hoch: Drift, Ambiguität, zweite Migration [I] | [I] mittel: wie A plus Overlap mit ReplayService [I] |
| **Fakten-Status** | [F] Bausteine vorhanden (Store, Replay, _replaying-Flag [F: graph.py:56]); Rebuild-Service fehlt [F: RC1_BRIEF] | [F] de-facto-Ist-Zustand [F: muscal_os.py:365-389] | [F] nicht vorhanden; Bausteine existieren [F: ESIA §8 C] |

- [F] Gemeinsame Abhängigkeit aller Optionen: Log-Vollständigkeit (E-1…E-5, E-9) und Rebuild-Validierung (E-10) [I: ESIA §8].
- [I] Dual Truth (B) ist im G7-01-Optionsraum nicht deklarierbar — Kombinations-/Neudeklarationsfrage an den Entscheider [I: SIM RC-1a].
- **Keine Auswahl.** Entscheidungs-Sheet: PKG Teil 5 D-01; aktuelle Basis RC1_FINAL_DECISION_BRIEF.

---

# 3. RC-2 / HDR-001 — Governance-Modelle

## 3.1 Modelle

### Council-Struktur (HDR-001 Architecture Council — Status quo/Annahme)

- [F] HDR-001: „Architecture Council (Gesamt-Governance des MUSCAL-CORE-Programms)" — READY FOR HUMAN DECISION, 9 Dependencies [F: PST:116; HDR_DECISION_RECORD:14].
- [F] HDR-002…004 BLOCKED by HDR-001 [F: PST:117-119].
- [F] Optionen-Raum HDR-001: A annehmen ohne Auflagen · B annehmen mit Auflagen (Standard: MC-TC-004-Bedingungen, Evidence-Pflicht, P0-Frist) · C ablehnen/verschieben · D Teilfreigabe [F: HDR_DECISION_RECORD:33-35].
- [I] Council als Menschen-Gremium: Entscheidungs-Verbindlichkeit (HDR-001 §5), aber Deadlock-Risiko ohne Frist-Mechanismus [I: PKG D-03].
- [I] SESSION_RULES-Autoritätskette ist Vorläufer ohne formale HDR-Bindung (v0.8-Manual-Autorität TC-H3 PARTIAL) [F: REG §RC-2].

### AI Review Layer

- [F] ARB-Rolle existiert als Review-Instanz: ADR_REVIEW_MATRIX (G7-03) mit Prüfmatrix + Review-Protokoll [F: HUMAN_DECISION_INDEX RC-4a]; ARB „Klären/Autorisieren" für MC-TC-005 [F: HUMAN_DECISION_INDEX:76].
- [F] Replay-/EventStore-Trust-Gate: MC-TC-004/006-Artefakte sind AI-erstellte Zertifizierungen mit formalem Prüfprotokoll [F: PHASE_A_REMEDIATION_PLAN:15].
- [I] AI Review Layer = Vorbereitung/Prüfung ohne Entscheidungsgewalt; Statuslage: RC-1 PENDING HUMAN, RC-2 HUMAN REQUIRED — Decision Owner ist Human [F: HUMAN_DECISION_INDEX:14-15].
- [I] Risiko: AI-Review ohne Menschen-Gate erzeugt Schein-Verbindlichkeit (Beleg: v0.8-Manual-Autorität ungeregelt) [I: REG §RC-2].

### Human Authority Layer

- [F] Human = Decision Owner für RC-1, RC-2, RC-4a-Status-Urteile, MC-TC-005 [F: HUMAN_DECISION_INDEX:14-18,76].
- [F] HDR-001 §5: verbindliche Entscheidung durch Human (Projektleitung/Programm-Owner); ARB nur fachliche Vorprüfung [F: HUMAN_DECISION_INDEX:34].
- [I] Human Layer benötigt: Frist-Mechanismus (fehlt — HDR-001 §6-3, kein Deadline-Mechanismus), Entscheidungs-Protokollierung (PROJECT_STATE + DECISION_REGISTRY) [F: POST_ARB_EXECUTION_PLAN 1.1-1.2].

## 3.2 Governance-Bewertung (neutral, keine Wahl)

| Aspekt | Council (A1) | AI Review Layer (A3-artig) | Human Authority (A4-artig) |
|--------|--------------|----------------------------|----------------------------|
| Verbindlichkeit | [F] hoch (formale Annahme via HDR-001) [F: HDR_RECORD] | [I] niedrig (Review-Vorbereitung) [I] | [F] höchste (Decision Owner) [F: HUMAN_DECISION_INDEX] |
| Geschwindigkeit | [I] langsam ohne Frist (seit 20.07 offen) [F: PST:116] | [I] schnell, aber ohne Bindung [I] | [I] von Prozess-Reife abhängig [I] |
| Qualitätssicherung | [I] kollektive Prüfung; Evidence-Pflicht via Auflagen B [F: HDR_RECORD:34] | [I] reproduzierbare Prüfprotokolle [F: ADR_REVIEW_MATRIX] | [I] Einzel-Verantwortung; benötigt Review-Input [I] |
| Blockier-Risiko | [F] HDR-Deadlock real (HDR-002…004) [F: PST:117-119] | [I] keine Blockade, aber keine Freigabe-Befugnis [I] | [I] Blockade bei Nicht-Entscheidung (RC-1/RC-2 offen seit 20.–31.07) [F: PST] |

- [I] Die drei Modelle sind orthogonal zur Architekturform (B1/B2/B3) und kombinierbar (PKG Teil 4: alle 12 Kombinationen möglich) [I].
- [F] P0-1/P0-2 sind unabhängig von HDR-001 zu entscheiden (G7-01: getrennte Entscheidungen) [F: G7-01; PST:43-48].
- **Keine Auswahl.** Entscheidungs-Sheet: PKG Teil 5 D-03/D-04.

---

# 4. RC-4a Vergleich — Architekturrichtung (ADR-022…025-Review-Kontext)

| Kriterium | A — Evolution CORE | B — Hybrid CORE + muscal/ | C — Cognitive OS Neubau |
|-----------|--------------------|----------------------------|-------------------------|
| **Technische Machbarkeit** | [F] hoch: CORE läuft (384-Test-Basis [F: KF3_QUEUE], Trust-Core MC-TC-004 zertifiziert [F: PST]); features/-Pfad erprobt [F: SR D-006] | [F] muscal/ existiert als eigenständiges Paket v0.1 (pyproject, 24 Module inkl. claims/evidence/reality/verification) [F: muscal/pyproject.toml; muscal/src/muscal/]; [I] Integrationsvertrag CORE↔muscal/ fehlt — kein Code-Kontakt [I: STE E1.1/E1.2] | [I] Entwurfs-Rahmen vorhanden (ADR-023-Intent→Goals→Context→Strategy→Planner→Runtime-Muster) [F: ADR-023 DRAFT]; [I] Cognitive-Kernel-Detail ist Audit-Entwurf, kein akzeptierter ADR [I: COGNITIVE_KERNEL_AUDIT §3] |
| **Risiko** | [I] niedrig: additive Erweiterungen; Core-Berührung bei Event-Gaps (E-1…E-5, D-020) [I] | [I] mittel: Parallel-Betrieb zweier Projektionen; Migrationspfad D-010↔D-001 undefiniert [F: REG §D]; Security-/Trust-Governance-Interaktion offen [F: ADR_REVIEW_MATRIX] | [I] hoch: Neubau ohne akzeptierte Doku-Rahmen (ADR-022…025 DRAFT), ADR-022↔023↔024-zirkuläre Fragen [I: KF3_QUEUE RC-4a] |
| **Zeit** | [I] kurzeste: Rebuild-/Watchdog-Features in features/ (S–M lt. G7-01) [F: RC1_BRIEF] | [I] mittel: Integrations-Design + Vertrag + Zwei-Projekt-Koordination [I] | [I] lang: Design-Phase + Akzeptanz-Kaskade (RC-4a → ADR-Status) [I] |
| **Zukunftsfähigkeit** | [I] Evolution trägt bestehende Zertifizierungen (MC-TC-004/006); MUSCAL-2.0-Pfad D-010 bleibt chat-only bis Migrationsbewertung [F: REG D-010] | [I] Verification-Runtime-Philosophie (CLAIM≠REALITY) [F: muscal/README] als komplementäre Schicht; Duplikations-Risiko bei Projekten [I] | [I] höchster Gestaltungsspielraum, aber Trust-Governance-NO-GO ungelöst [F: KF3_QUEUE RC-4a] |

- [F] RC-4a ist NOT READY: Turnier-Primärquelle nicht im Repo, Migrationsbewertung fehlt, Security-Model unzureichend, Trust-Governance-NO-GO offen, RFC-Prozess nicht definiert [F: HUMAN_DECISION_INDEX:51; KF3_QUEUE §RC-4a].
- [F] Review-Struktur steht (G7-03-ADR_REVIEW_MATRIX) [F: HUMAN_DECISION_INDEX:51].
- [I] ADR-022…025-Akzeptanz blockiert Folge-Architektur-Dokumente (MUSCAL-2.0-Richtung unverbindlich, chat-only) [F: HUMAN_DECISION_INDEX:17].
- **Keine Auswahl.** Entscheidungs-Sheet: PKG Teil 5 D-05 (Status je ADR); Review-Input-Vervollständigung ist Voraussetzung [F: KF3_QUEUE §RC-4a].

---

# 5. Entscheidungsgrundlage (Final Sheet — keine Entscheidung)

> „Decision Basis" — kompakte Zuordnung der offenen Entscheidungen zu den vorliegenden Bewertungen. Human bleibt Decision Owner.

| Entscheidung | Bewertung oben | Entscheidungs-Sheet | Evidenz-Anker | Status | Konsequenz bei Vertagung |
|--------------|----------------|---------------------|---------------|--------|---------------------------|
| RC-1 P0-1 (Truth Model A/B/C) | §2 | PKG D-01; RC1_BRIEF | ESIA §8; STE §4 (78 %/46 %); event_store.py:37 | PENDING HUMAN | Produktions-Restart-Risiko (G5 R1 HIGH); MC-TC-007 Phase H ❌ FAIL [F: MC-TC-007:67] |
| RC-1 P0-2 (Watchdog-Persistenz A–D) | §2 (gemeinsame Abhängigkeit) | PKG D-02; RC1_BRIEF | ESIA E-7/E-8; watchdog.py:60-119 | PENDING HUMAN | Erkennungen überleben Restart nicht; C03 bleibt [F: RC1_BRIEF:109] |
| RC-2 (HDR-001 Governance-Form) | §3 | PKG D-03 | HDR_RECORD:33-35; PST:116-119 | HUMAN REQUIRED | HDR-Deadlock (R2 HIGH); HDR-002…004 blockiert; v0.8-Manual-Autorität TC-H3 PARTIAL |
| RC-2 (HDR-001 Architekturform) | §3 (orthogonal) | PKG D-04 | PKG Teil 4; HDR_RECORD | HUMAN REQUIRED (eigene Frage) | keine Richtungsbindung; MUSCAL-2.0 bleibt chat-only |
| RC-4a (ADR-022…025-Status) | §4 | PKG D-05; ADR_REVIEW_PACKET | KF3_QUEUE §RC-4a; ADR-022…025 | NICHT GESTARTET (NOT READY) | Richtung unverbindlich; Folge-ADR blockiert |
| ADR-XXX (EventStore Integrity & State Reconstruction) | §1 (Zielarchitektur-Entwurf) | ESIA §10 | ESIA gesamt | ADR vorbereitet, NICHT erstellt | Log-Lücken bleiben; Rebuild-Treue 46–78 % [I: STE] |

- [F] Keine Option wurde ausgewählt; keine Statusänderung; kein Commit; nichts implementiert [F: dieser Bericht].
- [I] Entscheidungsreihenfolge (Hinweis aus RC6_GATE_PREPARATION_MATRIX §8, kein Beschluss): E-4 (RC-2, kleinster Aufwand) → E-1/E-2 (RC-1) → E-5/E-6 (RC-4a) → … → formale Re-Messung RC-6 [F: RC6_GATE_PREPARATION_MATRIX:83].

---

## Validation

- Read-only: keine Datei verändert (außer dieser neuen), kein Commit, keine Architekturentscheidung, keine Option gewählt, keine Empfehlung als Entscheidung formuliert.
- Alle [F] mit Datei:Zeile oder Artefakt-Referenz; [H]-Entwürfe (Schema v2, Replay-Garantien, Snapshot, Projection, Migration) ausdrücklich als Vorschlags-Raum gekennzeichnet, kein Beschluss.
- Konsistent mit ESIA/STE/SIM/RDY/PKG, DECISION_REGISTRY, PROJECT_STATE, SESSION_RULES v2.0, HDR-001-DECISION-RECORD, MC-TC-006/004-Artefakten; Statuslage unverändert (RC-1 PENDING HUMAN, RC-2 HUMAN REQUIRED, RC-4a NICHT GESTARTET).
