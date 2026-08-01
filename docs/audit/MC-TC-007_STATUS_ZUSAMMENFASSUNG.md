# MC-TC-007 — Vollständige Status-Zusammenfassung für AI-Übergabe

## Projekt: MUSCAL CORE

Ein modulares AI-Agent-System in Python. Kern ist ein Event-Sourcing-System mit
SQLite-basierter EventStore-Komponente. Ort: `/home/hz/AlitaProject/Codebase/MUSCAL CORE/`

---

## Abgeschlossene Audits

### MC-TC-005.3 — Single Event Authority Consolidation ✅ COMPLETE
- `EventStore → stored_events` table wurde als **einzige kanonische Event-Authorität** etabliert
- Die legacy `events` Tabelle ist eine **abgeleitete Read-Only-Projection**
- `WriterThread` delegiert zuerst an `EventStore.append()`, dann an legacy `events`
- `EventBus.swap_subscriber()` für atomaren Austausch ohne Event-Verlust
- 51 Tests: alle ✅

### MC-TC-006 — Replay & Deterministic Reconstruction ✅ CERTIFIED
- **Deterministisches Replay** aus `stored_events` allein (ohne `events` Tabelle)
- **Crash Recovery**: 6/6 Szenarien getestet ✅
- **Kausalketten**: Vollständig rekonstruierbar ✅
- **Semantischer Hash**: Identisch über 3 Runs ✅
- **Failure Matrix**: 6/6 Fehlermodi ✅
- Report: `docs/audit/MC-TC-006-REPLAY-DETERMINISTIC-RECONSTRUCTION-CERTIFICATION.md`

### MC-TC-007 — Full Reality Closure ⚠️ CONDITIONAL GO (aktuell)

---

## MC-TC-007: Detail-Ergebnisse

### ✅ Bestanden (12/14 Kriterien)

| Phase | Ergebnis | Beschreibung |
|-------|----------|-------------|
| A — Cold Boot Reconstruction | ✅ PASS | Live-Zustand == Replayed-Zustand (semantischer Hash identisch) |
| B — Replay → Continue → Replay | ✅ PASS | Replay(A) + Continue(B) == Frisches(A+B) |
| C — Receipt Persistence | ✅ PASS | Alle Receipt-Felder überleben Restart |
| D — Verification Persistence | ✅ PASS | Alle 5 Status (VERIFIED/FAILED/INCONCLUSIVE/NOT_SUPPORTED/TAMPERED) |
| E — Timeout Reality Closure | ✅ PASS | Timeout → Receipt → terminaler "failed"-State |
| F — Watchdog Recovery | ✅ PASS* | Orphans erkannt, aber **Events nicht in EventStore persistiert** |
| G — Identity & Causality | ✅ PASS | Vollständige Kausalkette über Restart hinweg |
| I — Failure Injection | ✅ PASS | 11/11 Szenarien graceful |
| J — Full Reality Equivalence | ✅ PASS | H_live == H_replayed == H_restarted == H_continued |
| K — Production Boot Matrix | ✅ PASS | Alle 6 Boot-Pfade konvergieren auf EventStore |
| L — Test Integrity | ✅ PASS | 384/384 Tests bestanden |
| 0 — Repository Reconnaissance | ✅ COMPLETE | Vollständige Topologie-Karte erstellt |

### ❌ Nicht bestanden (2/14 Kriterien)

| Phase | Ergebnis | Problem |
|-------|----------|---------|
| H — Graph-OS Reconstruction | ❌ FAIL | **P0: GraphState/SphereState sind rein in-memory — kein Rebuild-Mechanismus** |
| 12 — Keine neuen P0/P1 | ❌ FAIL | 2 neue P0 + 4 neue P1 gefunden |

---

## Contradiction Register (offene Probleme)

### P0 — Kritisch (muss vor FULL GO gelöst werden)

**C01 — Graph-OS nicht rekonstruierbar** (aus Phase H)

- `GraphState.nodes` und `GraphState.edges` sind `dict`/`list` in memory
- **KEINE** Methode `rebuild_from_replay()` oder `restore_from_event_store()` existiert
- Graph-Events (NODE_CREATED, EDGE_CREATED usw.) WERDEN in `stored_events` persistiert — die Daten sind da, aber es gibt keinen Code, der sie zurückliest
- `SphereState` ist eine reine Projektion von `GraphState` → ebenfalls verloren
- Impact: Bei jedem Prozess-Neustart ist der Graph-Zustand leer (keine Execution-History, kein Sphere-Kontext)

**C02 — Watchdog-Events nicht in EventStore** (aus Phase F)

- `ExecutionWatchdog._force_fail_orphan()` ruft NUR `event_bus.publish()` auf
- Es gibt **KEINEN** `event_store.append()` Aufruf
- EXECUTION_FAILED-Events erscheinen nur dann in EventStore, wenn ein EventBus→EventStore-Subscriber aktiv ist (was bei Crash-Szenarien nicht garantiert ist)
- Datei: `features/monitoring/execution_watchdog.py`, Zeile 96–119

### P1 — Wichtig (sollte gelöst werden)

**C03 — Watchdog erkennt denselben Orphan mehrfach**

- Nach der ersten Detektion wird `execution_state` nicht auf `"failed"` aktualisiert
- Bei jedem Poll (default 30s) wird derselbe Orphan erneut detektiert
- Im Test: 20 Detektionen in <2s

**C04 — Future.cancel() verhindert WriterThread nicht**

- Wenn ein Tool-Future gecancelled wird, wird das Event dennoch von WriterThread in EventStore geschrieben
- Die Queue-Verarbeitung ist unabhängig vom Future-Status
- Folge: Es können "Geister-Events" ohne zugehörige Execution erscheinen
- Datei: `runtime/kernel/writer.py`, Zeile 57–79

**C05 — Kein Boot-Pfad ruft EventStore.replay() auf**

- Obwohl MC-TC-006 deterministisches Replay bewiesen hat, ruft KEINE Boot-Sequenz `replay()` auf
- Selbst wenn C01 gelöst wird (Graph-OS Rebuild), wird es nie aufgerufen
- Datei: `muscal_os.py`, `supervisor.py`, `enriched_bootstrap.py`

**C06 — UTR in-memory Stores werden nicht neu befüllt**

- `UnifiedToolRuntime._receipt_store`, `_execution_store`, `_verification_store` sind `dict`s
- Nach Neustart sind alle leer
- Kanonische Daten existieren in `stored_events`, aber die Caches sind kalt
- Datei: `features/tool_runtime/tool_runtime.py`, Zeilen 344–347

---

## Technische Architektur (für AI-Navigation)

### Wichtige Dateien

| Datei | Zweck |
|-------|--------|
| `runtime/event_store.py` | **Kern**: SQLite-basierter EventStore mit `append()`, `replay()`, `store_receipt()`, `store_verification()` |
| `runtime/database.py` | Datenbank-Connection-Factory, Schema-Initialisierung |
| `runtime/kernel/writer.py` | WriterThread — Dual-Write (EventStore + legacy events) |
| `event_bus.py` | EventBus mit publish/subscribe/swap_subscriber |
| `muscal_os.py` | OS-Boot-Orchestrator (5 Phasen), erzeugt EventStore + EventBus + Kernel |
| `features/bootstrap/enriched_bootstrap.py` | EnrichedMuscalOS — Production-Wrapper mit Kontext-Anreicherung |
| `supervisor.py` | Production Supervisor — orchestriert OS + API-Runtime |
| `features/tool_runtime/tool_runtime.py` | UTR, ExecutionReceipt, VerificationResult, globale EventStore-Registry |
| `features/tool_runtime/receipt_store.py` | ReceiptStore (in-memory), FileReceiptStore (JSON-Dateien) |
| `features/monitoring/execution_watchdog.py` | ExecutionWatchdog — erkennt orphans via EventStore-Scan |
| `features/boot/utr_wiring.py` | Boot-Plugin — verdrahtet globale EventStore, Watchdog, Verifier |
| `features/identity/execution_context.py` | ExecutionContext, ContextManager, EventIdentity |
| `features/provenance/context.py` | ProvenanceContext (trace_id, span_id, decision_id via contextvars) |
| `features/identity/uuid7.py` | UUID v7 Generator |
| `graph.py` | GraphState — in-memory Graph (KEIN Rebuild!) |
| `sphere.py` | SphereState — radiale Projektion des Graphen |
| `kernel.py` | MuscalKernel — erzeugt GraphState + SphereState |
| `features/verification/orchestrator.py` | VerificationOrchestrator |
| `config.py` | DB_PATH, SESSION_ID |
| `os_config.py` | MuscalConfig, DeploymentMode |

### Event-Datenfluss (korrekt)

```
Producer → WriterThread.submit() → EventStore.append() → stored_events [CANONICAL]
                                      ↓
                                   events [DERIVED READ MODEL]

EventBus.publish() → _persist_to_store() → EventStore.append() → stored_events
                  → _bridge_to_graph() → GraphState (in memory)

tool_runtime.execute() → ExecutionReceipt
                      → EventStore.store_receipt() → stored_events
                      → VerificationResult
                      → EventStore.store_verification() → stored_events
```

### Event-Datenfluss (Lücken — was NICHT passiert)

```
stored_events → [❌ KEIN Boot-Pfad ruft replay() auf]
GraphState    → [❌ KEIN rebuild_from_replay()]
UTR Stores    → [❌ KEINE Befüllung aus stored_events]
Watchdog      → [❌ KEIN event_store.append() bei Orphan-Auflösung]
```

### stored_events Schema

```sql
stored_events (
    seq        INTEGER PRIMARY KEY AUTOINCREMENT,
    topic      TEXT NOT NULL,
    payload    TEXT NOT NULL DEFAULT '{}',   -- JSON
    source     TEXT NOT NULL DEFAULT '',
    priority   TEXT NOT NULL DEFAULT 'NORMAL',
    timestamp  REAL NOT NULL,
    event_id   TEXT NOT NULL UNIQUE,
    created_at TEXT NOT NULL,
    execution_id TEXT NOT NULL DEFAULT '',
    correlation_id TEXT NOT NULL DEFAULT '',
    causation_id TEXT NOT NULL DEFAULT '',
    execution_mode TEXT NOT NULL DEFAULT 'real',
    execution_state TEXT NOT NULL DEFAULT 'planned',
    verification_state TEXT NOT NULL DEFAULT 'unverified'
)
```

### Identity-Felder

```
request_id → plan_id → step_id → execution_id → receipt_id → verification_id
                                 ↓
                 causation_id → correlation_id → retry_count → attempt_number
                                 ↓
            cognitive_unit_id → agent_id → model_id → trace_id → span_id → decision_id
```

---

## Nächste Schritte (Minimal für FULL GO)

### Schritt 1: Graph-OS Rebuild (C01 lösen)
1. `GraphState.rebuild_from_replay(event_store)` implementieren in `graph.py`
   - `event_store.replay()` aufrufen
   - Events nach NODE_CREATED, EDGE_CREATED filtern
   - `self.nodes[node_id] = Node(...)` rekonstruieren
   - `self.edges.append(Edge(...))` rekonstruieren
2. `SphereState.rebuild()` implementieren — basiert auf GraphState
3. In `muscal_os.py` Boot-Phase START_SERVICES oder HEALTH_CHECK einhängen

### Schritt 2: Watchdog-Persistenz (C02 lösen)
1. In `features/monitoring/execution_watchdog.py`, `_force_fail_orphan()`:
   - Nach `event_bus.publish()` auch `event_store.append()` mit EXECUTION_FAILED aufrufen
   - Oder Watchdog-Events immer direkt in EventStore schreiben

### Schritt 3: Watchdog-Idempotenz (C03 lösen)
1. Nach Orphan-Detektion: `event_store.append()` mit aktualisiertem execution_state = "failed"
   - Oder: In-Memory-Set `_detected_orphans` führen

### Schritt 4: Boot-Replay (C05 lösen)
1. In `muscal_os._start_services()` oder `_health_check()`:
   - `event_store.replay()` aufrufen
   - Events an Graph-Rebuild weiterleiten

### Schritt 5: UTR-Cache-Befüllung (C06 lösen)
1. `create_default_utr()` oder `EnrichedMuscalOS._init_trust_core()`:
   - Nach EventStore-Init: `replay()` für receipt/verification-Events
   - `_receipt_store` und `_verification_store` befüllen

---

## Test-Befehle

```bash
cd "/home/hz/AlitaProject/Codebase/MUSCAL CORE"

# MC-TC-007 Audit-Skript (Phasen A–J)
python3 /tmp/audit_mc_tc_007_full_reality.py

# MC-TC-006 Crash-Recovery
python3 /tmp/audit_mc_tc_006_phase_f.py

# Alle relevanten Tests
python3 -m pytest tests/test_mc_tc_005_3_single_event_authority.py \
                  tests/test_event_store.py \
                  tests/test_replay_service.py \
                  tests/test_canonical_authority.py \
                  tests/test_cross_boot_trust_core.py \
                  tests/test_utr_timeout.py \
                  tests/test_receipt_serialization.py -v
```

---

## Audit-Artefakte (für AI-Referenz)

| Artefakt | Pfad |
|----------|------|
| MC-TC-007 Report | `docs/audit/MC-TC-007-FULL-REALITY-CLOSURE-CERTIFICATION.md` |
| MC-TC-007 Checks (A–J) | `/tmp/audit_mc_tc_007_full_reality.py` |
| MC-TC-006 Report | `docs/audit/MC-TC-006-REPLAY-DETERMINISTIC-RECONSTRUCTION-CERTIFICATION.md` |
| MC-TC-006 Phase F | `/tmp/audit_mc_tc_006_phase_f.py` |
| MC-TC-005.3 Report | `docs/audit/MC-TC-005.3-SINGLE-EVENT-AUTHORITY-CONSOLIDATION.md` |
| MC-TC-005.3 Tests | `tests/test_mc_tc_005_3_single_event_authority.py` |
| AGENTS.md | `AGENTS.md` (Core ist READ-ONLY) |
| Session-Regeln | `.opencode/SESSION_RULES.md` |
| Architecture Override | `spec/OVERRIDE.md` |

---

## Endergebnis

**EventStore-Layer:** ✅ CERTIFIED (Replay, Receipts, Verifications, Causal Chains, Timeouts, Crash Recovery — alles deterministisch und restart-sicher)

**Graph-OS-Layer:** ❌ NOT CERTIFIED (In-memory only, kein Rebuild-Mechanismus)

**Watchdog-Layer:** ⚠️ PARTIELL (Erkennt Orphans, aber persistiert nicht in EventStore)

**Gesamt: CONDITIONAL GO** — Produktion kann starten, aber Graph-OS-Zustand geht bei jedem Restart verloren, und Watchdog-Resolution-Events überleben nicht.
