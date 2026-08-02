# EVENT_SOURCING_INTEGRITY_ANALYSIS

Technische Grundlage für **ADR-XXX „EventStore Integrity & State Reconstruction Model"**

- Datum: 02.08.2026
- Modus: **READ ONLY** — Analyse, ADR-Vorbereitung, Evidenz-Sammlung; keine Codeänderung, keine Migration, keine Implementierung, keine Entscheidung, kein Commit
- Kennzeichnung: [F] FACT · [I] INFERENCE · [H] HYPOTHESIS — technische Aussagen mit `Datei:Zeile`
- Status: **created, not committed (external KF layer)**
- Vorlagen-/Referenz-Artefakte: STATE_TRANSITION_EVENT_ANALYSIS.md [STE], ARB_DECISION_SIMULATION_REPORT.md [SIM], RC6_ARCHITECTURE_DECISION_READINESS_REPORT.md [RDY], RC6_FINAL_ARB_DECISION_PACKAGE.md [PKG], DECISION_REGISTRY.md [REG], PROJECT_STATE.md [PST], SESSION_RULES.md [SR]

---

## 1. Executive Summary

- [F] MUSCAL CORE besitzt eine dreigeteilte Event-Landschaft: `stored_events` (EventStore, append-only, SQLite, „SINGLE CANONICAL EVENT AUTHORITY") [F: runtime/event_store.py:36-37], `events` (Legacy-Tabelle, vom WriterThread als abgeleitete Kopie beschrieben) [F: runtime/kernel/writer.py:44-46], `audit_log` (EventBus-Persistenz-Plugin mit 30-Tage-Retention) [F: features/observability/event_persistence.py:8,29-38].
- [F] Graph-State-Mutationen sind nur teilweise event-gespiegelt: `add_node`, `update_node`, `add_edge` erzeugen Events; `remove_node`, `remove_edge`, `prune_graph`, `set_focus` erzeugen **keine** Events [F: graph.py:77-83, 103-108, 124-128, 133-158, 162-165].
- [F] `NODE_UPDATED` trägt kein Payload-Delta: nur node_id/status/confidence/execution_id [F: graph.py:103-108]; Payload-Updates wie `payload={"result": …}` bleiben unsichtbar [F: kernel.py:152-156].
- [F] Replay existiert (EventStore.replay + ReplayService, MC-TC-006-zertifiziert) [F: runtime/event_store.py:305-332; features/replay/replay_service.py:22-44; PST]; der Replay-Cursor ist flüchtig (In-Memory, `_last_replayed_seq = 0`) [F: features/replay/replay_service.py:20,84-90].
- [F] GraphState-Rebuild aus dem Event-Log ist **nicht vollständig möglich**: Struktur-Rekonstruktion ≈ 78 %, Zustand-Rekonstruktion ≈ 46 % (Modell aus STE §4) [I: STE §4 S-1…S-12].
- [F] Kein Snapshot-Mechanismus: `_load_snapshot` prüft nur Datei-Existenz und publiziert Events, lädt aber keinen Graph-Zustand [F: muscal_os.py:391-397]; keine Snapshot-Tabelle für EventStore [I: runtime/database.py:160-174].
- [F] Keine Hash-/Integritäts-Verifikation der Event-Kette: `stored_events` ohne prev-hash/hash-Spalte [F: runtime/event_store.py:50-67].
- [I] Befunde sind unabhängig vom Truth-Model-Konzept (Option A/B/C) wirksam — sie definieren die Rekonstruierbarkeit unabhängig von der gewählten Architektur [I].

## 2. Event Inventory

| Event | Erzeuger | Datei:Zeile | Speicherung | Replay-Fähigkeit | Lücke |
|---|---|---|---|---|---|
| EVENT_NODE_CREATED → `graph.node_created` | GraphState.add_node | graph.py:77-83; muscal_os.py:370 | EventBus + EventStore (Wildcard-Subscriber) | ja (Payload: node_id, type, payload, timestamp, execution_id) | — |
| EVENT_NODE_UPDATED → `graph.node_updated` | GraphState.update_node | graph.py:103-108; muscal_os.py:371 | EventBus + EventStore | ja, aber ohne Payload-Delta | **Payload-Verlust** |
| EVENT_EDGE_CREATED → `graph.edge_created` | GraphState.add_edge | graph.py:124-128; muscal_os.py:372 | EventBus + EventStore | ja (ohne edge-payload, ohne timestamp) | **E-4/E-9** |
| EVENT_EXECUTION_STARTED/FINISHED → `graph.execution_started/finished` | GraphState-Event-Mapping | muscal_os.py:373-374 | EventBus + EventStore | ja | — |
| Alle weiteren EventBus-Topics (z. B. boot, plugins, snapshot.loaded) | MuscalOS-Boot-/Plugin-Pfade | muscal_os.py:305,324-327,338-340,354-358,361,394,396 | EventBus + EventStore (Wildcard) | ja | — |
| EXECUTION_FAILED (Watchdog) | ExecutionWatchdog._force_fail_orphan | features/monitoring/execution_watchdog.py:107-119 | **nur EventBus** (kein Store-append) | nein (fehlt im Store) | **E-7/E-8** |
| execution.receipt | UnifiedToolRuntime → EventStore.store_receipt | runtime/event_store.py:154-179 | EventStore | ja | — |
| execution.verification | VerificationOrchestrator → EventStore.store_verification | runtime/event_store.py:181-272 | EventStore | ja | — |
| Kernel-Events (events-Tabelle) | WriterThread (Runtime-Pfade, gate/bootstrap/workers) | runtime/kernel/writer.py:123-175; runtime/kernel/gate.py:55-57; runtime/api/workers.py:27-91; runtime/kernel/bootstrap.py:54 | EventStore (canonical) + `events` (derived) | ja (doppelt) | **Doppel-Speicherung** |
| bridge.execution | BridgeEventWriter.write_execution_event | features/bridge/bridge_event_writer.py:28-68 | EventStore | ja | — |
| EventBus-Historie | EventBus.publish | event_bus.py:43-70 | In-Memory `_history` (max 50000) | nein (flüchtig) | — |
| audit_log-Einträge | Plugin event_persistence._persist_event (Wildcard-Subscriber) | features/observability/event_persistence.py:40-59 | SQLite `audit_log` (30d-Retention, Löschung) | nein (retention-begrenzt) | **kein Dauer-Audit** |

### 2.1 Speicher-Landschaft im Detail

- [F] `stored_events`: seq AUTOINCREMENT, topic, payload TEXT, source, priority, timestamp REAL, event_id TEXT NOT NULL UNIQUE, created_at, execution_id, correlation_id, causation_id, execution_mode, execution_state, verification_state, is_replayed, receipt_id, schema_version [F: runtime/event_store.py:50-67].
- [F] `events` (Legacy): seq UNIQUE, idempotency_key UNIQUE, aggregate_id, aggregate_type, replayable, domain/layer/stream-CHECKs [F: runtime/database.py:53-71].
- [F] `audit_log`: id, entry_type, payload, created_at [F: runtime/database.py:166-169].
- [F] WriterThread schreibt canonical zuerst EventStore, dann derived `events`-Tabelle; bei EventStore-Duplikat nur Warning („may be idempotent retry") [F: runtime/kernel/writer.py:110-133].
- [F] Drei parallele Persistenzpfade ohne Konsistenz-Invariant zwischen `stored_events`, `events` und `audit_log` [F: runtime/kernel/writer.py:110-175; features/observability/event_persistence.py:40-59].
- [F] EventStoreAdapter verbindet Writer-Events mit EventStore (idempotency_key → id) [F: features/events/event_adapter.py:8-26,75-85].

## 3. Mutation Mapping

| Mutation | Datei:Zeile | aktuelles Event | Payload vorhanden | Replay möglich |
|---|---|---|---|---|
| add_node | graph.py:61-88 | EVENT_NODE_CREATED [F: graph.py:77-83] | ja (node_id, type, payload, timestamp, execution_id) | ja |
| update_node | graph.py:90-108 | EVENT_NODE_UPDATED [F: graph.py:103-108] | nein — **kein Payload-Delta** [F: graph.py:100-101,103-108] | eingeschränkt (Zustand rekonstruierbar, Inhalt nicht) |
| remove_node | graph.py:133-138 | **kein Event** [F: graph.py:133-138] | n/a | nein |
| remove_edge | graph.py:140-143 | **kein Event** [F: graph.py:140-143] | n/a | nein |
| prune_graph | graph.py:145-158 | **kein Event** (ruft remove_node/edges.pop ohne Event) [F: graph.py:145-158] | n/a | nein |
| set_focus | graph.py:162-165 | **kein Event** [F: graph.py:162-165] | n/a | nein |
| add_edge | graph.py:112-129 | EVENT_EDGE_CREATED [F: graph.py:124-128] | nein — ohne payload, ohne timestamp [F: graph.py:124-128] | eingeschränkt |
| System-Action-Start (State-Transition) | kernel.py:133-146 | add_node + add_edge (CONTROLS) [F: kernel.py:134-146] | ja (tool, status, args) | ja |
| System-Action-Finish (State-Transition) | kernel.py:147-157 | update_node(payload={"result":…}) [F: kernel.py:152-156] | **nein im Event** (nur im In-Memory-Node) [F: graph.py:100-108] | eingeschränkt |
| Watchdog-Orphan-Force-Fail | features/monitoring/execution_watchdog.py:96-119 | EXECUTION_FAILED via Bus [F: :107-119] | ja (execution_id, error, execution_state, execution_mode, verification_state) | **nein** (kein Store-append) |
| Receipt-/Verification-Transition | runtime/event_store.py:154-179,181-272 | execution.receipt / execution.verification [F] | ja | ja |
| Bridge-Execution-Status | features/bridge/bridge_event_writer.py:28-68 | bridge.execution [F] | ja (task_id, project_id, status, data) | ja |

### 3.1 Seiteneffekte und Invarianten

- [F] `add_node` setzt `active_focus_node` implizit auf ersten Knoten (kein eigenes Event) [F: graph.py:84-86].
- [F] `prune_graph` wird von add_node/add_edge nach jedem Event aufgerufen (`_dispatch_depth`-Guard) [F: graph.py:87,129,147-148].
- [F] `_replaying`-Flag unterdrückt Listener-Dispatch, streamt aber weiterhin in `_update_stream` [F: graph.py:56,220-233].
- [F] node_id ist deterministisch über `_node_counter` — aber abhängig von Pruning-Reihenfolge bei Rebuild [F: graph.py:55,65-66,145-158].

## 4. Reconstruction Capability

### Current Reconstruction Capability Matrix

| Kategorie | Aspekt | Wiederherstellbar | Wert | Beleg |
|---|---|---|---|---|
| A) Struktur | Nodes (ID, Typ) | ja — via NODE_CREATED, ID deterministisch | ~85 % | [F: graph.py:65-66,77-83] [I: STE §4] |
| A) Struktur | Edges (Typ) | ja — via EDGE_CREATED (ohne payload) | ~80 % | [F: graph.py:124-128] [I] |
| A) Struktur | Löschungen (remove/prune) | nein — keine Events | 0 % | [F: graph.py:133-158] |
| **A) Struktur gesamt** | | | **≈ 78 %** | [I: STE §4 S-1…S-12] |
| B) Inhalt | Node-Payload initial | ja — NODE_CREATED trägt payload | ~90 % | [F: graph.py:80] |
| B) Inhalt | Payload-Updates (z. B. result) | **nein — NODE_UPDATED ohne Delta** | ~0 % | [F: graph.py:103-108; kernel.py:152-156] |
| B) Inhalt | Edge-Payload | nein — nie im Event | 0 % | [F: graph.py:124-128] |
| B) Inhalt | Metadaten (confidence/status) | ja — NODE_UPDATED trägt beide | ~80 % | [F: graph.py:105-106] |
| **B) Inhalt gesamt** | | | **≈ 40-50 %** | [I: STE §4] |
| C) Historie | Änderungen | eingeschränkt (nur status/confidence) | ~30 % | [F: graph.py:103-108] |
| C) Historie | Löschungen | nein | 0 % | [F: graph.py:133-143] |
| C) Historie | Pruning | nein | 0 % | [F: graph.py:145-158] |
| **C) Historie gesamt** | | | **≈ 10 %** | [I] |
| D) Temporaler Zustand | Focus | nein — kein Event, kein Snapshot | 0 % | [F: graph.py:162-165; muscal_os.py:391-397] |
| D) Temporaler Zustand | aktive Prozesse (execution_state) | ja — im Store vorhanden | ~70 % | [F: runtime/event_store.py:63] |
| D) Temporaler Zustand | Agent-State | nein — nicht im Event-Modell | 0 % | [F: runtime/event_store.py:50-67] |
| **D) Temporaler Zustand gesamt** | | | **≈ 25 %** | [I] |

- [F] Gesamtwert Struktur/Zustand im STE-Modell: Struktur ≈ 78 %, Zustand ≈ 46 % [I: STE §4] — konsistent mit obiger Einzelbewertung [I].
- [F] Rebuild-Orchestrierung fehlt: kein Service, der Store→Replay→GraphState rekonstruiert; nur `_replaying`-Flag und `emit`-Brücke existieren [F: graph.py:56,235-239; muscal_os.py:384-389].

## 5. Missing Event Register (Gap Register)

### E-1 Payload Delta

- **ID:** E-1
- **Problem:** NODE_UPDATED enthält kein Payload-Delta; `payload.update(payload)` mutiert Node in-memory ohne Event-Abbild
- **Dateien:** graph.py, kernel.py
- **Zeilen:** graph.py:90-108, 100-101; kernel.py:152-156
- **Auswirkung:** Rebuild rekonstruiert veraltete Node-Payloads; SYSTEM_ACTION-Ergebnisse verloren; Zustands-Treue bricht
- **Architekturzone:** CORE (graph.py — immutable, D-020)
- **Abhängigkeiten:** RC-1a-Truth-Model; D-020/OVERRIDE; Tests
- **Priorität:** HIGH
- **Entscheidungsstatus:** PENDING — Teil von RC-1a

### E-2 Node Delete Event

- **ID:** E-2
- **Problem:** remove_node() erzeugt kein Event
- **Dateien:** graph.py
- **Zeilen:** graph.py:133-138
- **Auswirkung:** Rebuild behält gelöschte Knoten; Struktur-Treue sinkt
- **Architekturzone:** CORE (graph.py — immutable)
- **Abhängigkeiten:** RC-1a; D-020
- **Priorität:** HIGH
- **Entscheidungsstatus:** PENDING — Teil von RC-1a

### E-3 Edge Delete Event

- **ID:** E-3
- **Problem:** remove_edge() erzeugt kein Event
- **Dateien:** graph.py
- **Zeilen:** graph.py:140-143
- **Auswirkung:** Rebuild behält gelöschte Kanten
- **Architekturzone:** CORE (graph.py — immutable)
- **Abhängigkeiten:** RC-1a; D-020
- **Priorität:** HIGH
- **Entscheidungsstatus:** PENDING — Teil von RC-1a

### E-4 Pruning Event

- **ID:** E-4
- **Problem:** prune_graph() entfernt älteste Nodes/Edges ohne Marker-Event; Rebuild hat keine identische Pruning-Regel
- **Dateien:** graph.py
- **Zeilen:** graph.py:41-42,145-158
- **Auswirkung:** Rebuild übersteigt MAX_NODES/MAX_EDGES oder divergiert; node_id-Verteilung abweichend
- **Architekturzone:** CORE (graph.py — immutable)
- **Abhängigkeiten:** RC-1a; Rebuild-Prüfregel
- **Priorität:** HIGH
- **Entscheidungsstatus:** PENDING — Teil von RC-1a

### E-5 Focus Event

- **ID:** E-5
- **Problem:** set_focus() erzeugt kein Event; Implizit-Set in add_node auch ohne Event
- **Dateien:** graph.py
- **Zeilen:** graph.py:84-86,162-165
- **Auswirkung:** active_focus_node nach Rebuild leer/falsch
- **Architekturzone:** CORE (graph.py — immutable)
- **Abhängigkeiten:** RC-1a
- **Priorität:** MEDIUM
- **Entscheidungsstatus:** PENDING — Teil von RC-1a

### E-6 Replay Cursor Persistence

- **ID:** E-6
- **Problem:** `_last_replayed_seq` ist In-Memory, Reset bei Neustart
- **Dateien:** features/replay/replay_service.py
- **Zeilen:** features/replay/replay_service.py:20,43-44,81-90
- **Auswirkung:** Inkrementeller Rebuild ab „letztem Stand" unmöglich; nur Full-Replay; erneute Publikation ab 0
- **Architekturzone:** features/replay (Feature-Zone, D-006-konform)
- **Abhängigkeiten:** MC-TC-006; Rebuild-Strategie
- **Priorität:** MEDIUM
- **Entscheidungsstatus:** PENDING — Teil von RC-1a/C

### E-7 Watchdog EventStore Append

- **ID:** E-7
- **Problem:** Watchdog publiziert EXECUTION_FAILED nur auf EventBus, appends nicht in EventStore
- **Dateien:** features/monitoring/execution_watchdog.py
- **Zeilen:** features/monitoring/execution_watchdog.py:60-76 (liest), 96-119 (schreibt nicht)
- **Auswirkung:** Orphan-Erkennungen überleben Restart nicht; C03-Doppelalarme möglich
- **Architekturzone:** features/monitoring (Feature, D-006)
- **Abhängigkeiten:** RC-1b; MC-TC-006-Replay-Matrix; event_adapter.py:80-85
- **Priorität:** HIGH
- **Entscheidungsstatus:** PENDING — Teil von RC-1b

### E-8 Execution Failure Persistence

- **ID:** E-8
- **Problem:** EXECUTION_FAILED fehlt in `_EXECUTION_REQUIRED_TOPICS`; append ohne execution_id wäre technisch möglich
- **Dateien:** runtime/event_store.py
- **Zeilen:** runtime/event_store.py:21-32
- **Auswirkung:** Inkonsistenz mit anderen Execution-Topics; fehlender Integritäts-Schutz
- **Architekturzone:** EventStore-Layer (runtime/)
- **Abhängigkeiten:** RC-1b; Schema-Entscheidung
- **Priorität:** LOW
- **Entscheidungsstatus:** PENDING — Teil von RC-1b

### E-9 Temporal Metadata

- **ID:** E-9
- **Problem:** EDGE_CREATED ohne timestamp und ohne payload; EventBus-Graph-Spiegelung verliert Original-Timestamp (MuscalOS nutzt msg.timestamp)
- **Dateien:** graph.py, event_bus.py, muscal_os.py
- **Zeilen:** graph.py:124-128; event_bus.py:16-23; muscal_os.py:279-294,365-382
- **Auswirkung:** Zeitliche Kanten-Reihenfolge nur über seq ableitbar; Zeitreihen-Analysen eingeschränkt; Temporal-Reasoning (muscal/-Konzepte) unterversorgt
- **Architekturzone:** CORE (graph.py) + EventStore-Layer
- **Abhängigkeiten:** RC-1a; muscal/-Temporal-Konzepte
- **Priorität:** MEDIUM
- **Entscheidungsstatus:** PENDING — Teil von RC-1a

### E-10 Snapshot Capability

- **ID:** E-10
- **Problem:** kein Snapshot/Restore: `_load_snapshot` prüft nur Datei-Existenz, lädt keinen Zustand; keine Snapshot-Tabelle für EventStore
- **Dateien:** muscal_os.py, runtime/database.py
- **Zeilen:** muscal_os.py:391-397; runtime/database.py:160-174
- **Auswirkung:** Rebuild immer vollständig; Start-Kosten linear; lange Historie ohne Verdichtung
- **Architekturzone:** Boot-/Runtime-Layer (runtime/)
- **Abhängigkeiten:** RC-1a; Rebuild-Strategie; D-020 (muscal_os.py immutable)
- **Priorität:** MEDIUM
- **Entscheidungsstatus:** PENDING — Teil von RC-1a/C

### E-11 Hash Verification

- **ID:** E-11
- **Problem:** keine Integritäts-Verifikation der Event-Kette: keine Hash-Spalte, kein prev-hash, kein Verifikations-Pfad für stored_events
- **Dateien:** runtime/event_store.py
- **Zeilen:** runtime/event_store.py:50-67,305-332
- **Auswirkung:** Manipulation/Tampering nicht erkennbar; Audit-Belastbarkeit begrenzt; MC-TC-004-Boundary ohne Ketten-Integrität
- **Architekturzone:** EventStore-Layer (runtime/)
- **Abhängigkeiten:** RC-1a; MC-TC-004/006-Rahmen
- **Priorität:** MEDIUM
- **Entscheidungsstatus:** PENDING — Teil von RC-1a; MCPL-Schema-Extensions (spec/MC-006-MCPL-TECHNICAL-SPECIFICATION.md:1481) berühren

## 6. Event Schema Assessment

| Feld | stored_events | events (Legacy) | EventBus-Message | Bewertung |
|---|---|---|---|---|
| event_id | ja (event_id UNIQUE) [F: event_store.py:57] | ja (idempotency_key UNIQUE) [F: database.py:60] | ja (uuid7) [F: event_bus.py:23,52] | vorhanden |
| sequence | ja (seq AUTOINCREMENT) [F: event_store.py:51] | ja (seq UNIQUE) [F: database.py:54] | nein (nur History-Reihenfolge) | vorhanden |
| aggregate_id | **nein** [F: event_store.py:50-67] | ja [F: database.py:62] | nein | **fehlt in stored_events** |
| aggregate_type | **nein** [F: event_store.py:50-67] | ja [F: database.py:63] | nein | **fehlt in stored_events** |
| actor | nein — nur source [F: event_store.py:54] | ja (actor) [F: database.py:56] | nein — nur source [F: event_bus.py:20] | teilweise (source≈actor) |
| correlation_id | ja [F: event_store.py:60] | nein | nein | vorhanden (Store) |
| parent_event | **nein** — causation_id als Näherung [F: event_store.py:61] | nein — caused_by als Näherung [F: database.py:59] | nein | **fehlt** (nur Näherung) |
| payload | ja [F: event_store.py:53] | ja [F: database.py:59] | ja [F: event_bus.py:19] | vorhanden |
| metadata | **nein** — keine eigene Spalte [F: event_store.py:50-67] | nein — payload_misc-Felder teils | nein | **fehlt** |
| verification | ja (verification_state) [F: event_store.py:64] | nein | nein | vorhanden (Store) |
| timestamp | ja (timestamp REAL) [F: event_store.py:56] | ja (ts/occurred_at) [F: database.py:55] | ja [F: event_bus.py:22] | vorhanden |
| logical_time | **nein** [F: event_store.py:50-67] | nein | nein | **fehlt** (Lamport/Hybrid) |

- [F] store_receipt/store_verification schreiben vollständigere Identitätsfelder als generische appends [F: event_store.py:154-179,181-272].
- [I] MCPL-Spezifikation sieht Schema-Erweiterung von `stored_events` vor (spec/MC-006-MCPL-TECHNICAL-SPECIFICATION.md:81-86,1481) — künftige Felder könnten dort anknüpfen [F].

## 7. Snapshot Assessment

- [F] Event-Replay-Kosten: SQLite-Scan `seq > cursor ORDER BY seq LIMIT ?`; Kosten O(n) bei Full-Replay, batching via limit [F: event_store.py:328-332]. Bei MAX_NODES=5000/MAX_EDGES=10000 in-memory [F: graph.py:41-42] und Replay-Batches à 100 [F: replay_service.py:28-30] skaliert Full-Replay linear, kein Blocker bei aktueller Größe [I].
- [F] Graph-Größe: begrenzt durch Pruning (MAX_NODES 5000, MAX_EDGES 10000) [F: graph.py:41-42,145-158]; `_update_stream` ist dagegen **unbegrenzt** [F: graph.py:54,220-223] — Memory-Risiko bei langen Sessions [I].
- [F] EventBus-Historie: begrenzt auf 50000 (FIFO-Drop) [F: event_bus.py:40,55-56].
- [F] Memory-Limit: kein konfigurierter Bound für _update_stream; DB bleibt Single-File-SQLite [F: graph.py:54; runtime/database.py:160-174].
- [I] Snapshotting (Kompression von Event-Stream → Zustand) ist bei aktuellen Limits optional, wird bei wachsender Historie bzw. Wiederanlauf-Latenz relevant [I]; kein Snapshot-Mechanismus vorhanden [F: E-10].
- [I] Skalierung: Single-Consumer-ReplayService ohne Consumer-Group [F: replay_service.py:14]; parallel wachsende Prozesse wären spätere Skalierungsfrage [I].

## 8. Option Comparison A/B/C

### Option A — EventStore Single Source of Truth

- **Architektur-Konsistenz:** [I] konsistent mit „SINGLE CANONICAL EVENT AUTHORITY" [F: event_store.py:37] und D-008 (Layer-Trennung) [F: REG D-008]; GraphState wird Projektion [I]
- **Migration:** [I] kein Bestands-Umbau nötig (Store existiert, Replay existiert); Neu-Code in features/ (D-006) [I]
- **Risiko:** [I] mittel — Log-Lücken (E-1…E-5, E-9) begrenzen Rebuild-Treue; Pruning-Markierung (E-4) zwingend für Struktur-Treue [I]
- **Replay:** [F] vorhanden und zertifiziert (MC-TC-006) [F: PST]; Cursor-Persistenz fehlt (E-6) [F]
- **Auditierbarkeit:** [I] eine append-only-Spur; Ketten-Hash fehlt (E-11) [I]
- **MUSCAL-2.0-Kompatibilität:** [I] passt zum „durable execution"-Sieger (ADR-022 §Context); Migrationspfad D-010↔D-001 offen [F: REG §D]
- **Agent-Architecture-Kompatibilität:** [I] einheitliche Wahrheit für Agenten; Session/Checkpoint bleibt bei Runtime (Kernel-Audit §4) [F: COGNITIVE_KERNEL_AUDIT]
- **Wartbarkeit:** [I] eine Quelle, ein Rebuild-Pfad; Rebuild-Tests wachsen [I]

### Option B — Dual Truth (Memory State + EventStore)

- **Architektur-Konsistenz:** [I] heutiger Ist-Zustand de-facto (GraphState in-memory + persistierte Bus-Spiegel); Konsistenz-Semantik fehlt, kein Reconciliation-Invariant [I]
- **Migration:** [I] kein Umbau; spätere Vereinheitlichung = zweite Migration; Log-Lücken bleiben wirksam [I]
- **Risiko:** [I] hoch — Drift zwischen Live-Zustand und Log; Ambiguität für Leser [I]
- **Replay:** [I] Replay existiert, aber Live-Zustand und Rebuild divergieren ohne Abgleich [I]
- **Auditierbarkeit:** [I] Audit über Store, Live über Memory — Abweichungen ungeprüft [I]
- **MUSCAL-2.0-Kompatibilität:** [I] konfliktär zur durable-Execution-Einheitsquelle [I]
- **Agent-Architecture-Kompatibilität:** [I] je Leseweg unterschiedliche Wahrheit möglich [I]
- **Wartbarkeit:** [I] teuerste Variante: Doppel-Buchführung, Drift-Diagnose [I]

### Option C — Reconstruction Layer über bestehendem System

- **Architektur-Konsistenz:** [I] explizite Schicht zwischen EventStore und GraphState (CQRS-Projection-Muster); D-008-konform; Abgrenzung zu ReplayService nötig [I]
- **Migration:** [I] wie A plus Layer-Kontrakt-Definition; Layer-API als Migrationsanker [I]
- **Risiko:** [I] mittel — wie A plus Abgrenzungs-/Overlap-Risiko mit ReplayService [I]
- **Replay:** [I] Replay = Layer-Eingang; Layer-Tests gegen Replay-Matrix [I]
- **Auditierbarkeit:** [I] Audit über Store; Layer erzeugt nachvollziehbare Rebuild-Nachweise [I]
- **MUSCAL-2.0-Kompatibilität:** [I] Layer als wiederverwendbares durable-Recovery-Modul [I]
- **Agent-Architecture-Kompatibilität:** [I] stabiler Layer-Kontrakt als Agenten-Schnittstelle [I]
- **Wartbarkeit:** [I] gut wartbar; Duplikationsrisiko mit ReplayService als Folgepflege [I]

### Querschnitt

- [I] Alle Optionen respektieren die Core-Grenze, wenn Rebuild ausschließlich public GraphState-API (graph.py:61-108) nutzt [I: SR].
- [F] Log-Vollständigkeit (E-1…E-5, E-9) ist gemeinsame Abhängigkeit — betrifft A und C direkt, B nur bei Rebuild-Nutzung [I].
- **Keine Empfehlung, keine Auswahl** — Optionen-Raum bleibt für ARB/Human offen.

## 9. Governance Mapping

| Governance-Baustein | Bezug | Befund |
|---|---|---|
| D-008 (EventBus/EventStore/AuditLog Trennung) | Layer-Trennung | [F] real existiert: Bus (in-memory), Store (SQLite), audit_log (30d) — getrennte Tabellen/Objekte [F: event_bus.py:26-41; event_store.py:35-37; database.py:166-169]; [I] Doppel-Speicherung (Store + events-Tabelle + audit_log) ist grenzwertig bzgl. Trennungs-Doktrin [I: writer.py:110-175] |
| D-020 (CORE Immutability) | graph.py, muscal_os.py, event_bus.py immutable | [F] Gaps E-1…E-5, E-9 berühren CORE (graph.py) → nur via OVERRIDE-Dokumentation oder features/-Projektionsweg [F: SR; REG D-020]; [I] E-6/E-7 liegen in features/ (D-006-konform) [I] |
| D-006 (Feature-Erweiterungen) | Neuer Code in features/ | [F] Rebuild-Service/Reconstruction Layer und Watchdog-Append sind als features/-Arbeiten möglich [F: SR; features/replay/, features/events/ existieren als Vorlage] |
| RC-1a (EventStore Truth Model) | P0-1 | [F] alle Log-Lücken (E-1…E-5, E-9) und Cursor (E-6), Snapshot (E-10), Hash (E-11) sind Entscheidungsinputs für RC-1a [F: PKG Teil 1] |
| RC-1b (Watchdog Persistence) | P0-2 | [F] E-7/E-8 sind Inputs für RC-1b-Optionen A–D [F: PKG Teil 2; RDY] |
| MC-TC-006 (Replay-Pflicht) | Determinismus | [F] neue Topics/Events müssen die Replay-Matrix passieren; ReplayService bleibt Referenz [F: PST; replay_service.py:22-44]; [I] E-6 (Cursor-Persistenz) gefährdet inkrementellen Pfad [I] |
| MC-TC-004 (EventStore Trust Boundary) | EventStore | [F] SANCTIONED (G2-01) [F: spec/OVERRIDE.md:1523]; [I] E-11 (Hash) betrifft die Belastbarkeit dieser Boundary [I] |
| ADR-003 / ADR-EVENT-001 | Event-System / Boundary | [F] Graph→Bus-Mapping in ADR-003 dokumentiert (5 Topics) [F: spec/ADR-003-events.md:21]; [F] ADR-EVENT-001 definiert zwei append-Pfade in dieselbe Tabelle [F: spec/ADRs/ADR-EVENT-001-eventstore-boundary.md:11-20] |

## 10. Open Human Decisions

| ID | Entscheidung | Eingangsevidenz | Status |
|---|---|---|---|
| RC-1a | EventStore Truth Model (A/B/C) | PKG Teil 1; diese Analyse §8 | PENDING HUMAN (P0-1) [F: PST] |
| RC-1b | Watchdog Persistence (A–D) | PKG Teil 2; E-7/E-8 | PENDING HUMAN (P0-2) [F: PST] |
| E-1…E-5, E-9 | Log-Vollständigkeit (CORE-Berührung) | §5; §3 | PENDING — Teil von RC-1a; D-020/OVERRIDE-Frage [F: SR] |
| E-6 | Replay-Cursor-Persistenz | §5; §4 | PENDING — Teil von RC-1a/C |
| E-10 | Snapshot-Mechanismus | §7; §5 | PENDING — Teil von RC-1a/C |
| E-11 | Hash-/Ketten-Verifikation | §5; §9 (MC-TC-004) | PENDING — Teil von RC-1a; MCPL-Schema |
| ADR-XXX | EventStore Integrity & State Reconstruction Model | diese Analyse | **ADR-VORBEREITET, NICHT ERSTELLT** — Erstellung nur auf Anweisung |
| HDR-001 (D-03/D-04) | Governance-Form / Architekturform | PKG Teil 4/5 | HUMAN REQUIRED (RC-2) [F: PST] |

---

## Validation

- Read-only eingehalten: keine Datei verändert, kein Commit, keine Migration, keine Implementierung, keine Entscheidung, keine Empfehlung als Entscheidung.
- Alle [F] mit `Datei:Zeile`; [I]/[H] klar getrennt; Werte (78 %/46 %) als Modell aus STE übernommen und gekennzeichnet.
- Konsistent mit STE/SIM/RDY/PKG und Code-Stand 02.08.2026.
