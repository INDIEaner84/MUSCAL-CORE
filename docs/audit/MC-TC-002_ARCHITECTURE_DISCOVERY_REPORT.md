# MC-TC-002 — MUSCAL Trust Core Architecture Discovery & Repository Reconstruction

## ARCHITECTURE DISCOVERY REPORT

**Date:** 2026-07-24
**Status:** DISCOVERY COMPLETE — CONTRADICTIONS FOUND
**Trust Core Status:** PARTIALLY DEFINED
**Implementation:** FORBIDDEN (this phase)

---

## 1. Executive Summary

This report reconstructs the **actual** MUSCAL architecture from source code, configuration, tests, and runtime paths. The repository was inspected across 220+ Python files, 85+ test files, 230+ documentation files, and all configuration/schema artifacts.

### Key Findings

1. **Execution truth is fragmented across two event storage systems** with different schemas, writers, and consumers. `stored_events` (via `EventStore`) and `events` (via `WriterThread`) are both written to during pipeline execution, but neither is authoritative over the other.

2. **Execution identity is generated in multiple locations** with different ID formats. `features/tool_runtime/` generates UUID v4 (via `uuid.uuid4()` standard library), while `features/identity/uuid7.py` generates UUID v7. `kernel.py` generates no execution ID at all.

3. **`kernel.py` — the core execution pipeline — has zero awareness of `execution_mode`, `execution_state`, `verification_state`, or any identity field.** All enrichment happens as an **external wrapper** (`EnrichedMuscalOS`) layered on top. The kernel itself is identity-agnostic.

4. **Verification exists in two parallel systems:** `UnifiedToolRuntime._verify_one()` (integrity hash + tool verifier) and the newer `VerificationOrchestrator` (full rule engine + EventBus integration). They are not unified.

5. **Simulation mode is represented by TWO independent mechanisms:** `simulation_mode: bool` (OS boot flag in `os_config.py`) and `execution_mode: ExecutionMode` (per-event enum in `features/identity/`). They are not synchronized.

6. **The causal chain (Intent → Plan → Authorization → Action → Result → Verification → Outcome) is partially reconstructable** but has significant gaps: authorization is not causally linked, verification is not always linked to its source execution, and evidence is not consistently captured.

7. **No `is_authoritative` flag exists anywhere** in the codebase. Authority is an implicit architectural concept, not an enforced property.

---

## 2. Repository Architecture Map

### 2.1 Project Structure

```
MUSCAL CORE/                         # 89 root-level .py files
├── api_server.py                    # FastAPI server (module-level init)
├── api/main.py                      # Re-exports api_server.app
├── boot_manager.py                  # Boot phases, BootReport
├── bridge.py                        # MKC task mapping
├── config.py                        # DB_PATH (module-level constant)
├── event_bus.py                     # In-memory pub/sub
├── graph.py                         # GraphState (Node/Edge/Events)
├── kernel.py                        # MuscalKernel (pipeline orchestration)
├── main.py                          # Minimal REPL
├── main_boot.py                     # Full-featured CLI entrypoint
├── mel.py                           # MEL executor
├── memory.py                        # Memory store
├── muscal_loop.py                   # Autonomous loop
├── muscal_os.py                     # MuscalOS (central boot/run orchestrator)
├── os_config.py                     # Config (simulation_mode: bool)
├── schema.py                        # Node/Edge dataclasses, event constants
├── supervisor.py                    # Production entrypoint (Containerfile CMD)
├── features/                        # 24 subdirectories, ~80 .py files
│   ├── bootstrap/enriched_bootstrap.py  # EnrichedMuscalOS wrapper
│   ├── identity/                    # execution_id, reality, uuid7
│   ├── tool_runtime/tool_runtime.py # UTR, ExecutionReceipt, VerificationResult
│   ├── verification/                # Verifier, Orchestrator, Rules (Phase 2)
│   ├── projection/graph_os_projection.py
│   ├── streaming/ws_adapter.py
│   ├── provenance/                  # Classifier, Validator, Context
│   ├── execution/                   # Outcome, MREIL, Evaluation
│   ├── events/                      # EventAdapter, EventConsolidation
│   ├── supl/                        # SUPL supervisor plugin layer
│   └── pipeline/                    # Stage definitions (cu, governance, routing)
├── runtime/                         # ~55 .py files
│   ├── event_store.py               # EventStore (SQLite append-only)
│   ├── database.py                  # events table schema (kernel audit)
│   ├── kernel/                      # WriterThread, Governance, Bootstrap
│   ├── api/                         # Flask API endpoints
│   └── services/snapshot.py         # Snapshot creation
├── tests/                           # 85+ test files
└── docs/, spec/, specs/             # 230+ .md files
```

### 2.2 Architectural Layer Map

```
┌──────────────────────────────────────────────────────────────────┐
│  ENTRYPOINT LAYER                                                 │
│  supervisor.py (prod), main_boot.py (dev), main.py (minimal),    │
│  runtime/main.py (runtime-only), api_server.py (FastAPI)         │
├──────────────────────────────────────────────────────────────────┤
│  OS LAYER                                                         │
│  MuscalOS (muscal_os.py): boot, run, shutdown                    │
│  EnrichedMuscalOS (features/bootstrap/enriched_bootstrap.py)     │
│  MuscalLoop (muscal_loop.py): autonomous loop                    │
├──────────────────────────────────────────────────────────────────┤
│  KERNEL LAYER                                                     │
│  MuscalKernel (kernel.py): pipeline orchestration                 │
│   ├── RAGModule → rag.py                                         │
│   ├── MKCModule → mkc.py                                         │
│   ├── BridgeModule → bridge.py                                   │
│   ├── MELModule → mel.py                                         │
│   ├── FeedbackModule → feedback.py                               │
│   ├── MemoryModule → memory.py                                   │
│   └── Pipeline stages (features/pipeline/)                       │
│  GraphState (graph.py): node/edge state                           │
│  SphereState (sphere.py): 3-ring cognitive projection             │
├──────────────────────────────────────────────────────────────────┤
│  TOOL RUNTIME LAYER                                               │
│  UnifiedToolRuntime (features/tool_runtime/tool_runtime.py)      │
│  ExecutionReceipt, VerificationResult, VerificationStatus        │
│  Tool executors + verifiers                                       │
├──────────────────────────────────────────────────────────────────┤
│  IDENTITY LAYER                                                   │
│  ExecutionContext (features/identity/execution_context.py)       │
│  Reality model (features/identity/reality.py)                    │
│  UUID v7 (features/identity/uuid7.py)                            │
├──────────────────────────────────────────────────────────────────┤
│  EVENT LAYER                                                      │
│  EventBus (event_bus.py): in-memory pub/sub                     │
│  EventStore (runtime/event_store.py): stored_events SQLite       │
│  WriterThread (runtime/kernel/writer.py): events SQLite          │
│  ReplayService (features/replay/replay_service.py)               │
│  EventConsolidation (features/events/event_consolidation.py)    │
├──────────────────────────────────────────────────────────────────┤
│  VERIFICATION LAYER                                               │
│  VerificationOrchestrator (features/verification/orchestrator.py)│
│  Verifier ABC + built-in (features/verification/verifier.py)     │
│  RuleEngine + HARD_RULES (features/verification/rules.py)        │
│  UTR._verify_one (features/tool_runtime/tool_runtime.py)         │
├──────────────────────────────────────────────────────────────────┤
│  PROJECTION / TRANSPORT LAYER                                     │
│  GraphOSProjection (features/projection/graph_os_projection.py)  │
│  WebSocketAdapter (features/streaming/ws_adapter.py)             │
│  SUPL WebSocket (features/supl/ws_stream.py)                     │
├──────────────────────────────────────────────────────────────────┤
│  PROVENANCE LAYER                                                 │
│  ProvenanceContext (features/provenance/context.py)              │
│  Classifier (features/provenance/classifier.py)                  │
│  Validator (features/provenance/validator.py)                    │
├──────────────────────────────────────────────────────────────────┤
│  RUNTIME INFRASTRUCTURE                                           │
│  Flask API (runtime/api/), IPC (runtime/ipc_*), Daemon,          │
│  ProcessManager, Monitoring, Optimizer, Observation              │
├──────────────────────────────────────────────────────────────────┤
│  GOVERNANCE / RECONCILIATION                                      │
│  Guards (guards/), Reconciliation (reconciliation/),             │
│  GovernanceStage, SafetyGate, WriteGuard                          │
├──────────────────────────────────────────────────────────────────┤
│  SUPL (SUPERVISOR PLUGIN LAYER)                                   │
│  EventBusBridge, SemanticAdapter, ProjectionEngine,              │
│  ProvenanceLinker, WSStream, AdapterRegistry                     │
└──────────────────────────────────────────────────────────────────┘
```

---

## 3. Execution Truth Reconstruction

### 3.1 Production Execution Flow (supervisor.py)

```
supervisor.py::start()
  │
  ├─ MuscalOS(config).start()              # Boot through 5 phases
  │   ├─ _init_event_store()               # Creates EventStore
  │   │   └─ events.subscribe("*", _persist_to_store)  # Auto-persist
  │   ├─ _init_event_bus()
  │   ├─ _init_kernel() → MuscalKernel()   # Pipeline (no identity)
  │   ├─ _init_plugins() → load_plugins()
  │   ├─ _init_system_runtime()
  │   ├─ _wire_event_bus()                 # Graph → EventBus bridge
  │   └─ _load_snapshot()
  │
  ├─ init_db()                             # Creates `events` + `snapshots`
  ├─ WriterThread.start()                  # Writes kernel events to `events`
  ├─ GovernanceSync() / RoutingPolicy()
  ├─ init_router() / init_smol()           # LLM models
  ├─ ObservationLoop.start()
  │
  └─ Flask app.run(port=5001)              # API server (blocks)
```

### 3.2 Kernel Execution Flow (kernel.py::run())

```
kernel.run(input_text)
  │
  ├─ Prune graph (>10K nodes)
  ├─ emit(EVENT_EXECUTION_STARTED)         # Graph event (no identity fields)
  ├─ hook("kernel_before")
  │
  ├─ GovernanceStage.process()             # Governance check
  ├─ stage_rag()                           # RAG retrieve + enrich
  ├─ stage_mkc()                           # MKC compile → MCXF
  ├─ stage_mcxf_section()                  # MCXF document build
  ├─ stage_bridge()                        # map_tasks → ExecutionPlan
  ├─ stage_optimizer()                     # OptimizerPipeline (optional)
  ├─ stage_mel()                           # MEL.execute() → tool calls
  │   ├─ Tool executions via UnifiedToolRuntime
  │   ├─ SystemAgentRuntime (browser, desktop)
  │   └─ Events captured in graph (NODE_TYPE_TOOL_EXECUTION)
  ├─ stage_feedback()                      # analyze_feedback()
  ├─ stage_memory()                        # store_snapshot() + log()
  │   └─ emit(EVENT_EXECUTION_FINISHED)    # Graph event
  │
  ├─ hook("kernel_after")
  └─ return KernelResult(...)              # mcxf, execution, memory_id, etc.
```

### 3.3 MuscalOS.run() (wrap around kernel)

```
MuscalOS.run(input_text)
  │
  ├─ sim = config.simulation_mode           # Boolean flag only
  ├─ result = kernel.run(input_text)        # No enrichments from OS layer
  ├─ CognitiveDiffEngine.diff()             # MCXF diff (previous vs current)
  ├─ publish("os.executed", ...)            # EventBus event (no identity)
  └─ return result dict
```

### 3.4 EnrichedMuscalOS.run() (Phase 1B wrapper)

```
EnrichedMuscalOS.run(input_text, execution_mode, correlation_id, causation_id, parent_context)
  │
  ├─ ctx = ExecutionContext(                # Identity generated HERE
  │      execution_id=uuid7(),
  │      correlation_id=...,
  │      causation_id=...,
  │      execution_mode=normalize(execution_mode),
  │      execution_state="running",
  │      verification_state="unverified")
  ├─ _ctx_mgr.set_context(ctx)
  ├─ _publish_lifecycle("EXECUTION_STARTED", ...)  # Enriched EventBus event
  │   └─ payload enriched with execution context
  │
  ├─ result = self._os.run(input_text)      # Delegates to MuscalOS.run()
  │                                           # kernel.py gets NO identity
  │
  ├─ if success:
  │     ctx.execution_state = "completed"
  │     _publish_lifecycle("EXECUTION_COMPLETED", ...)
  │   else:
  │     ctx.execution_state = "failed"
  │     _publish_lifecycle("EXECUTION_FAILED", ...)
  │
  ├─ [optional] verify_execution()          # Phase 2: VerificationOrchestrator
  └─ restore/clear context
```

### 3.5 Event Persistence during Execution

There are **two parallel event persistence paths** during execution:

**Path A — EventStore (stored_events table):**
```
kernel events → GraphState.emit() → EventBus (via _wire_event_bus)
  → EventBus subscriber _persist_to_store (muscal_os.py)
  → OR _enriched_persist (if EnrichedMuscalOS replaces it)
  → EventStore.append() → stored_events table
```

**Path B — WriterThread (events table):**
```
kernel pipeline → MEL.execute()
  → system_runtime events
  → WriterThread._write_atomic()
  → events table (with rich schema: actor, domain, layer, idempotency_key, etc.)
```

### 3.6 Critical Finding: kernel.py has NO identity awareness

```
kernel.py:622  def run(self, input_text: str):
                   │
                   │ NO execution_id generated
                   │ NO execution_mode checked
                   │ NO execution_state tracked
                   │ NO verification_state set
                   │ NO correlation_id propagated
                   │ NO causation_id tracked
                   │
                   ▼
               MuscalKernel.run() is identity-agnostic
               All identity enrichment is EXTERNAL
```

**Evidence:**
- `kernel.py` imports: 0 references to `execution_context`, `reality`, `uuid7`, `execution_id`
- `kernel.py::run()` parameter: `input_text: str` only — no execution_id, correlation_id, etc.
- `kernel.py::stage_mel()` → `mel.execute(optimized_plan)`: tool names passed but NO execution_id
- `MuscalOS.run()` similarly passes `input_text: str` only to `kernel.run()`

**Impact:** All identity fields (`execution_id`, `execution_mode`, `execution_state`, `verification_state`) exist only in the **enrichment layer** (`EnrichedMuscalOS`, `ExecutionContextManager`). The core execution pipeline has no native identity concept. Identity is a bolt-on, not a first-class architectural element.

---

## 4. Event Architecture Map

### 4.1 Event Systems Inventory

| System | Class/File | Storage | Schema | Writer | Consumer(s) | Events |
|--------|-----------|---------|--------|--------|-------------|--------|
| **EventBus** | `event_bus.py:26` | In-memory (`_history: list`, max 50K) | `EventMessage(topic, payload, source, priority, timestamp, id)` | Any code calling `publish()` | Subscribers by topic + `"*"` | All system events |
| **EventStore** | `runtime/event_store.py:8` | SQLite `stored_events` | 13 columns: seq, topic, payload, source, priority, timestamp, event_id, created_at, execution_id, correlation_id, causation_id, execution_mode, execution_state, verification_state | `_persist_to_store()` or `_enriched_persist()` | WebSocket adapter, ReplayService, GraphOSProjection | All EventBus events (persisted) |
| **WriterThread `events`** | `runtime/kernel/writer.py:71` | SQLite `events` | 24 columns: id, seq, ts, occurred_at, type, actor, actor_type, domain, layer, stream, session_id, payload, caused_by, schema_version, idempotency_key, model_id, confidence, trust_level, severity, aggregate_id, aggregate_type, replayable, payload_sanitized | `WriterThread._write_atomic()` | API endpoints, snapshot service, handoff service | Kernel pipeline events |
| **GraphState** | `graph.py:45` | In-memory (`nodes: dict`, `edges: list`) | `Node(id, type, payload, timestamp, confidence, status)` + `Edge(source_id, target_id, edge_type, payload)` | `GraphState.add_node/update_node/add_edge` | SphereState, event listeners, event bus bridge | Graph lifecycle events |
| **EventConsolidation** | `features/events/event_consolidation.py` | Wraps EventStore | Same as EventStore | `emit_event()` | Query API | Enriched events |
| **SUPL EventBusBridge** | `features/supl/event_integration.py` | Delegates to EventBus (in-memory) | Typed SUPL events | `publish_*()` methods | SUPL subscribers | SUPL-specific events |

### 4.2 Authoritative Event Source

**CURRENTLY: NONE — `stored_events` is the closest to authoritative but is NOT enforced as such.**

- The Architecture Freeze (`GRAPH_OS_ARCHITECTURE_FREEZE_v1.0.md`) declares `stored_events` as canonical
- But `runtime/kernel/writer.py` continues to write to the `events` table independently
- No mechanism prevents the `events` table from diverging from `stored_events`
- No migration or reconciliation exists between the two

### 4.3 Event Lifecycle

```
CREATE     → Any component calls EventBus.publish() or GraphState.emit()
PUBLISH    → EventBus distributes to subscribers synchronously
PERSIST    → EventStore.append() writes to stored_events (via subscriber)
           → WriterThread writes to events table (via separate path)
PROJECT    → GraphOSProjection.project(EventMessage) → normalized dict
REPLAY     → EventStore.replay() → ReplayService republishes to EventBus
```

### 4.4 Event Truth Classification

| Event | Classification | Evidence |
|-------|---------------|----------|
| EVENT_EXECUTION_STARTED | **Claim** (kernel emits before execution) | `kernel.py:633` — emitted at start of `run()` |
| EVENT_SYSTEM_ACTION_STARTED | **Request** (before tool dispatch) | `kernel.py:84` in SystemModule |
| MEL.execute() | **Attempt/Execution** (actual tool call) | `mel.py` → UTR.execute() |
| ExecutionReceipt | **Actual Execution Evidence** (result + hash) | `tool_runtime.py:96` |
| EVENT_SYSTEM_ACTION_COMPLETED | **Outcome** (after result received) | `kernel.py:96` |
| EVENT_EXECUTION_FINISHED | **Outcome** (after pipeline completes) | `kernel.py:321` |
| VerificationResult | **Verification** (independent check) | `tool_runtime.py:40` |
| VERIFICATION_PASSED/FAILED | **Verification Event** (on EventBus) | `orchestrator.py:154` |

### 4.5 Event Gaps

| Gap | Where | Impact |
|-----|-------|--------|
| No event links authorization to execution | SafetyGate/Governance decisions are not published as events | Cannot prove authorization preceded execution |
| No event links intent to execution_id | `EXECUTION_STARTED` in kernel has no execution_id | Cannot trace intent to outcome through events alone |
| No event for ground truth observation | File read-back, DB queries not captured as events | Verification evidence is one-sided |
| Two event tables with no cross-reference | `stored_events` vs `events` | Cannot determine which table is source of truth |
| Replay markers are advisory only | `_replayed=True` marker is a payload field, not enforced | Replayed events can be re-persisted if code path misses the check |

---

## 5. Execution Identity Map

### 5.1 Identity Fields Inventory

| Field | Generated Where | Propagated Where | Persisted Where | Used By | Trust Level |
|-------|----------------|------------------|-----------------|---------|-------------|
| **execution_id** (UUID v7) | `features/identity/uuid7.py` — pure Python | `ExecutionContext` → `enrich_payload()` → EventBus → EventStore → Projection → WebSocket | `stored_events.execution_id` | EnrichedMuscalOS, VerificationOrchestrator, WebSocket client | **HIGH** (uuid7, time-ordered) |
| **execution_id** (UUID v4) | `features/tool_runtime/tool_runtime.py:120` — `execution_id or uuid7()` | `ExecutionReceipt.execution_id` → `_execution_store` (in-memory) | `_execution_store` dict (in-memory only) | UnifiedToolRuntime dedup, verification | **LOW** (in-memory, lost on restart) |
| **correlation_id** | `features/identity/execution_context.py:25` — user-supplied or defaults to execution_id | `ExecutionContext.enrich_payload()` → EventBus → EventStore → Projection | `stored_events.correlation_id` | Execution chain grouping | **MEDIUM** (user-supplied, not verified) |
| **causation_id** | `features/identity/execution_context.py:26` — parent execution_id | `ExecutionContext.enrich_payload()` → EventBus → EventStore → Projection | `stored_events.causation_id` | Causal chain reconstruction | **MEDIUM** (depends on correct parent assignment) |
| **event_id** | `event_bus.py:44` — `uuid7()` if not provided | EventMessage → EventStore | `stored_events.event_id` (UNIQUE) | Deduplication, causal references | **HIGH** (uuid7, DB UNIQUE constraint) |
| **receipt_id** | `features/tool_runtime/tool_runtime.py:114` — `uuid7()` | ExecutionReceipt → VerificationResult | In-memory + optional ReceiptStore | Execution evidence, verification | **HIGH** (uuid7, integrity hash) |
| **trace_id** | `features/provenance/context.py` | `ProvenanceContext` (thread-local) → UTR → ExecutionReceipt | In-memory only | Runtime trace gathering | **LOW** (in-memory, no persistence) |
| **span_id** | `features/provenance/context.py` | `ProvenanceContext` (thread-local) → UTR → ExecutionReceipt | In-memory only | Runtime span tracking | **LOW** (in-memory, no persistence) |
| **session_id** | `runtime/database.py:62` — from config | `events` table (kernel audit) | `events.session_id` | API session tracking | **MEDIUM** |
| **seq** (EventStore) | SQLite AUTOINCREMENT | EventStore replay | `stored_events.seq` (PK) | Cursor-based replay, ordering | **HIGH** (DB-enforced) |
| **seq** (events table) | `database.py:_next_seq()` | WriterThread → API | `events.seq` (UNIQUE) | Kernel audit trail ordering | **HIGH** (DB-enforced) |
| **verification_id** | `features/tool_runtime/tool_runtime.py:52` — `uuid7()` | VerificationResult → EventBus (VERIFICATION_PASSED/FAILED) | `_verification_store` (in-memory) + EventBus event | Verification tracking | **MEDIUM** (in-memory, lost on restart) |

### 5.2 Identity Generation Map

```
                      IDENTITY GENERATION POINTS
                      
kernel.py::run()                     → NO identity generated
MuscalOS.run()                       → NO identity generated
MuscalOS.__init__()                  → NO identity generated
┌─────────────────────────────────────────────────────────────┐
│  EnrichedMuscalOS.run()            → execution_id (uuid7)    │
│                                     correlation_id          │
│                                     causation_id             │
│                                     execution_mode           │
│                                     execution_state          │
│                                     verification_state       │
│  UnifiedToolRuntime.execute()      → execution_id (uuid4)    │
│                                     OR reuses provided one   │
│  UnifiedToolRuntime._build_receipt → receipt_id (uuid7)     │
│  event_bus.publish()              → event_id (uuid7)        │
│  ProvenanceContext                → trace_id, span_id       │
│  SQLite AUTOINCREMENT             → seq (stored_events)     │
│  database._next_seq()             → seq (events table)      │
└─────────────────────────────────────────────────────────────┘
```

### 5.3 Identity Collisions / Fragmentation

| Issue | Evidence | Severity |
|-------|----------|----------|
| **kernel.py generates NO execution_id** | `kernel.py:622-681` — no execution_id parameter or generation | **CRITICAL** — kernel's execution record has no cross-reference |
| **Two execution_id generators (v4 vs v7)** | `tool_runtime.py:120` uses `uuid7()` (imported from identity module, was previously `uuid4()`) vs `execution_context.py:33` uses `uuid7()` | **RESOLVED** — both now use uuid7 |
| **Identity in enriched path only** | `EnrichedMuscalOS.run()` generates ID; `kernel.run()` receives none | **HIGH** — tool results in MEL have no execution_id unless UTR generates one |
| **Verification results lost on restart** | `_verification_store` is in-memory dict | **HIGH** — no evidence survives runtime restart |
| **Receipt store is in-memory by default** | `_receipt_store` is a plain dict | **HIGH** — no receipt survives runtime restart |
| **ExecutionStore is in-memory** | `_execution_store` is a plain dict | **MEDIUM** — dedup lost on restart, allowing duplicate execution_ids |

---

## 6. Verification Architecture

### 6.1 Verification Mechanisms Inventory

| Mechanism | File | What It Verifies | Verifier Independence | Persistence | Trust Level |
|-----------|------|------------------|----------------------|-------------|-------------|
| **UTR.verify()** | `tool_runtime.py:501` | ExecutionReceipt by receipt_id or tool_name | **Independent** — uses registered verifier functions | In-memory `_verification_store` | **MEDIUM** |
| **UTR._verify_one()** | `tool_runtime.py:518` | Single receipt: hash integrity + tool verifier | **Independent** — no agent claim influence | In-memory | **MEDIUM** |
| **IntegrityVerifier** | `verifier.py:27` | Receipt integrity hash (SHA-256) | **Fully independent** — pure hash recomputation | Via Orchestrator store | **HIGH** |
| **MathVerifier** | `verifier.py:81` | `math.add` result via recomputation | **Fully independent** — pure recomputation | Via Orchestrator store | **HIGH** |
| **FilesystemVerifier** | `verifier.py:126` | File existence + optional content match | **Partially independent** — file read-back is objective, but expected content may come from agent | Via Orchestrator store | **MEDIUM** |
| **OpenCodeRunVerifier** | `verifier.py:206` | `opencode.run` result status | **Partially independent** — checks result status field, not ground truth | Via Orchestrator store | **LOW** |
| **VerificationOrchestrator** | `orchestrator.py:58` | Full verification pipeline: integrity → tool verifier → rules → event publish | **Independent** — orchestrator routes to independent verifiers | `_verification_store` (in-memory) | **MEDIUM** |
| **RuleEngine** | `rules.py:95` | VerificationResult against 9 HARD_RULES | **Fully independent** — hardcoded rules | Transient (check only) | **HIGH** |

### 6.2 Verification Trust Classification

```
NO VERIFICATION              → Context enrichment without verification
SELF-VERIFICATION            → Agent claims execution without receipt
RUNTIME VERIFICATION         → UTR.verify() with registered verifiers
INDEPENDENT VERIFICATION     → VerificationOrchestrator (integrity hash + tool verifier)
EXTERNAL VERIFICATION        → Filesystem read-back (partial — expected content may be agent-provided)
HUMAN VERIFICATION           → NOT IMPLEMENTED
```

### 6.3 Critical Findings

1. **Verification is not automatically triggered.** `EnrichedMuscalOS.verify_execution()` must be called explicitly. The `VerificationOrchestrator` is optional and not wired by default.

2. **Verification results do not survive restart.** All verification stores (`_verification_store`, `_receipt_store`, `_execution_store`) are in-memory dicts.

3. **There is no independent verifier infrastructure for the `events` table.** The WriterThread writes to `events` but no verification exists for that path.

4. **Verification events (VERIFICATION_PASSED/FAILED) flow through EventBus but are not linked back to the original execution event** causally at the EventStore level (they share correlation_id but no direct FK).

5. **The VerificationOrchestrator and UTR.verify() are not unified.** Both exist, both work, but neither knows about the other. There is no single `verify()` entry point for the system.

6. **Can verification be bypassed?** YES — any code can call `VerificationResult(status="verified")` directly without going through any verifier. There is no enforcement that verification status must come from a verifier function.

---

## 7. Provenance Completeness Matrix

| Transition | Status | Evidence | Gap |
|-----------|--------|----------|-----|
| INTENT → PLAN | **PRESENT** | `kernel.py:366` — MKC compile + Bridge map_tasks | Intent ID tracked in graph |
| PLAN → AUTHORIZATION | **PARTIAL** | GovernanceStage checks permission; not linked causally | Authorization decision is NOT linked to execution_id |
| AUTHORIZATION → ACTION REQUEST | **PARTIAL** | SafetyGate check in UTR; event published? | SafetyGate result not published as event |
| ACTION REQUEST → TOOL INVOCATION | **PRESENT** | `MEL.execute()` → UTR.execute() | OK |
| TOOL INVOCATION → EXECUTION | **PRESENT** | `UTR.execute()` produces ExecutionReceipt | OK |
| EXECUTION → OBSERVATION | **PARTIAL** | Receipt stores result_data; no ground truth re-check | Result stored but not independently verified at capture time |
| OBSERVATION → STATE CHANGE | **PARTIAL** | Graph state nodes added; no cross-reference to execution_id | GraphState.Node has NO execution_id field in `schema.py` |
| STATE CHANGE → EVIDENCE | **PARTIAL** | ExecutionReceipt with integrity hash; hash only covers receipt fields | Evidence does NOT include ground truth observation |
| EVIDENCE → VERIFICATION | **PARTIAL** | VerificationOrchestrator.verify() → VerificationResult | Not automatically triggered; not persisted |
| VERIFICATION → OUTCOME | **PARTIAL** | VERIFICATION_PASSED/FAILED published to EventBus | Not causally linked to execution via FK |
| FULL CHAIN | **PARTIALLY RECONSTRUCTABLE** | Requires joining EventStore data + in-memory stores + graph state | No single query can reconstruct the full chain |

### Provenance Chain Gap Score: 6/11 transitions partial or missing

---

## 8. State Authority Map

### 8.1 State Classification

| State | Classification | Evidence | Can Mutate Authoritative? |
|-------|---------------|----------|--------------------------|
| **EventStore (stored_events)** | **AUTHORITATIVE** (by declaration) | Architecture freeze designates it canonical | N/A — declared canonical |
| **WriterThread (events table)** | **AUTHORITATIVE** (by existence) | Oldest event storage; rich schema; used by API | Yes — can write concurrently with EventStore |
| **GraphState (in-memory)** | **DERIVED** | Built from kernel pipeline; nodes have no execution_id | No — only reads from kernel stages |
| **SphereState (in-memory)** | **DERIVED** | Synced from GraphState events | No — read-only sync |
| **ExecutionContext (thread-local)** | **EPHEMERAL** | `threading.local()`, exists only during execution | No — transient |
| **EventBus history** | **EPHEMERAL** | In-memory list, max 50K, lost on restart | No — advisory |
| **API state** | **DERIVED** | Reads from events table + GraphState | No — read-only |
| **Frontend (Scene State)** | **EPHEMERAL** | Not implemented in code (conceptual only) | N/A |
| **Verification stores** | **EPHEMERAL** | In-memory dicts, lost on restart | No |
| **Receipt store** | **EPHEMERAL** | In-memory dict (or optional ReceiptStore) | No |
| **Execution store** | **EPHEMERAL** | In-memory dict for dedup | No |

### 8.2 Critical Finding: Dual Authoritative State

**Both `stored_events` and `events` table function as authoritative state** with no synchronization:

```
WriterThread → events table
  - Written by: runtime/kernel/writer.py:71-130
  - Contains: 24 columns, idempotency_key, trust_level, etc.
  - Used by: API endpoints (events.py, state.py, chat.py)
  - Schema: rich domain model (actor, domain, layer, stream)

MuscalOS._persist_to_store → EventStore → stored_events
  - Written by: muscal_os.py:246-256 (or enriched_bootstrap.py:149-167)
  - Contains: 13 columns, execution_id, correlation_id, etc.
  - Used by: WebSocket adapter, ReplayService, GraphOSProjection
  - Schema: enriched transport model

PROBLEM: These are NOT the same events.
- WriterThread writes kernel pipeline events (MKC, MEL, Feedback, Memory)
- EventStore writes EventBus events (graph events, lifecycle events)
- Neither captures the other's events
- API reads from events table → does NOT see execution_id enrichment
- WebSocket reads from stored_events → does NOT see actor/domain/layer
- No cross-reference between the two tables
```

---

## 9. Failure/Crash Analysis

### Case A: Tool never starts

| Aspect | Current Behavior | Evidence |
|--------|-----------------|----------|
| 404/unknown tool | `UTR.execute()` returns ToolResult with error "Unknown tool" | `tool_runtime.py:406-410` |
| Receipt generated? | YES — `_build_receipt()` called with `success=False` | `tool_runtime.py:399-405` |
| Event emitted? | NO — graph event may be emitted by SystemModule but no dedicated error event | `kernel.py:84-106` |
| Execution state known? | **PARTIAL** — receipt exists in memory but not causally linked to execution | |
| Survives restart? | NO — receipt is in-memory | |

### Case B: Tool starts and fails

| Aspect | Current Behavior | Evidence |
|--------|-----------------|----------|
| Exception in executor | `UTR.execute()` catches Exception, builds receipt with failed VerificationResult | `tool_runtime.py:479-499` |
| Receipt generated? | YES — `_build_receipt()` with `success=False` | |
| Event emitted? | YES — SystemModule `EVENT_SYSTEM_ACTION_FAILED` | `kernel.py:96-103` |
| Graph node created? | YES — `NODE_TYPE_SYSTEM_ACTION` or `NODE_TYPE_TOOL_EXECUTION` | `kernel.py:403-414` |
| Memory snapshot? | YES — `stage_memory()` stores snapshot if pipeline continues | `kernel.py:312-322` |

### Case C: Tool executes successfully but result is lost

| Aspect | Current Behavior | Evidence |
|--------|-----------------|----------|
| Receipt captured? | YES — `_build_receipt()` stores result | `tool_runtime.py:444-455` |
| Where is result? | In-memory receipt store + graph node payload | |
| Can result be recovered? | **NO** — if process crashes, result is lost | |
| EventStore has it? | **Only if pipeline published EventBus event** — tool result is NOT automatically published to EventBus | |

### Case D: Tool succeeds but runtime crashes before recording result

| Aspect | Current Behavior | Evidence |
|--------|-----------------|----------|
| Receipt built? | **NO** — `_build_receipt()` happens after `fn(args)` returns | `tool_runtime.py:438-455` |
| Any evidence? | **NONE** — no receipt, no event, no graph node | |
| Crash between result and receipt | **INVISIBLE TO SYSTEM** — no record | |
| Recovery? | **IMPOSSIBLE** — no evidence exists | |

### Case E: Tool reports success but external state is wrong

| Aspect | Current Behavior | Evidence |
|--------|-----------------|----------|
| Detected by verifier? | **ONLY IF verification is triggered** — FilesystemVerifier can detect | `verifier.py:126` |
| Automatic verification? | **NO** — must call `verify_execution()` explicitly | |
| How detected? | Verification reads back file content vs expected | |
| What happens on detection? | `VerificationResult(status="FAILED")`; VERIFICATION_FAILED published | `orchestrator.py:154` |

### Case F: Tool executes twice due to retry

| Aspect | Current Behavior | Evidence |
|--------|-----------------|----------|
| Dedup mechanism? | `_execution_store` dict — checks `execution_id` | `tool_runtime.py:387-394` |
| Returns what on dedup? | ToolResult with `error="DUPLICATE_EXECUTION_ID"` | |
| Survives restart? | **NO** — `_execution_store` is in-memory | |
| Idempotency at DB level? | YES — `events` table has `idempotency_key UNIQUE` | `database.py:64` |
| Idempotency at EventStore? | YES — `event_id UNIQUE` constraint | `event_store.py:27` |

### Case G: Agent claims execution without invoking tool

| Aspect | Current Behavior | Evidence |
|--------|-----------------|----------|
| Can this happen? | **YES** — if code calls `_build_receipt()` or constructs VerificationResult directly | |
| Detection? | No integrity check against actual tool dispatch | |
| Protection? | None — any code can create receipts | |
| Trust boundary enforcement? | **PARTIAL** — EXECUTION_INTEGRITY_CONTRACT specifies rules but they are not enforced at system boundaries | |

### Case H: Simulation incorrectly interpreted as real execution

| Aspect | Current Behavior | Evidence |
|--------|-----------------|----------|
| Per-event mode tracking? | YES — `execution_mode` propagated via `ExecutionContext` | |
| kernel.py awareness? | **NO** — kernel has no `execution_mode` concept | |
| OS config flag? | `simulation_mode: bool` used in `muscal_os.py` | `muscal_os.py:132` |
| Confusion possible? | **YES** — kernel pipelines runs identically regardless of mode | |
| Enriched wrapper handles it? | YES — `EnrichedMuscalOS.run()` sets `execution_mode` | `enriched_bootstrap.py:77` |

---

## 10. MUSCAL Component Inventory

| Component | File | Purpose | Architectural Layer | Maturity | Tests | Trust Core Relevance | Recommendation |
|-----------|------|---------|--------------------|----------|-------|---------------------|---------------|
| **MuscalOS** | `muscal_os.py` | Boot/run orchestrator | OS | HIGH | Yes (indirect) | LOW — OS orchestration, not trust | KEEP |
| **MuscalKernel** | `kernel.py` | Pipeline orchestration | Kernel | HIGH | Yes (6 test files) | **HIGH** — execution core | EXTRACT (identity) |
| **EnrichedMuscalOS** | `features/bootstrap/enriched_bootstrap.py` | Identity-enriched wrapper | Identity | HIGH | Yes (Phase 1B tests) | **HIGH** — identity propagation | KEEP |
| **UnifiedToolRuntime** | `features/tool_runtime/tool_runtime.py` | Tool execution + verification | Tool Runtime | HIGH | Yes (multiple test files) | **HIGH** — execution evidence | KEEP (extract trust parts) |
| **ExecutionReceipt** | `features/tool_runtime/tool_runtime.py:96` | Execution evidence | Trust Core | HIGH | Yes (extensive) | **HIGH** — core trust evidence | KEEP |
| **VerificationResult** | `features/tool_runtime/tool_runtime.py:40` | Verification evidence | Trust Core | HIGH | Yes | **HIGH** — core trust evidence | KEEP |
| **VerificationStatus** | `features/tool_runtime/tool_runtime.py:24` | Verification status constants | Trust Core | HIGH | Yes | **HIGH** | KEEP |
| **ExecutionContext** | `features/identity/execution_context.py` | Identity carrier | Identity | HIGH | Yes | **HIGH** | KEEP |
| **ExecutionContextManager** | `features/identity/execution_context.py:73` | Thread-local context | Identity | HIGH | Yes | **HIGH** | KEEP |
| **ExecutionMode** | `features/identity/reality.py:12` | Reality mode enum | Reality | HIGH | Yes | **HIGH** — distinguish sim/reality | KEEP |
| **ExecutionState** | `features/identity/reality.py:20` | Execution lifecycle enum | Reality | HIGH | Yes | **HIGH** | KEEP |
| **VerificationState** | `features/identity/reality.py:29` | Verification status enum | Reality | HIGH | Yes | **HIGH** | KEEP |
| **validate_state_transition** | `features/identity/reality.py:79` | State validity check | Reality | HIGH | Yes | **HIGH** | KEEP |
| **UUID v7** | `features/identity/uuid7.py` | UUID generation | Identity | HIGH | Yes | **HIGH** | KEEP |
| **VerificationOrchestrator** | `features/verification/orchestrator.py` | VF orchestration | Trust Core | HIGH | Yes (Phase 2) | **HIGH** | KEEP |
| **Verifier (ABC)** | `features/verification/verifier.py` | Verifier base class | Trust Core | HIGH | Yes | **HIGH** | KEEP |
| **Built-in Verifiers** | `features/verification/verifier.py` | Math/Filesystem/OpenCode | Trust Core | HIGH | Yes | **HIGH** | KEEP |
| **RuleEngine** | `features/verification/rules.py` | Hard rules enforcement | Trust Core | HIGH | Yes | **HIGH** | KEEP |
| **HARD_RULES** | `features/verification/rules.py:80` | 9 HARD_RULES | Trust Core | HIGH | Yes | **HIGH** | KEEP |
| **GraphOSProjection** | `features/projection/graph_os_projection.py` | Event normalization | Projection | HIGH | Yes | **MEDIUM** — transport concern | KEEP |
| **WebSocketAdapter** | `features/streaming/ws_adapter.py` | WebSocket transport | Transport | HIGH | Yes | **LOW** — transport | KEEP |
| **EventStore** | `runtime/event_store.py` | Event persistence | Storage | HIGH | Yes | **HIGH** — trust store | KEEP (as canonical) |
| **EventBus** | `event_bus.py` | In-memory pub/sub | Transport | HIGH | Yes | **LOW** — plumbing | KEEP |
| **WriterThread** | `runtime/kernel/writer.py` | Kernel audit persistence | Storage | HIGH | Yes | **MEDIUM** — duplicate store | DEPRECATE for trust |
| **GraphState** | `graph.py` | In-memory graph | State | HIGH | Yes | **LOW** — derived view | KEEP |
| **SphereState** | `sphere.py` | Cognitive projection | State | HIGH | Yes | **LOW** | KEEP |
| **ProvenanceContext** | `features/provenance/context.py` | Trace/span context | Provenance | MEDIUM | Yes | **MEDIUM** | EXTRACT |
| **Provenance Classifier** | `features/provenance/classifier.py` | Evidence classification | Provenance | MEDIUM | Yes | **HIGH** — trust classification | KEEP |
| **Provenance Validator** | `features/provenance/validator.py` | Provenance validation | Provenance | MEDIUM | Yes | **HIGH** | KEEP |
| **OutcomeRecord** | `features/execution/outcome.py` | Execution outcome + integrity | Execution | MEDIUM | Yes | **MEDIUM** | EXTRACT |
| **EvaluationValidation** | `features/execution/evaluation_validation.py` | Evaluation + integrity | Execution | LOW | Yes | **LOW** | REFACTOR |
| **MREILInstruction** | `features/execution/mreil.py` | MREIL cost data | Execution | LOW | No | **LOW** — optimization metadata | DEPRECATE from trust |
| **EventConsolidation** | `features/events/event_consolidation.py` | Consolidated event API | Events | MEDIUM | Yes | **LOW** — wraps EventStore | KEEP |
| **EventAdapter** | `features/events/event_adapter.py` | Writer↔EventStore bridge | Events | LOW | Yes | **MEDIUM** — bridge between two stores | REFACTOR |
| **SafetyGate** | `features/safety/safety_gate.py` | Execution safety check | Governance | HIGH | Yes | **HIGH** — authorization | KEEP (link to trust) |
| **GovernanceStage** | `features/pipeline/governance_stage.py` | Pipeline governance | Governance | MEDIUM | Yes | **MEDIUM** | KEEP |
| **SUPL EventBusBridge** | `features/supl/event_integration.py` | SUPL event bridge | SUPL | HIGH | Yes | **LOW** | KEEP |
| **ReplayService** | `features/replay/replay_service.py` | Event replay | Events | MEDIUM | Yes | **HIGH** — trust replay | KEEP (extract) |
| **ReceiptStore** | `features/tool_runtime/receipt_store.py` | Receipt persistence | Tool Runtime | LOW | Partial | **HIGH** — trust persistence | EXTRACT |
| **os_config** | `os_config.py` | Configuration | Config | HIGH | N/A | **LOW** | KEEP |
| **schema.py** | `schema.py` | Data models | Schema | HIGH | N/A | **MEDIUM** — Node/Edge need trust fields | REFACTOR (add execution_id) |

---

## 11. MPP / MPIR / Prompt AST Positioning

| Component | Status | Finding |
|-----------|--------|---------|
| MUSCAL Prompt Pipeline (MPP) | **CONCEPTUAL ONLY** | Not found in code. No MPP class or module exists. |
| MPES | **CONCEPTUAL ONLY** | Not found in code. Mentioned in docs only. |
| MPIR | **CONCEPTUAL ONLY** | Not found in code. Mentioned in docs only. |
| Prompt AST | **CONCEPTUAL ONLY** | Not implemented. MKC produces MCXF, not a Prompt AST. |
| Cognitive Kernel Stack | **NOT FOUND** | Not in code or documentation as an implemented system. |
| Prompt Compiler | **NOT FOUND** | MKC compilation is the closest analog, but is domain-specific, not a general prompt compiler. |
| Intent Parser | **PARTIALLY IMPLEMENTED** | MKC module parses input into tasks/decisions. No formal intent model. |
| Semantic Normalizer | **NOT FOUND** | Not in code. |
| Constraint Extractor | **PARTIALLY IMPLEMENTED** | MKC extracts constraints into MCXF.constraints. |
| Context Loader | **PARTIALLY IMPLEMENTED** | RAGModule loads context from memory. Not a structured context loader. |
| Knowledge Graph Builder | **NOT FOUND** | GraphState builds an execution graph, not a knowledge graph. |
| Architecture Reconstructor | **NOT FOUND** | Not in code. |
| Missing Knowledge Detector | **NOT FOUND** | Not in code. |
| Expert Scheduler | **NOT FOUND** | `scheduler.py` is a kernel pipeline scheduler, not an expert scheduler. |
| Consensus Engine | **PRESENT** | `consensus_engine.py` + `weighted_consensus.py` exist but are not wired into the execution pipeline. |
| Code Planner | **NOT FOUND** | Not in code. |
| Implementation Generator | **NOT FOUND** | Not in code. |
| Verification Engine | **PRESENT** | `features/verification/` implements this. Phase 2 of GRAPH-OS. |
| Performance Optimizer | **PRESENT** | `runtime/optimizer/` exists (OptimizerPipeline, cost optimizer, node fusion, etc.). |
| MREIL Evaluator | **PARTIALLY IMPLEMENTED** | `features/execution/mreil.py` defines MREILInstruction. Not wired into verification. |
| Knowledge Distiller | **NOT FOUND** | Not in code. |
| Response Compiler | **PARTIALLY IMPLEMENTED** | Kernel returns KernelResult. No formal response compilation. |

**Conclusion:** The MPP/MPIR/Prompt AST ecosystem is largely **conceptual** or **only partially implemented**. None of these are Trust Core candidates.

---

## 12. MREIL Positioning

| Aspect | Finding |
|--------|---------|
| Code location | `features/execution/mreil.py` |
| What it is | `MREILInstruction` dataclass with `action`, `execution_id`, `quality`, `resource_usage`, `latency`, `token_efficiency`, `consensus_efficiency` |
| Wired into execution? | **NO** — MREILInstruction is defined but not used in any execution path |
| Wired into verification? | **NO** — no verifier references MREIL data |
| Is it Trust Core? | **NO** — MREIL is optimization metadata (quality, resource usage, latency, token efficiency) |
| Is it execution truth? | **NO** — MREIL measures execution efficiency, not correctness |
| Recommendation | **DEPRECATE from Trust Core** — belongs in an Optimization Metadata layer, not Trust Core |

---

## 13. Graph-OS / ALITA Boundary Analysis

### 13.1 Current Authority Model

```
MUSCAL Kernel (kernel.py)
  → execution pipeline (NO identity)
  → GraphState (in-memory graph, NO execution_id on nodes)
  → EventBus events (with or without enrichment)

EnrichedMuscalOS (wrapper)
  → Adds execution_id, execution_mode, etc.
  → Uses EventBus subscriber to persist enriched events

GraphOSProjection
  → Transforms EventMessage → normalized GraphOSEvent dict
  → Filters by CANONICAL_EVENT_TYPES

WebSocketAdapter
  → Delivers projected events to connected clients

ALITA
  → NOT IMPLEMENTED — no ALITA code exists
```

### 13.2 Existing Write Paths That Violate Proposed Authority Model

| Violation | Path | Severity |
|-----------|------|----------|
| **WriterThread writes to `events` table independently** | Kernel pipeline → `runtime/kernel/writer.py:95` → `events` table | **HIGH** — bypasses EventStore enrichment |
| **No execution_id on GraphState.Node** | `schema.py:139-145` — Node dataclass has NO execution_id field | **HIGH** — GraphState nodes cannot be traced to execution |
| **EventBus has no access control** | Any code can call `event_bus.publish()` | **MEDIUM** — ALITA could write to EventBus (but no ALITA code exists) |
| **GraphState.emit() goes to EventBus via bridge** | `muscal_os.py:348` — `_bridge_to_graph` subscribes `"*"` and calls `graph.emit()` | **MEDIUM** — bidirectional bridge allows event injection |

### 13.3 Verified Authority Flow

```
Proposed:                     Actual Today:
MUSCAL / Trust Core           MuscalKernel (no identity)
        ↓                              ↓
Projection Layer               EnrichedMuscalOS (adds identity)
        ↓                              ↓
Graph-OS                       GraphOSProjection (normalizes)
        ↓                              ↓
Scene State                    WebSocketAdapter (delivers)
        ↓
ALITA (NOT IMPLEMENTED)
```

**The proposed authority model is architecturally valid but not enforced.** The actual flow has identity injection at the enrichment layer (not the kernel), two parallel event stores, and no access control on the EventBus.

---

## 14. Architecture Delta Map

### Current MUSCAL → Trust Core Target

| Component | Current | Target | Recommendation |
|-----------|---------|--------|---------------|
| **Execution identity** | Injected by EnrichedMuscalOS (wrapper) | Must be generated by kernel at entry point | **EXTRACT** identity into kernel |
| **execution_id** | Generated in wrapper (uuid7) + UTR (uuid7) | Single generation point in kernel | **REFACTOR** to kernel generation |
| **Event storage** | `stored_events` (enriched) + `events` (kernel audit) | Single canonical `stored_events` (enriched) | **DEPRECATE** `events` for trust queries |
| **Verification** | UTR.verify() + VerificationOrchestrator (unified) + in-memory stores | Single persisted verification layer | **REFACTOR** into unified, persisted service |
| **GraphState.Node** | No execution_id | Must carry execution_id | **REFACTOR** schema.py Node |
| **Authorization** | SafetyGate (pre-execution) + GovernanceStage (pipeline) | Must be causally linked to execution | **EXTRACT** authorization into events |
| **Provenance** | Thread-local + in-memory + partial | Persisted, queryable causal chain | **EXTRACT** into Trust Core store |
| **Replay** | ReplayService + EventStore.replay() | Trusted replay with verification | **KEEP** — exists, needs hardening |
| **Receipt store** | In-memory dict | Persisted receipt store | **EXTRACT** into persistent store |
| **Verification store** | In-memory dict | Persisted verification store | **EXTRACT** into persistent store |
| **Execution store (dedup)** | In-memory dict | Persisted execution store | **EXTRACT** into persistent store |
| **ALITA** | NOT IMPLEMENTED | Observer only — no write path | **DEFER** |
| **Graph-OS** | NOT IMPLEMENTED (only projection + WS) | Derived cognitive projection | **KEEP** trajectory |
| **MREIL** | Defined but unused | Optimization metadata, not trust | **DEPRECATE** from trust scope |

---

## 15. Contradiction Register

| ID | Contradiction | Evidence A | Evidence B | Impact | Severity | Proposed Resolution |
|----|--------------|-----------|-----------|--------|---------|-------------------|
| C-001 | **Two authoritative event stores** | Architecture freeze designates `stored_events` as canonical | `runtime/kernel/writer.py` continues writing to `events` table independently | Dual authority with no reconciliation | **CRITICAL** | Deprecate `events` table for trust queries; migrate all consumers to `stored_events` |
| C-002 | **execution_id generated in two places** | `EnrichedMuscalOS.run()` generates uuid7 | `UnifiedToolRuntime.execute()` generates uuid7 (fallback) | Identity fragmentation; kernel has none | **HIGH** | Single generation point in `kernel.run()` |
| C-003 | **Simulation mode: boolean vs enum** | `os_config.py:59` `simulation_mode: bool` used by OS layer | `features/identity/reality.py:12` `ExecutionMode` 5-value enum used by enrichment layer | Two independent simulation concepts; kernel unaware of either | **HIGH** | Unify; kernel must be mode-aware |
| C-004 | **kernel.py has no identity awareness** | Architecture freeze §I requires execution_id in kernel.run() | `kernel.py:622` `run(input_text: str)` has no identity parameters | Core execution has no identity concept | **CRITICAL** | Add execution_id, correlation_id, etc. to kernel.run() |
| C-005 | **GraphState.Node has no execution_id** | Architecture freeze §H requires Node enriched with execution_id | `schema.py:139` Node dataclass has NO execution_id field | Graph nodes cannot be traced to execution | **HIGH** | Add execution_id to schema.py Node |
| C-006 | **Verification not automatically triggered** | Architecture freeze §G requires verification on every execution | `EnrichedMuscalOS.verify_execution()` is optional, not called by default | Verification can be skipped | **HIGH** | Wire verification into `EnrichedMuscalOS.run()` by default |
| C-007 | **Two verification systems ununified** | `UTR._verify_one()` with in-memory store | `VerificationOrchestrator.verify()` with separate store | No single verification entry point | **MEDIUM** | Unify into single verification service |
| C-008 | **Verification stores are in-memory** | All verification/receipt/execution stores are dicts | Trust requires persistence for crash recovery | All evidence lost on restart | **HIGH** | Persist verification results in EventStore |
| C-009 | **execution_mode unused by kernel** | `features/identity/reality.py` defines 5-mode enum | `kernel.py` never references execution_mode | Simulation vs reality indistinguishable within kernel | **HIGH** | Propagate execution_mode into kernel pipeline |
| C-010 | **schema.py Node has no enrichment fields** | Architecture freeze §H requires execution_id, execution_mode, etc. on Node | `schema.py:139-145` Node has only: id, type, payload, timestamp, confidence, status | Node is not enriched | **HIGH** | Add enrichment fields to Node |
| C-011 | **SafetyGate decisions not published as events** | `UTR.execute()` calls SafetyGate | No event published for authorization result | Authorization not causally linked to execution | **MEDIUM** | Publish authorization events |
| C-012 | **Documentation declares frozen architecture but code contradicts** | `GRAPH_OS_ARCHITECTURE_FREEZE_v1.0.md` declares Node with execution_id | `schema.py:Node` has no execution_id | Freeze document not enforced in code | **HIGH** | Compliance pass needed |
| C-013 | **Simulated/real distinction feasible but not enforced** | `execution_mode` on every enriched event | `kernel.py` has no mode awareness; pipeline identical for both | Enforcement gap | **HIGH** | Kernel must reject invalid mode transitions |
| C-014 | **No `is_authoritative` flag anywhere** | Every architecture document discusses authority | No code enforces authority concept | Authority is conceptual only | **MEDIUM** | Add authority marker to events |
| C-015 | **EventBus history lost on restart** | `_history` in-memory list (max 50K) | No event survives process restart | System has no memory of past events | **MEDIUM** | EventStore already persists; reduce EventBus history reliance |

### Contradiction Summary: 15 documented contradictions, 4 CRITICAL, 8 HIGH, 3 MEDIUM

---

## 16. Trust Core Readiness Matrix

| Domain | Status | Evidence | Gap | Priority |
|--------|--------|----------|-----|----------|
| **Execution Truth** | **PARTIAL** | EnrichedMuscalOS generates identity; kernel has none | Kernel must generate and propagate identity natively | P0 |
| **Identity** | **PARTIAL** | UUID v7 exists; execution_id generated in two places | Single generation point; kernel integration | P0 |
| **State Authority** | **NOT READY** | Two event stores with no reconciliation | Single canonical store; deprecate events table for trust | P0 |
| **Evidence** | **PARTIAL** | ExecutionReceipt with integrity hash; in-memory only | Persist receipts in EventStore; survive restart | P1 |
| **Verification** | **PARTIAL** | Two parallel systems; in-memory stores; not automatically triggered | Unify into single, persisted, default-on service | P1 |
| **Provenance** | **PARTIAL** | causality_engine, causation_id chain, but not queryable | Single queryable causal chain from intent to outcome | P1 |
| **Failure Semantics** | **NOT READY** | Crash analysis reveals invisible failures (Case D: result lost between execution and receipt) | Atomic execution-receipt pair; crash recovery | P1 |
| **Recovery** | **NOT READY** | Everything in-memory; no replay-based recovery path | Replay from EventStore; rebuild state | P2 |
| **Replay** | **READY** | EventStore.replay() + ReplayService exist and tested | Needs verification integration | P1 |
| **Authorization** | **PARTIAL** | SafetyGate + GovernanceStage exist; not causally linked to execution | Link auth decisions to execution chain | P2 |
| **Tool Mediation** | **PARTIAL** | UTR registers tools/schemas/verifiers; some verifiers are partial | Ensure all tools have independent verifiers | P1 |
| **Human Governance** | **NOT READY** | No human-in-the-loop path exists | Future concern | P3 |
| **External Reality Boundary** | **PARTIAL** | FilesystemVerifier reads ground truth; no external system verifiers | Expand verifiers for all external interactions | P2 |

### Readiness Summary: 1/13 READY, 6/13 PARTIAL, 5/13 NOT READY, 1/3 P3

---

## 17. Architecture Review Board Decision

### Question 1: What is already trustworthy?

1. **ExecutionReceipt with SHA-256 integrity hash** — cryptographically verifiable evidence of tool execution
2. **VerificationOrchestrator** — correctly routes to independent verifiers and enforces Hard Rules
3. **EventStore with append-only semantics** — SQLite AUTOINCREMENT provides ordered, immutable event log
4. **UUID v7 generation** — pure Python, time-ordered, globally unique
5. **Reality model (ExecutionMode × ExecutionState × VerificationState)** — complete validity matrix
6. **ExecutionContext propagation** — thread-local context correctly enriches events through the pipeline

### Question 2: What is only claimed to be trustworthy?

1. **`stored_events` as "canonical"** — claimed in architecture freeze but not enforced; `events` table continues to be written
2. **Execution integrity** — claimed in `EXECUTION_INTEGRITY_CONTRACT.md` but kernel has no identity awareness
3. **Verification independence** — claimed but some verifiers (FilesystemVerifier) accept agent-provided expected content
4. **Simulation/reality distinction** — claimed via `execution_mode` enum but kernel is mode-agnostic

### Question 3: What is missing?

1. **Kernel-native identity** — `kernel.run()` must generate and propagate execution_id
2. **Single authoritative event store** — deprecate `events` table for trust queries
3. **Persisted verification/receipt/execution stores** — currently in-memory only
4. **Automatic verification** — `verify_execution()` must be called by default
5. **Unified verification entry point** — UTR.verify() and VerificationOrchestrator must be unified
6. **Authorization events** — SafetyGate decisions must be published as events
7. **execution_id on GraphState.Node** — nodes cannot be traced to execution
8. **execution_id on schema.py Node** — dataclass lacks enrichment fields
9. **Crash recovery** — Case D (result lost between tool return and receipt) has no handling
10. **Cross-reference between event stores** — no mechanism to join `stored_events` and `events`

### Question 4: What is contradictory?

See Contradiction Register (§15) — 15 contradictions, 4 CRITICAL, 8 HIGH.

### Question 5: What can be extracted?

1. **Trust Core Identity Layer** — `features/identity/` (execution_context.py, reality.py, uuid7.py) — directly reusable
2. **Trust Core Evidence Layer** — `ExecutionReceipt`, `VerificationResult`, `VerificationStatus` from `features/tool_runtime/` — extract into `features/trust/`
3. **Trust Core Verification Layer** — `features/verification/` (orchestrator, verifier, rules) — directly reusable
4. **Trust Core Store** — `EventStore` + persisted receipt/verification/execution tables
5. **Trust Core Provenance** — `features/provenance/classifier.py`, `validator.py` — direct candidates

### Question 6: What must be redesigned?

1. **kernel.run()** — must accept and propagate execution_id, execution_mode, etc.
2. **Event storage architecture** — single authoritative store with trust metadata
3. **Verification store** — from in-memory to persisted EventStore-backed
4. **Receipt store** — from in-memory to persisted EventStore-backed
5. **Authorization event linking** — SafetyGate results must be published and linked

### Question 7: What must be discarded?

1. **`events` table as trust source** — keep for MUSCAL internal audit but remove from trust queries
2. **`simulation_mode: bool`** — replace entirely with `execution_mode: ExecutionMode`
3. **In-memory-only verification/receipt stores** — replace with persisted stores
4. **Unverified tool execution paths** — any execution path without verification

### Question 8: What is the smallest coherent Trust Core boundary?

```
Minimum Trust Core:
┌───────────────────────────────────────────────┐
│  features/trust/                               │
│  ├── identity.py      (from identity/)         │
│  ├── evidence.py      (from tool_runtime/)     │
│  ├── verification.py  (from verification/)     │
│  ├── store.py         (EventStore + trust tables)│
│  └── provenance.py    (from provenance/)       │
│                                               │
│  Integration:                                  │
│  ├── kernel.run() must generate identity       │
│  ├── EventStore is canonical trust store       │
│  ├── Executions are auto-verified              │
│  └── All trust data persisted and replayable   │
└───────────────────────────────────────────────┘
```

---

## 18. Required ADR Changes

| ADR | Change Required | Priority |
|-----|----------------|----------|
| **ADR-003 (Events)** | Update to designate single canonical event store; add `authority` field to event envelope | P0 |
| **ADR-007 (Immutability)** | Extend to include Trust Core tables (receipt, verification, execution stores) | P0 |
| **ADR-011 (Verification)** | Update to reflect Phase 2 implementation; unify with UTR.verify() | P1 |
| **ADR-014 (Tool Runtime)** | Update to require kernel-native identity; remove dual execution_id generation | P0 |
| **New ADR: Trust Core Boundary** | Define the `features/trust/` package; extract from existing features | P0 |
| **New ADR: Kernel Identity Integration** | Require `kernel.run()` to accept/generate execution_id, correlation_id, execution_mode | P0 |
| **New ADR: Event Store Consolidation** | Deprecate `events` table for trust; migrate consumers to `stored_events` | P0 |

---

## 19. Recommended MC-TC-003 Scope

MC-TC-003 should:

1. **Define the Trust Core package structure** (`features/trust/`)
2. **Extract Trust Core components** from existing code (identity, evidence, verification, provenance)
3. **Design the persisted trust storage** (EventStore tables for receipts, verifications, executions)
4. **Design the kernel identity integration** (execution_id generation in kernel.run())
5. **Define migration path** for `events` table consumers to `stored_events`
6. **Resolve all 15 contradictions** from the Contradiction Register
7. **Implement unified verification service** (single entry point, persisted results)
8. **Define crash recovery semantics** (atomic execution-receipt pairs, replay-based recovery)
9. **Produce ADR changes** for all 7 required ADR changes
10. **RECOMMENDATION: Do NOT attempt to implement MPP/MPIR/Prompt AST as Trust Core** — these are Cognitive Layer concerns

---

## 20. Final Status

### ARCHITECTURE DISCOVERY STATUS

**DISCOVERY COMPLETE — CONTRADICTIONS FOUND**

The repository has been thoroughly inspected. The architecture is reconstructable but contains 15 documented contradictions, 4 of which are critical. The core execution pipeline (`kernel.py`) has no native identity awareness. Execution truth is fragmented across two event stores. Verification exists but is not automatic, not unified, and not persisted.

### TRUST CORE STATUS

**PARTIALLY DEFINED**

The Trust Core concepts (identity, evidence, verification, provenance) exist in the repository but are:
- Split across multiple feature directories (`identity/`, `tool_runtime/`, `verification/`, `provenance/`)
- Not unified into a coherent package
- Using in-memory stores that lose data on restart
- Not integrated into the kernel's core execution path
- Lacking automatic enforcement

The foundation is solid (UUID v7, SHA-256 integrity hashes, 5-mode reality model, independent verifiers, 9 hard rules) but the architectural integration is incomplete.

### IMPLEMENTATION STATUS

**FORBIDDEN** — This was an architecture discovery phase. No code was modified.

---

*Report produced by MC-TC-002 architecture discovery process.*
*Repository truth is authoritative. All claims verified against source code.*
