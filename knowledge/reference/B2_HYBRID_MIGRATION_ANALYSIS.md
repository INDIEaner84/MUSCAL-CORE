# B2_HYBRID_MIGRATION_ANALYSIS

Technische Migrationsanalyse — MUSCAL B2 Hybrid Zielarchitektur

- Datum: 02.08.2026
- Rolle: Lead Software Architect (B2 Hybrid Zielarchitektur)
- Rahmen: **READ ONLY** — keine Codeänderungen, kein Commit, keine Implementierung, nur Analyse; External KF layer
- Kennzeichnung: [F] FACT (Datei:Zeile) · [I] INFERENCE · [H] HYPOTHESIS
- Ziel: MUSCAL CORE bleibt Runtime; muscal/ wird Verification + Governance Layer; EventStore wird Single Source of Truth (Arbeitshypothese, nicht beschlossen)
- Quellen: EVENT_SOURCING_INTEGRITY_ANALYSIS.md [ESIA], STATE_TRANSITION_EVENT_ANALYSIS.md [STE], B2_HYBRID_ARCHITECTURE_DECISION_PACKAGE.md [B2PKG], RC6_FINAL_ARB_DECISION_PACKAGE.md [PKG], RC6_ARCHITECTURE_DECISION_READINESS_REPORT.md [RDY], SESSION_RULES v2.0 [SR], DECISION_REGISTRY.md [REG], PROJECT_STATE.md [PST], Code-Stand 02.08.2026
- Status: **created, not committed (external KF layer)**

---

## 1. EventStore Schema v2

### 1.1 Fehlende Felder (Ist-Defizit)

| Feld | Status heute | Beleg | Zweck in B2 |
|------|--------------|-------|-------------|
| aggregate_id | [F] fehlt in `stored_events` (nur in legacy `events`) | runtime/event_store.py:50-67; runtime/database.py:62 | [I] zielgerichtete Rekonstruktion je Aggregat (Graph/Node/Execution) |
| aggregate_type | [F] fehlt in `stored_events` (nur in legacy `events`) | runtime/event_store.py:50-67; runtime/database.py:63 | [I] Aggregat-Klassifikation für Projection-Regeln |
| metadata | [F] fehlt (keine Spalte) | runtime/event_store.py:50-67 | [I] Pruning-Marker (E-4), Focus-Marker (E-5), Temporal-Info (E-9) |
| parent_event_id | [F] fehlt (causation_id als Näherung) | runtime/event_store.py:61 | [I] explizite Event-Kette (Kausal-Struktur) |
| payload_delta | [F] fehlt — NODE_UPDATED ohne Payload | graph.py:103-108; kernel.py:152-156 | [I] Inhalts-Rekonstruktion (E-1) |
| logical_time | [F] fehlt | runtime/event_store.py:50-67 | [H] Monotonie unabhängig von wall-clock; heute seq erfüllt Ordnung [I: ESIA §6] |
| prev_hash / event_hash | [F] fehlt — keine Ketten-Integrität | runtime/event_store.py:50-67 | [I] Tamper-Erkennung (E-11), Audit-Belastbarkeit |
| event_source_scope | [F] fehlt (source ist Freitext) | runtime/event_store.py:54 | [H] formaler Erzeuger-Scope (CORE/muscal/Bridge) für Boundary-Prüfung |

- [F] Vorhanden: seq, topic, payload, source, priority, timestamp, event_id UNIQUE, created_at, execution_id, correlation_id, causation_id, execution_mode, execution_state, verification_state, is_replayed, receipt_id, schema_version [F: runtime/event_store.py:50-67].
- [F] MCPL-Spezifikation plant bereits Schema-Erweiterung von `stored_events` [F: spec/MC-006-MCPL-TECHNICAL-SPECIFICATION.md:81-86,1481] — Überschneidung mit v2-Feldern prüfen [I].

### 1.2 Migration ohne Datenverlust

- [F] Migrations-Muster existiert: `_migrate_add_columns` (additiv, idempotent, PRAGMA-basiert) [F: runtime/event_store.py:274-303] — Referenz für alle v2-Spalten [I].
- [I] Empfohlene Vorgehensweise (Analyse, kein Beschluss):
  1. Additive Spalten via `ALTER TABLE … ADD COLUMN` mit Defaults (Muster event_store.py:287-302)
  2. `schema_version`-Inkrement auf 2; Bestands-Events behalten Version 1 [F: event_store.py:65,143]
  3. Bestehende Zeilen bleiben unverändert (kein Rewrite) — Replay-Reihenfolge (seq) unberührt [F: event_store.py:328]
  4. Verifikation: SELECT-Mapping vor/nach (Zeilenanzahl + seq-Kontinuität)
- [F] Kein Datenverlust-Risiko bei additivem Ansatz: INSERT-Pfad erweitert nur die Werte-Liste; keine Spalte wird entfernt [I: event_store.py:121-152].
- [F] Duplikat-Schutz bleibt: event_id UNIQUE [F: event_store.py:57]; IntegrityError-Handling im WriterThread für idempotente Retries [F: runtime/kernel/writer.py:115-117].
- [I] Legacy-`events`-Tabelle bleibt Parallel-Spur (WriterThread-derived) — Konsistenz-Invariant zwischen beiden fehlt weiterhin (kein Abgleich-Mechanismus) [F: runtime/kernel/writer.py:44-46,110-175; ESIA §2.1].

### 1.3 Replay-Garantien (Bewertung unter v2)

- [F] Replay: `seq > cursor ORDER BY seq ASC LIMIT ?` — deterministisch, batching [F: runtime/event_store.py:305-332].
- [F] Cursor: In-Memory (`_last_replayed_seq`), Reset bei Neustart [F: features/replay/replay_service.py:20,84-90] — E-6-Gap.
- [I] Garantie-Matrix (Zielzustand, kein Beschluss):
  - G1 Determinismus: bleibt durch seq-Ordnung + `_replayed`-Suppression [F: event_store.py:94-95,112-119]
  - G2 Idempotenz: event_id UNIQUE + Replay-Marker [F: event_store.py:57; replay_service.py:92-105]
  - G3 Inkrementalität: nur mit Cursor-Persistenz (E-6) [I]
  - G4 Vollständigkeit: nur nach Log-Gap-Schluss (E-1…E-5) [I: ESIA §5]
- [F] MC-TC-006-Rerun ±0 ist Pflicht nach Schema-Änderungen [F: POST_ARB_EXECUTION_PLAN 4.3; B2PKG R1].

---

## 2. GraphState Evolution

| Mutation | Ist | Ziel-Event (Analyse) | CORE-Berührung |
|----------|-----|----------------------|----------------|
| NODE_UPDATED Payload | [F] kein Delta im Event (nur node_id/status/confidence/execution_id) [F: graph.py:103-108]; In-Memory-Mutation via `node.payload.update(payload)` [F: graph.py:100-101] | [H] Event-Payload um `payload_delta` erweitern (nur geänderte Keys) — damit Rebuild den Inhalt rekonstruieren kann [I: ESIA E-1] | [F] ja — graph.py ist CORE/IMMUTABLE (D-020) [F: SR] → nur OVERRIDE oder features/-Projektionsweg [I] |
| NODE_REMOVED Events | [F] fehlen — remove_node löscht ohne Event [F: graph.py:133-138] | [H] Tombstone-Event `graph.node_removed` (node_id, reason: explicit/prune) [I: ESIA E-2] | [F] ja (graph.py) |
| PRUNING Events | [F] fehlen — prune_graph entfernt älteste Nodes/Edges ohne Marker [F: graph.py:145-158] | [H] `graph.pruned`-Event mit entfernten IDs + Regel-Version (MAX_NODES 5000/MAX_EDGES 10000 [F: graph.py:41-42]) — Rebuild braucht identische Regel oder Marker [I: ESIA E-4] | [F] ja (graph.py) |
| FOCUS_CHANGED Events | [F] fehlen — set_focus ohne Event [F: graph.py:162-165]; Implizit-Set in add_node [F: graph.py:84-86] | [H] `graph.focus_changed`-Event (node_id) [I: ESIA E-5] | [F] ja (graph.py) |
| EDGE-Mutationen | [F] EDGE_CREATED ohne payload/timestamp [F: graph.py:124-128]; remove_edge ohne Event [F: graph.py:140-143] | [H] Schema-Vervollständigung analog E-3/E-4/E-9 [I: ESIA E-3/E-9] | [F] ja (graph.py) |

- [F] `_replaying`-Flag existiert [F: graph.py:56,226-229] und streamt weiterhin in `_update_stream` [F: graph.py:220-233] — Basis für Replay-Einschleusung [I].
- [F] node_id deterministisch (Counter) [F: graph.py:55,65-66] — Rebuild-Struktur nur stabil, wenn Pruning-Reihenfolge identisch oder via Pruning-Events [I: graph.py:145-158].
- [I] Alternativer Weg ohne graph.py-Änderung: Projection-Layer in features/ rekonstruiert Zustand via public API (add_node/update_node/add_edge) — Log-Vollständigkeit muss trotzdem im Quell-Event liegen [I: B2PKG Teil 3; PKG Teil 1].
- [I] Rebuild-Treue heute: Struktur ≈78 %, Zustand ≈46 % [I: STE §4] — Zielwerte nur durch Human-Beschluss definierbar [I].

---

## 3. Snapshot Architektur

### 3.1 Snapshot Format (Analyse)

- [F] Konfiguration existiert: `snapshot_file: str = "storage/kernel_snapshot_v0.1.json"` [F: os_config.py:52]; `_load_snapshot` prüft nur Existenz + publiziert snapshot.loaded/missing, lädt keinen Zustand [F: muscal_os.py:391-397].
- [F] Graph-Snapshot-Struktur verfügbar: get_snapshot() liefert nodes (id/type/payload/timestamp/confidence/status/execution_id), edges (source_id/target_id/edge_type/payload), focus, event_count [F: graph.py:254-279].
- [H] Snapshot-Format (Vorschlag): JSON-Dokument mit
  - `schema_version` (Snapshot-Format-Version) [I]
  - `state`: GraphState.get_snapshot()-äquivalent [F: graph.py:254-279]
  - `store_seq`: letzter verarbeiteter EventStore-seq (Resume-Anker) [I: event_store.py:51]
  - `created_at` / `source` / `hash` (Integrität) [H: ESIA E-11-Muster]
- [I] Verortung: Datei (snapshot_file-Konfiguration) oder Event (`graph.snapshot`-Topic) — beide Optionen bleiben offen [H: B2PKG Teil 4, ESIA §1.3].

### 3.2 Restore Ablauf (Analyse)

- [H] Ablauf-Vorschlag (kein Beschluss):
  1. Snapshot laden (existiert nicht → Leerzustand + Full-Replay ab 0)
  2. Konsistenzprüfung (s. 3.3)
  3. Events ab `store_seq+1` über EventStore.replay [F: event_store.py:319-321] einspielen
  4. GraphState via public API rekonstruieren (features/-Pfad, D-006) [I: B2PKG Teil 2]
  5. Validierung: Rebuild-Kennzahl + Spot-Checks (E-10-Mechanismus) [I: ESIA E-10]
- [F] Boot-Anbindung: Boot-Matrix Phase K ist dokumentierter Integrationspunkt [F: POST_ARB_EXECUTION_PLAN 3.2].
- [F] Achtung: `_load_snapshot` ist CORE (muscal_os.py IMMUTABLE) [F: SR] — Restore-Logik gehört in features/-Plugin, Anrufpunkt muss klassifiziert werden [I].

### 3.3 Konsistenzprüfung (Analyse)

- [F] Heute kein Mechanismus: kein Rebuild-Validierungs-Test „Rebuild ≡ Event-Log"; MC-TC-007 Phase H ❌ FAIL [F: MC-TC-007_STATUS_ZUSAMMENFASSUNG.md:67; ESIA E-10].
- [H] Prüf-Ebenen (Vorschlag):
  - Struktur: node/edge-Anzahl + IDs nach Rebuild vs. erwartet (Pruning-Marker nötig) [I: ESIA E-4]
  - Inhalt: Stichproben-Payload-Vergleich (nur möglich nach E-1) [I]
  - Kette: seq-Kontinuität + event_id-UNIQUE-Verletzungen [F: event_store.py:51,57]
  - Determinsmus: gleiches Event-Log → identischer Zustand (MC-TC-006-Pattern) [F: PST]
- [I] Konsistenzprüfung ist Gate-Bedingung für Phase 2 (Replay/Reconstruction) [I: B2PKG Teil 9].

---

## 4. muscal Integration

### 4.1 Module-Klassifikation (Analyse)

**Separat bleibend (Paket, kein Plugin):**

| Modul | Beleg | Begründung (Analyse) |
|-------|-------|----------------------|
| verification/ (engine, states) | [F] muscal/src/muscal/verification/engine.py, states.py | [I] Verification-State-Machine ist eigenständige Laufzeit (UNKNOWN→CLAIMED→CHECKING→VERIFIED [F: muscal/README]) — als Dienst integrieren, nicht als CORE-Plugin |
| reality/ | [F] muscal/src/muscal/reality/ | [I] Reality-Modell ist Paket-Kern (CLAIM≠REALITY [F: README]) |
| claims/ | [F] muscal/src/muscal/claims/ | [I] Claims-Modell |
| evidence/ (recorder, models, graph) | [F] muscal/src/muscal/evidence/ | [I] Evidence-Erfassung konsumiert Events; bleibt Paket-API |
| security/ | [F] muscal/src/muscal/security/ | [I] Sicherheits-Schicht außerhalb CORE-Zertifizierung |
| cognitive_os/ | [F] muscal/src/muscal/cognitive_os/ | [I] B3-nah — bleibt separat, kein B2-Anteil [I: B2PKG Teil 1] |
| simulation/ | [F] muscal/src/muscal/simulation/ | [I] Test-/Simulations-Orbital |
| tenant/, mreil/, compliance/, incidents/, knowledge/, workflow/ | [F] muscal/src/muscal/ | [I] Fachmodule ohne CORE-Kopplung |

**Plugin-Kandidaten (features/):**

| Modul | Beleg | Begründung (Analyse) |
|-------|-------|----------------------|
| governance/ (governor, budget, conflict, consensus, registry, scheduler) | [F] muscal/src/muscal/governance/ | [I] Policy-Layer als features/-Plugin (D-006-konform), das auf Event-Kette prüft und Governance-Events erzeugt |
| monitoring/ | [F] muscal/src/muscal/monitoring/ | [I] komplementär zu CORE-features/monitoring; Adapter-Plugin |
| api/, runtime/ | [F] muscal/src/muscal/ | [I] Integrations-Adapter als features/-Brücken (Muster: features/bridge/, EventStoreAdapter [F: features/events/event_adapter.py:75-85]) |
| validation/ | [F] muscal/src/muscal/validation/ | [I] Validierungs-Plugin auf EventStore-Basis |

- [H] Integrations-Muster (Analyse): muscal/-Kern bleibt eigenständiges Paket; CORE-seitig entsteht ein dünner Integrations-Plugin-Adapter in features/, der EventStore→muscal/-Evidence weiterreicht und muscal/-Verification-Ergebnisse als `execution.verification`-Events zurückführt [I: event_store.py:181-272-Muster; PKG Teil 3].
- [F] Kein Code-Kontakt heute — Integrationsvertrag ist Vorarbeit [F: STE E1.1/E1.2; B2PKG R2].

### 4.2 CORE-Verletzungs-Prüfung (D-006/D-020)

- [F] D-006: Erweiterungen nur in features/ [F: SR]; D-020: CORE-Dateien IMMUTABLE (graph.py, kernel.py, event_bus.py, muscal_os.py …) [F: SR; AGENTS.md].
- [F] muscal/ ist ein externes Paket (eigenes pyproject) [F: muscal/pyproject.toml] — kein CORE-Import von muscal/ in CORE nötig [I].
- [I] Verletzungs-Risiko-Punkte (Analyse):
  - Event-Gaps (E-1…E-5) in graph.py → CORE-Berührung: nur via OVERRIDE (spec/OVERRIDE.md-Pfad) oder feature-seitige Projection [I: ESIA E-1…E-5]
  - `_persist_to_store`/`_bridge_to_graph` (muscal_os.py:279-294,384-389) sind CORE — neue Kopplungen dürfen sie nicht erweitern; Adapter in features/ [I]
  - WriterThread (runtime/kernel/writer.py) ist CORE — muscal/-Events laufen über EventStore.append-API, nicht über Writer-Modifikation [I]
- [F] Architektur-Änderungs-Klassifikation + `--allow-core-write` nur mit dokumentiertem OVERRIDE [F: AGENTS.md; SR D-020].
- [I] Boundary-Tests (Import-/Zugriffs-Gates) sind Voraussetzung gegen R2 (Boundary Drift) [I: B2PKG R2].

---

## 5. Production Readiness Roadmap

> Nur Reihenfolge, keine Zeitversprechen (B2PKG Teil 9-Erweiterung um Phase 0).

**Phase 0 — Audit (Voraussetzung):**
- Bestandsaufnahme: drei Event-Systeme (stored_events/events/audit_log) [F: ESIA §2.1], Log-Gaps (E-1…E-11) [F: ESIA §5], Zertifizierungs-Status (MC-TC-004/006 CERTIFIED, MC-TC-007 Phase H ❌) [F: PST; MC-TC-007:67]
- Eingangs-Gates: RC-1a/RC-1b-Entscheidung, RC-2 (HDR-001), RC-4a (ADR-Review) [F: RC6_MEASUREMENT_GATE_CHECKLIST; HUMAN_DECISION_INDEX:69]
- Audit-Artefakte: ESIA (vorliegend), B2PKG (vorliegend), diese Analyse (vorliegend)

**Phase 1 — Event Integrity:**
- Schema v2-Felder additiv (aggregate_id, metadata, payload_delta, prev_hash) [I: §1.2]
- Log-Gaps schließen: NODE_UPDATED-Delta (E-1), NODE_REMOVED (E-2), Edge (E-3), PRUNING (E-4), FOCUS (E-5), Temporal (E-9) [I: §2]
- Watchdog-Persistenz (E-7/E-8) via EventStoreAdapter [F: features/events/event_adapter.py:75-85]
- MC-TC-006-Rerun ±0 nach jeder Schema-/Event-Änderung [F: POST_ARB_EXECUTION_PLAN 4.3]
- CORE-Berührung je Gap → OVERRIDE-Klassifikation oder features/-Projektionsweg [I: §4.2]

**Phase 2 — Verification Integration:**
- Integrationsvertrag CORE↔muscal/ (Boundary-Definition, B2PKG Teil 2) [I]
- muscal/-Evidence-Adapter als features/-Plugin; Verification-Ergebnisse als `execution.verification`-Events [I: §4.1]
- Replay/Reconstruction: Cursor-Persistenz (E-6), Rebuild-/Projection-Service, Snapshot-Mechanismus (E-10) [I: §3]
- Rebuild-Validierung (MC-TC-007-Phase-H-Ziel) [F: MC-TC-007:67]

**Phase 3 — Agent Governance:**
- Policy-Layer (muscal/governance) als Plugin auf Event-Kette [I: §4.1]
- Authorization-/Capability-Schritt im Agent-Fluss (Agent→Capability→Authorization→Execution→Evidence→Verification→Commit) [H: B2PKG Teil 5]
- Governance-Gates je Agent-Pfad; Agent-Identität (agent_id [F: MC-TC-004-POST-REMEDIATION:376])

**Phase 4 — Production Gate:**
- Formale Re-Messung RC-6 (M1…M5) [F: RC6_MEASUREMENT_GATE_CHECKLIST]
- Kriterien: Rebuild-Treue-Zielwerte (Human-Beschluss nötig) [I], MC-TC-006 ±0, MC-TC-007-Phase-H-Ziel, Performance-Budget (Verification-Latenz, B2PKG R3) [I]
- Freigabe-Beschluss durch Human (Decision Owner) [F: HUMAN_DECISION_INDEX]

---

## Validation

- Read-only: keine Datei verändert (außer dieser neuen), kein Commit, keine Implementierung, keine automatische Entscheidung, keine Empfehlung als Fakt.
- Alle [F] mit Datei:Zeile bzw. Artefakt-Referenz; [H]-Vorschläge (Schema-Felder, Event-Typen, Snapshot-Format, Integrations-Muster, Phasen) ausdrücklich als Analyse-Spielraum gekennzeichnet, kein Beschluss.
- Konsistent mit ESIA/STE/B2PKG/PKG/RDY, SESSION_RULES v2.0, DECISION_REGISTRY, PROJECT_STATE; Statuslage unverändert (RC-1 PENDING HUMAN, RC-2 HUMAN REQUIRED, RC-4a NICHT GESTARTET).
