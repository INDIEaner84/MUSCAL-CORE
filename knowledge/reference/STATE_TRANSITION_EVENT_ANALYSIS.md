# STATE_TRANSITION_EVENT_ANALYSIS

- Datum: 02.08.2026
- Zweck: Analyse aller persistenten und flüchtigen Zustandsänderungen in MUSCAL CORE — Event Inventory, Mutation→Event-Mapping, Missing Event Matrix, Reconstruction Feasibility Score, Minimal Required Event Extensions
- Modus: **READ-ONLY** — keine Codeänderung, keine Empfehlung, nur Evidenz
- Kennzeichnung: FACT (Datei:Zeile belegt) · INFERENCE (Schlussfolgerung) · HYPOTHESIS (Annahme)
- Basis: runtime/event_store.py, runtime/kernel/writer.py, event_bus.py, graph.py, muscal_os.py, features/monitoring/execution_watchdog.py, features/events/event_adapter.py, features/events/event_consolidation.py, features/bridge/bridge_event_writer.py, features/runtime/observability.py, features/observability/event_persistence.py, features/replay/replay_service.py, kernel.py, schema.py
- Status: **created, not committed (external KF layer)**

---

## 1. EVENT INVENTORY

### 1.1 Persistente Schreibpfade (Ziel-Tabellen)

| # | Pfad | Ziel | Producer | Auslöser | FACT |
|---|------|------|----------|----------|------|
| P1 | EventStore.append() | `stored_events` (SQLite, append-only, seq AUTOINCREMENT, event_id UNIQUE) | muscal_os `_persist_to_store` | jede Bus-Publikation via `subscribe("*")` | muscal_os.py:257, 279-294 |
| P2 | EventStore.append() | `stored_events` | WriterThread (canonical) + derived Kopie in legacy `events`-Tabelle | Kernel-Event-Durchlauf | runtime/kernel/writer.py:110-173 |
| P3 | EventStore.append() | `stored_events` | ConsolidatedEventWriter.write_event | explizite write_event-Aufrufe | event_consolidation.py:55 |
| P4 | EventStore.append() | `stored_events` | EventStoreAdapter.append_writer_event | Writer-Events (SUPL-Pfad) | event_adapter.py:80-85 |
| P5 | EventStore.append() | `stored_events` | RuntimeObservability.emit | runtime.*-Events (whitelist ALL_RUNTIME_EVENTS) | observability.py:18-52 |
| P6 | EventStore.append() | `stored_events` | BridgeEventWriter.write_execution_event | Bridge-Execution (topic `bridge.execution`) | bridge_event_writer.py:28-68 |
| P7 | SQLite INSERT | `audit_log` | event_persistence-Plugin `_persist_event` | jede Bus-Publikation via `subscribe("*")` | features/observability/event_persistence.py:40-59 |
| P8 | SQLite DELETE | `audit_log` (Retention) | event_persistence-Plugin `_prune_old_events` | Registrierung; cutoff = now − 30d | event_persistence.py:29-38 |
| P9 | WriterThread | legacy `events`-Tabelle (derived copy) | WriterThread | jeder Event-Durchlauf mit event_store/WriterThread | writer.py:122-175 |

INFERENCE I1.1: Drei parallele persistente Event-Speicher existieren für denselben Bus-Stream (`stored_events`, `events`, `audit_log`) — deren Konsistenz zueinander ist kein Invariant (kein Code-Nachweis eines Abgleichs). Der einzige append-only-, sequenzielle und zertifizierte Pfad ist `stored_events` (P1–P6).

### 1.2 Produzierte Event-Topics (Bus) und ihre Persistenz

| Topic | Producer | Via Store persistiert? | FACT |
|-------|----------|------------------------|------|
| boot.init, kernel.initialized, plugins.initialized, runtime.initialized, runtime.skipped | muscal_os Boot-Phasen | ✅ (P1, wenn OS-Bus aktiv) | muscal_os.py:305-363 |
| os.started, os.stopped, os.simulate, os.executed | muscal_os | ✅ (P1) | muscal_os.py:100-186 |
| snapshot.loaded, snapshot.missing | muscal_os `_load_snapshot` | ✅ (P1) | muscal_os.py:391-397 |
| health.memory, health.graph, health.sphere, health.tools | muscal_os Health-Checks | ✅ (P1) | muscal_os.py:405-440 |
| graph.node_created, graph.node_updated, graph.edge_created, graph.execution_started, graph.execution_finished | graph→Bus-Spiegelung | ✅ (P1) | muscal_os.py:369-378 |
| EXECUTION_FAILED | ExecutionWatchdog | ❌ **nur Bus** (kein append) | execution_watchdog.py:96-119 |
| bridge.execution | BridgeEventWriter | ✅ (P6, direkt) | bridge_event_writer.py:10, 47-68 |
| runtime.* (whitelist) | RuntimeObservability | ✅ (P5, direkt) | observability.py:28-52 |
| SUPL_APPLICATION_* / supl.* | features/supl | ✅ (P4 via Adapter) / ⚠️ P1 | event_adapter.py; supl/event_integration.py:50 |
| Replay-Republikationen (beliebige Store-Topics) | ReplayService | ❌ (Republish mit `_replayed`-Marker; append unterdrückt `_replayed`-Payloads) | replay_service.py:34-38, 92-105; event_store.py:93-95 |

INFERENCE I1.2: Der Watchdog ist der einzige produktive Bus-Produzent ohne Store-Pfad (P1 fängt ihn nicht ab, weil er nur publish, nicht den OS-Bus mit `_persist_to_store` besitzt — er erhält `event_bus` als eigene Referenz, execution_watchdog.py:16-23).

### 1.3 Event-Schema-Felder im Store (vollständig)

FACT (event_store.py:50-67): `seq, topic, payload, source, priority, timestamp, event_id, created_at, execution_id, correlation_id, causation_id, execution_mode, execution_state, verification_state, is_replayed, receipt_id, schema_version`.

FACT (event_store.py:21-32): `_EXECUTION_REQUIRED_TOPICS` = {EXECUTION_STARTED, EXECUTION_FINISHED, TOOL_EXECUTED, SYSTEM_ACTION_STARTED, SYSTEM_ACTION_COMPLETED, SYSTEM_ACTION_FAILED, execution.receipt, execution.verification, VERIFICATION_PASSED, VERIFICATION_FAILED}; **EXECUTION_FAILED ist nicht enthalten**.

FACT (event_store.py:202-231): `store_verification()` erzwingt für `verified` receipt_id + execution_id (EvidenceRequiredError); Konflikt verified/failed → VerificationConflictError.

FACT (event_store.py:57, 121-149): doppelter `event_id` → sqlite3.IntegrityError (Idempotenz-Hebel).

---

## 2. MUTATION → EVENT MAPPING

### 2.1 GraphState-Mutationen (graph.py)

| # | Mutation | API | Erzeugtes Event (Bus-Topic) | Event-Felder | Vollständig? | FACT |
|---|----------|-----|------------------------------|--------------|--------------|------|
| M1 | Node erstellen | add_node | NODE_CREATED → `graph.node_created` | node_id, type, payload, timestamp, execution_id | ⚠️ ohne status/confidence-Initialwerte | graph.py:77-83 |
| M2 | Status/Confidence ändern | update_node | NODE_UPDATED → `graph.node_updated` | node_id, status, confidence, execution_id | ⚠️ **ohne payload-Delta** | graph.py:103-108 |
| M3 | Payload ändern | update_node(payload=…) | NODE_UPDATED (gleicher Event, **kein payload-Feld**) | — | ❌ **Payload-Änderung unsichtbar** | graph.py:100-108 |
| M4 | Edge erstellen | add_edge | EDGE_CREATED → `graph.edge_created` | source_id, target_id, edge_type | ⚠️ ohne payload, ohne timestamp | graph.py:124-128 |
| M5 | Node löschen | remove_node | **kein Event** | — | ❌ | graph.py:133-138 |
| M6 | Edge löschen | remove_edge | **kein Event** | — | ❌ | graph.py:140-143 |
| M7 | Pruning (MAX_NODES/MAX_EDGES) | prune_graph | **kein Event** | — | ❌ (Entfernungen unsichtbar) | graph.py:145-158 |
| M8 | Fokus setzen | set_focus | **kein Event** | — | ❌ | graph.py:162-166 |
| M9 | Beliebige Bus-Topics in Graph | graph.emit (via _bridge_to_graph) | direkt im Event-Stream (`graph.emit` → _push_event → Bus-Spiegel) | kompletter Topic-Name als Event-Typ | ✅ (Payload unverändert + `_source`) | muscal_os.py:384-389; graph.py:235-239 |
| M10 | Event-Stream-Trace | _push_event | `_update_stream` (flüchtig, letzte 50 via get_event_stream) | type, payload, timestamp | n/a (flüchtig) | graph.py:220-243 |

INFERENCE I2.1: M3 ist die kritischste Lücke mit Produktions-Beleg: kernel.py:152-156 ruft `update_node(nid, status=…, payload={"result": …})` auf — das Ergebnis des SYSTEM_ACTION geht im persistierten Event-Verlauf verloren.

### 2.2 Execution-/Kernel-Mutationen

| # | Mutation | Produzent | Event | Store? | FACT |
|---|----------|-----------|-------|--------|------|
| M11 | Execution-Start | kernel.py:595-648 | EVENT_EXECUTION_STARTED (graph.emit) | ✅ via Bus→Store (P1) | kernel.py:595 |
| M12 | Execution-Finish | kernel.py:392, 552 | EVENT_EXECUTION_FINISHED | ✅ (P1) | kernel.py:392, 552 |
| M13 | System-Action-Zyklus | system_runtime.py:95-111 | SYSTEM_ACTION_STARTED/COMPLETED/FAILED (graph.emit) | ✅ (P1); Topic ∈ _EXECUTION_REQUIRED_TOPICS | system_runtime.py; event_store.py:21-32 |
| M14 | Orphan-Fail | ExecutionWatchdog | EXECUTION_FAILED | ❌ nur Bus | execution_watchdog.py:107-119 |
| M15 | Verification | features/verification/orchestrator.py:171 | publish (Verification-Topic) | ⚠️ nur wenn Bus→Store verdrahtet | orchestrator.py:171 |
| M16 | Bridge-Execution | BridgeEventWriter | bridge.execution | ✅ (P6) | bridge_event_writer.py:47-68 |

### 2.3 Flüchtige Zustände ohne Event-Pfad

| # | Zustand | Halter | Mutation | Event? |
|---|---------|--------|----------|--------|
| M17 | EventBus._history (max 50.000, Overflow pop(0)) | EventBus | publish; Verlust ab Limit | ❌ (Verlust) | event_bus.py:54-57 |
| M18 | EventBus._topic_counts | EventBus | publish | ❌ (derivierbar) | event_bus.py:57 |
| M19 | Watchdog-Zähler (_warnings_issued, _orphans_resolved) | ExecutionWatchdog | _force_fail_orphan | ❌ | execution_watchdog.py:99-100, 121-128 |
| M20 | ReplayService._last_replayed_seq | ReplayService | replay_all/replay_since | ❌ (flüchtiger Cursor) | replay_service.py:20, 43-44 |
| M21 | GraphState._node_counter | GraphState | add_node | n/a (aus node_id derivierbar) | graph.py:65-66 |
| M22 | GraphState._replaying | GraphState | Rebuild-Modus | n/a (Kontroll-Flag) | graph.py:56, 226-229 |
| M23 | audit_log-Retention-Löschung | event_persistence | DELETE | ❌ (bewusste Löschung, 30d) | event_persistence.py:29-38 |
| M24 | Legacy memory.py / GraphMemory / memory_compressor / memory_rewriter | Core legacy | schreiben ohne Event-Feed | ❌ (orphaned, MEMORY_FABRIC_AUDIT §3) | MEMORY_FABRIC_AUDIT.md:33-36 |

---

## 3. MISSING EVENT MATRIX

| ID | Fehlendes Event / Feld | Betroffene Mutation | Konsequenz für Rekonstruktion | Severity | FACT |
|----|------------------------|---------------------|-------------------------------|----------|------|
| X-1 | NODE_UPDATED ohne payload-Delta | M3 | Rebuild rekonstruiert veraltete Node-Payloads (z. B. `result` von SYSTEM_ACTION geht verloren) | **HIGH** | graph.py:103-108; kernel.py:152-156 |
| X-2 | Kein NODE_REMOVED | M5 | Rebuild behält gelöschte Knoten | **HIGH** | graph.py:133-138 |
| X-3 | Kein EDGE_REMOVED / Prune-Marker | M6, M7 | Rebuild wächst über MAX_NODES/MAX_EDGES bzw. behält Kanten, die gelöscht wurden | **HIGH** | graph.py:140-158 |
| X-4 | Kein FOCUS_CHANGED | M8 | active_focus_node nach Rebuild falsch (leer) | MEDIUM | graph.py:162-166 |
| X-5 | NODE_CREATED ohne status/confidence-Initialwerte | M1 | Nodes mit confidence ≠ 1.0/status ≠ „created" verlieren Initialwert | MEDIUM | graph.py:77-83 |
| X-6 | EDGE_CREATED ohne payload/timestamp | M4 | Edge-Payloads verloren; zeitliche Kanten-Reihenfolge nur über seq | MEDIUM | graph.py:124-128 |
| X-7 | Watchdog: kein append (EXECUTION_FAILED nur Bus) | M14 | Orphan-Erkennungen nach Restart verloren; C03-Doppelalarme | HIGH | execution_watchdog.py:107-119 |
| X-8 | EXECUTION_FAILED nicht in _EXECUTION_REQUIRED_TOPICS | M14 | append ohne execution_id wäre technisch möglich (kein Schutz) | LOW | event_store.py:21-32 |
| X-9 | ReplayCursor flüchtig | M20 | Rebuild ab „letztem Stand" nicht möglich; nur Full-Replay | MEDIUM | replay_service.py:20 |
| X-10 | EventBus-History-Overflow (pop 0) | M17 | In-Memory-Verlust ab 50.000; Store bleibt Quelle (falls P1 aktiv) | LOW | event_bus.py:54-57 |
| X-11 | audit_log-Retention-Delete | M23 | 30d-Grenze — Audit-Spur nicht append-only | MEDIUM | event_persistence.py:29-38 |
| X-12 | Doppel-Persistenz ohne Abgleich (stored_events vs events vs audit_log) | P2, P7, P9 | Identische Bus-Nachricht in 3 Tabellen; kein Konsistenz-Invariant | MEDIUM | writer.py:110-173; event_persistence.py:40-55 |
| X-13 | memory.py-/GraphMemory-Mutationen ohne Event-Feed | M24 | Memory-Wahrheit nicht rekonstruierbar aus Events | LOW (legacy) | MEMORY_FABRIC_AUDIT.md:33-36 |

---

## 4. RECONSTRUCTION FEASIBILITY SCORE

Methodik (INFERENCE): Score je Zustandsbereich = Anteil der für vollständige Rekonstruktion benötigten Felder/Mutationen, die aus `stored_events` (append-only, seq-geordnet) ableitbar sind. Scores sind Modell-Kennzahlen aus Code-Beleg, keine Messungen.

| Bereich | Benötigt | Im Store ableitbar | Fehlend | Score |
|---------|----------|--------------------|---------|-------|
| S-1 Nodes: id, type, payload, timestamp, execution_id | 5 Felder | ✅ NODE_CREATED | — | **100%** |
| S-2 Nodes: status, confidence | 2 Felder | ⚠️ nur wenn je via NODE_UPDATED gesetzt; Initialwert (≠1.0) nicht | X-5 | **50%** |
| S-3 Nodes: payload-Updates | 1 | ❌ | X-1 | **0%** |
| S-4 Edges: source, target, type | 3 | ✅ EDGE_CREATED | — | **100%** |
| S-5 Edges: payload, timestamp | 2 | ❌ | X-6 | **0%** |
| S-6 Node/Edge-Entfernungen (inkl. Prune) | 1 | ❌ | X-2, X-3 | **0%** |
| S-7 active_focus_node | 1 | ❌ | X-4 | **0%** |
| S-8 node_id-Zuweisung (Counter-Reihenfolge) | 1 | ✅ (seq + deterministische Counter-Logik) | — | **100%** |
| S-9 Execution-Flow (Started/Finished/System-Actions) | 3 Topics | ✅ (∈ _EXECUTION_REQUIRED_TOPICS bzw. P1) | — | **100%** |
| S-10 Watchdog-Erkennungen | 1 | ❌ (nur Bus) | X-7 | **0%** |
| S-11 Bridge-Execution | 1 | ✅ (P6) | — | **100%** |
| S-12 OS-Lifecycle/Health | 1 | ✅ (P1) | — | **100%** |

**Gesamt-Graph-Rekonstruktion (S-1…S-8, gewichtet je Feld):**
- Vollständige Nodes/Kanten-Konstruktion (Struktur): **~78%** (8 von 13 Feldgruppen vollständig: 100+100+100+100+100+0+0+0+100 über 8 Gruppen → struktur-relevant 6/8 = 75–100%)
- Exakte Zustands-Wiederherstellung inkl. Payloads/Status/Entfernungen: **~46%** (6 von 13 Score-Punkten zu 100% ableitbar, 7 zu 0% → 6/13 = 46,2%)

INFERENCE I4.1: Der Graph ist als **Struktur** (Knoten/Kanten-Gerüst, IDs, Typen) gut rekonstruierbar; als **Zustand** (Payloads, Status, Fokus, Entfernungen) unvollständig. Der „vollständige Reconstruction/Hydration Flow" (P0-1) benötigt zwingend X-1…X-4.

| Szenario (RC-1a) | Erwarteter Gesamt-Score | Begründung | Marke |
|------------------|------------------------|------------|-------|
| A — EventStore Single Truth | Struktur ~78% / Zustand ~46% ohne Erweiterungen; mit X-1…X-6 → >90% | Rebuild kann nur das rekonstruieren, was im Log steht | INFERENCE |
| B — Dual Truth | Rekonstruktion aus Store allein nicht ausreichend; Live-State als zweite Quelle nötig (Drift-Risiko) | zwei Wahrheiten, keine Reconciliation-Invariante im Code | INFERENCE |
| C — Reconstruction Layer | gleiche Logik wie A; Layer könnte X-1…X-6 als Mapping-Regeln verarbeiten | Layer verbessert Wiederverwendbarkeit, nicht Log-Inhalt | INFERENCE |

---

## 5. MINIMAL REQUIRED EVENT EXTENSIONS

Nur Katalog — **keine Empfehlung, keine Priorisierung, keine Umsetzung**. Jede Extension schließt eine oben belegte Lücke; Gültigkeit erst nach Entscheidung.

| ID | Extension | Schließt | Technischer Anker (FACT) |
|----|-----------|----------|--------------------------|
| E-1 | NODE_UPDATED-Event um `payload` (vollständig oder Delta) erweitern | X-1 | graph.py:103-108 — payload-Feld ergänzbar, ohne Core-Schema-Bruch? → Prüfung durch Entscheider/Agent |
| E-2 | NODE_REMOVED-Event bei remove_node() | X-2 | graph.py:133-138 — Event-Push analog _push_event |
| E-3 | EDGE_REMOVED-Event bei remove_edge() + Prune-Marker (z. B. `PRUNE_BOUNDARY` mit seq-Grenze) | X-3 | graph.py:140-158 |
| E-4 | FOCUS_CHANGED-Event bei set_focus() | X-4 | graph.py:162-166 |
| E-5 | NODE_CREATED um `status`/`confidence`-Initialwerte | X-5 | graph.py:77-83 |
| E-6 | EDGE_CREATED um `payload`/`timestamp` | X-6 | graph.py:124-128 |
| E-7 | Watchdog: `_force_fail_orphan()` zusätzlich `EventStore.append()` via EventStoreAdapter; `event_id` = deterministischer Idempotenz-Key (z. B. `orphan_{execution_id}`), der `event_id UNIQUE` als Dedup nutzt | X-7, X-8 | execution_watchdog.py:96-119; event_adapter.py:80-85; event_store.py:57 |
| E-8 | Replay-Cursor persistieren (z. B. eigene Store-Topic) für inkrementellen Rebuild | X-9 | replay_service.py:20, 84-90 |
| E-9 | Konsistenz-Invariant/Abgleich zwischen `stored_events`, `events`, `audit_log` definieren (kein Verschmelzen — D-008) | X-12 | writer.py:110-173; event_persistence.py:40-55 |
| E-10 | EXECUTION_FAILED in _EXECUTION_REQUIRED_TOPICS aufnehmen (execution_id-Pflicht) | X-8 | event_store.py:21-32 |

INFERENCE I5.1: E-1…E-6 berühren den CORE (graph.py = immutable, D-020) — jede dieser Erweiterungen benötigt ARCHITECTURE CHANGE + OVERRIDE-Pfad oder einen features/-Projektions-Ansatz. E-7 liegt außerhalb des CORE (features/monitoring/, D-006-konform).

---

## Validation

- Read-only: keine Datei verändert, kein Commit, keine Empfehlung, kein Score als Messung ausgegeben (Scores sind Ableitungen aus Code-Beleg).
- Alle FACT mit Datei:Zeile; INFERENCE/HYPOTHESIS gekennzeichnet; keine neuen Behauptungen ohne Beleg.
- Ergänzt ARB_DECISION_SIMULATION_REPORT (R2 → hier X-1…X-4, E-1…E-6) und RC6_ARCHITECTURE_DECISION_READINESS_REPORT (Watchdog-Befund → hier X-7, E-7).
