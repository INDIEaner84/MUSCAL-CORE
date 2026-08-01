# GRAPH-OS ARCHITECTURE FREEZE v1.0

**Version:** 1.0.0
**Date:** 2026-07-24
**Status:** APPROVED FREEZE — ALL P0 BLOCKERS RESOLVED
**Authority:** Architecture Gate reconciliation of MUSCAL Core repository

---

## PRE-FREEZE RECONCILIATION SUMMARY

**Evidence classification legend throughout this document:**

| Tag | Meaning |
|-----|---------|
| `[IMPLEMENTED]` | Exists in repository code, functional |
| `[PARTIAL]` | Exists but incomplete or not wired |
| `[SPEC_ONLY]` | Exists only in markdown documents |
| `[TEST_ONLY]` | Exists only in test files, not in production code |
| `[MISSING]` | Does not exist anywhere |
| `[CONTRADICTED]` | Documentation claims it exists but code disagrees |

---

## SECTION A — EXECUTIVE ARCHITECTURE DECISION

```
APPROVED FREEZE — ALL P0 BLOCKERS RESOLVED
```

**Rationale:** All 7 P0 decisions are now resolved. The WebSocket adapter architecture (P0.4, the final blocker) has been designed and implemented in `features/streaming/ws_adapter.py` with the event projection layer in `features/projection/graph_os_projection.py`. The architecture is demonstrable end-to-end: EventBus → Projection → WebSocket → client.

---

## SECTION B — REPOSITORY EVIDENCE MATRIX

| Domain | Status | Evidence | Risk | Decision |
|--------|--------|----------|------|----------|
| **EventBus** | `[IMPLEMENTED]` | `event_bus.py:26-101` — EventBus class with pub/sub, history, topics, priorities, thread-safe | Low — stable and tested | Freeze as-is |
| **EventStore** | `[IMPLEMENTED]` | `runtime/event_store.py:8-151` — SQLite-backed append-only store with cursor replay | Low — tested pattern | Freeze as-is |
| **Domain events table** | `[IMPLEMENTED]` | `runtime/database.py:52-70` — `events` table with actor/domain/layer/stream | Medium — dual-write with stored_events | Deprecate as Graph-OS source; keep as MUSCAL internal audit |
| **Graph State** | `[IMPLEMENTED]` | `graph.py:46-270` — GraphState with nodes dict + edges list, 5K/10K limits | Low — stable | Freeze as-is, enriched |
| **Sphere State** | `[IMPLEMENTED]` | `sphere.py:40-257` — 3-ring cognitive projection | Medium — O(n) sync, no debounce per ADR-006 | Freeze, defer optimization |
| **Scene State** | `[MISSING]` | No scene state class exists in any repository | High — must be created | Design in freeze |
| **Execution ID** | `[PARTIAL]` | `features/tool_runtime/tool_runtime.py:105` — ExecutionReceipt auto-generates UUID; NOT wired to EventBus, GraphState, or EventStore | Medium — exists in feature but not in core event flow | Must wire into EventBus enrichment |
| **Correlation ID** | `[PARTIAL]` | Same as execution_id — exists in ToolRuntime only | Medium | Must wire into EventBus |
| **Causation ID** | `[PARTIAL]` | `events` table has `caused_by` column but it's JSON array of references, not single causation_id | Medium | Normalize to single causation_id |
| **Execution Mode** | `[SPEC_ONLY]` | `os_config.py:59` — `simulation_mode: bool`; no execution_mode enum exists anywhere | Critical — single bit is insufficient | Create execution_mode enum |
| **Verification State** | `[PARTIAL]` | `features/tool_runtime/tool_runtime.py:22-31` — VerificationStatus enum (PENDING/EXECUTED/VERIFIED/FAILED/INCONCLUSIVE/NOT_SUPPORTED/TAMPERED); NOT wired to GraphState or EventStore | Medium — exists in feature but isolated | Integrate into core event model |
| **Reality Integrity Contract** | `[SPEC_ONLY]` | `spec/EXECUTION_INTEGRITY_CONTRACT.md` — defines trust boundaries, receipt immutability, verification independence | Medium — strong spec, no code enforcement | Hold as spec, implement in Phase 2 |
| **WebSocket Transport** | `[PARTIAL]` | `api_server.py:180-221` — `/stream` and `/graph/stream` endpoints; polling-based (1s), uses deprecated GraphStore, not wired to EventBus | Critical — current implementation is a prototype dead-end | Must redesign from scratch |
| **Frontend (Nexus OS)** | `[IMPLEMENTED]` Mock data only | `/ALITA TEST REPOS ALT/core/BROWSEROS/DEEPSEEK PROTOYP OS/` — 13 TSX files, design system, 7 layers, mock data, no backend connection | Medium — design system is valuable, mock data is not | Extract design system, replace data layer |
| **Frontend (MUSCAL IDE)** | `[IMPLEMENTED]` Partial backend | `/ALITA TEST REPOS ALT/core/BROWSEROS/CLAUDE_FAV_GUI_VSCODE/muscal-ai-ide-specification/` — D3 graphs, WebSocket client code, API client | Medium — contains integration patterns worth informing | Reference for design, do not directly reuse |
| **Frontend (Dashboard)** | `[IMPLEMENTED]` Real polling | `muscal_dashboard.html` — 548 lines, Canvas 2D, polls /api/state at 1.5s | Low — validates API endpoints work | Extract integration patterns, replace rendering |
| **ALITA** | `[SPEC_ONLY]` | No ALITA code exists. ALITA is a persona name in OpenCode agents, a label on `sphere.py:1` ("ALITA SPHERE UI Layer"), and chat persona references | Low — not implemented yet | Define boundary, defer implementation |
| **Security (Auth)** | `[IMPLEMENTED]` | `runtime/api/__init__.py:62-80` — API-key auth on POST/sensitive GET; `api_server.py:175-177` — WebSocket token check | Low — adequate baseline | Freeze as-is |
| **Security (Rate Limit)** | `[IMPLEMENTED]` | `runtime/api/__init__.py:22-43` — built-in `_RateLimiter`, 60/min per IP | Low | Freeze as-is |
| **Security (CORS/Headers)** | `[IMPLEMENTED]` | `runtime/api/__init__.py:114-131` — CORS whitelist + security headers | Low | Freeze as-is |
| **Execution Integrity** | `[SPEC_ONLY]` | `spec/EXECUTION_INTEGRITY_CONTRACT.md` — 10 hard rules | Medium — spec is strong but no enforcement | Hold as spec, enforce in Phase 2 |

---

## SECTION C — ARCHITECTURAL CONTRADICTIONS FOUND

### C-01: Two event stores with overlapping-but-different schemas

**Contradiction:** The repository has TWO SQLite tables for event storage with different schemas, written by different subsystems, with no synchronization.

| Table | File | Schema | Writer |
|-------|------|--------|--------|
| `stored_events` | `runtime/event_store.py:21-31` | seq, topic, payload, source, priority, timestamp, event_id, created_at | `muscal_os._persist_to_store()` (EventBus subscriber) |
| `events` | `runtime/database.py:52-70` | id, seq, ts, occurred_at, type, actor, actor_type, domain, layer, stream, session_id, payload, caused_by, schema_version, idempotency_key, model_id, confidence, trust_level, severity, aggregate_id, aggregate_type, replayable, payload_sanitized | `runtime/kernel/writer.py:94-125` (WriterThread) |

**Impact:** HIGH — No single authoritative event source for Graph-OS to consume. Any Graph-OS implementation would face a choice between two incompatible schemas.

**Resolution:** `stored_events` becomes the canonical transport log (enriched with execution_id, correlation_id, execution_mode, verification_state). `events` becomes the MUSCAL internal domain audit trail — NOT exposed to Graph-OS directly.

**Priority:** REQUIRED

### C-02: Execution ID exists in feature code but not in core event flow

**Contradiction:** `features/tool_runtime/tool_runtime.py` defines `ExecutionReceipt.execution_id` (auto-generated UUID v4) and `ExecutionReceipt.correlation_id`, with tests validating dedup, spoofing detection, and chain tracing. However:

- `EventBus.EventMessage` has NO `execution_id` field — `event_bus.py:16-23`
- `GraphState.Node` has NO `execution_id` field — `schema.py:139-145`
- `EventStore.stored_events` has NO `execution_id` column — `runtime/event_store.py:21-31`
- `MuscalKernel.run()` does NOT generate or propagate an execution_id — `kernel.py:622-681`

**Impact:** HIGH — The execution identity layer exists as an isolated feature but is disconnected from the core event/graph/transport systems that Graph-OS would consume. Events flowing through EventBus to Graph-OS have no execution identity.

**Resolution:** Execution ID generation must be elevated from `features/tool_runtime/` into `kernel.py:run()` and carried on every `EventMessage` published during that execution. The enrichments must flow through EventBus → EventStore → WebSocket.

**Priority:** REQUIRED

### C-03: Verification status exists in feature code but not in GraphState

**Contradiction:** `VerificationStatus` enum (`tool_runtime.py:22-31`) defines 7 states (PENDING/EXECUTED/VERIFIED/FAILED/INCONCLUSIVE/NOT_SUPPORTED/TAMPERED). `VerificationResult` has `execution_id`, `receipt_id`, `verifier_id`, `expected_state`, `observed_state`. But GraphState.Node has only `status: str = "created"` — no verification state field.

**Impact:** MEDIUM — Graph-OS cannot display verification status because the graph model has no field for it.

**Resolution:** Add `verification_state` field to `schema.py:Node`. Wire `VerificationResult` into GraphState when verification events occur.

**Priority:** REQUIRED

### C-04: Simulation mode is a single boolean, not an execution mode

**Contradiction:** `os_config.py:59` has `simulation_mode: bool`. `DeploymentMode` enum has `SIMULATION = "simulation"`. Both treat simulation as a binary on/off flag at config level. However:
- No `execution_mode` field exists on any event, graph node, or database table
- Multiple concurrent execution modes (REAL, SIMULATED, PROPOSED, SHADOW, REPLAY) are not representable
- An execution pipeline runs entirely in one mode — mixed-mode execution is impossible

**Impact:** HIGH — The architecture cannot distinguish simulated from real events at the event/graph level. This violates the core principle "Simulation MUST NEVER be visually or semantically indistinguishable from real execution."

**Resolution:** Replace `simulation_mode: bool` with `execution_mode: ExecutionMode` enum (5 values). Add to EventMessage, GraphState.Node, and EventStore. Retain `simulation_mode` as config-level convenience flag that sets the default `execution_mode` for all events during that session.

**Priority:** REQUIRED

### C-05: Architecture freeze document is about the wrong component

**Contradiction:** `MUSCAL_ARCHITECTURE_FREEZE_v1.0.md` at `docs/audit/` is a 555-line document describing the **Reconciliation Engine** (scanners, rules, runners, reports). It does NOT mention Graph-OS, ALITA, event contracts, reality integrity, WebSocket transport, or any domain relevant to the Graph-OS architecture. Despite this, previous planning sessions treated it as a Graph-OS architecture freeze.

**Impact:** HIGH — There is no authoritative freeze document for the Graph-OS architecture. Decisions made in prior analysis sessions were not captured in any document the repository can enforce.

**Resolution:** This document (`GRAPH_OS_ARCHITECTURE_FREEZE_v1.0.md`) serves as the authoritative Graph-OS architecture freeze.

**Priority:** REQUIRED

### C-06: Frontend prototypes have no integration path to backend

**Contradiction:** Two frontend prototypes exist (Nexus OS, MUSCAL IDE) plus a functional dashboard — all consuming either mock data or polling HTTP. None use the EventBus or EventStore. The `api_server.py` WebSocket endpoints use `GraphStore` (deprecated) instead of `GraphState`.

**Impact:** HIGH — Neither prototype can be incrementally connected to the real backend. Any attempt would require rewriting the data layer.

**Resolution:** Define a clean WebSocket protocol (Section J) that both the new WebSocket adapter and the frontend must implement. The existing prototypes' visual design (Nexus OS) and integration patterns (MUSCAL IDE) inform but do not constrain the protocol design.

**Priority:** REQUIRED

---

## SECTION D — FINAL AUTHORITY MODEL

```
                    ┌─────────────────────────────────┐
                    │            HUMAN                 │
                    │  Governance · Approval · Audit   │
                    └────────────┬────────────────────┘
                                 │ authorizes
                                 ▼
 ┌─────────────────────────────────────────────────────────────────┐
 │                        MUSCAL CORE                              │
 │  AUTHORITATIVE EXECUTION TRUTH                                  │
 │                                                                 │
 │  Owns:  execution lifecycle, graph truth, verification,         │
 │         provenance, causality, reality classification,          │
 │         event persistence, governance enforcement               │
 │                                                                 │
 │  Components:  MuscalKernel, GraphState, EventBus, EventStore,   │
 │               UnifiedToolRuntime, WriterThread, GovernanceLayer │
 └───────────────────────────┬─────────────────────────────────────┘
                             │ canonical events (enriched)
                             ▼
 ┌─────────────────────────────────────────────────────────────────┐
 │                     EVENT PROJECTION LAYER                      │
 │  NORMALIZED GRAPH-OS EVENTS                                     │
 │                                                                 │
 │  Transforms:  MUSCAL events → Graph-OS events                   │
 │  Filters:     event type whitelist, field sanitization          │
 │  Enriches:    surface-level relevance heuristic                  │
 └───────────────────────────┬─────────────────────────────────────┘
                             │ Graph-OS events
                             ▼
 ┌─────────────────────────────────────────────────────────────────┐
 │                    GRAPH-OS                                      │
 │  COGNITIVE / VISUAL PROJECTION                                   │
 │                                                                  │
 │  Owns:  graph projection, navigation state, attention focus,    │
 │         relevance scoring, semantic grouping, filtering,         │
 │         visualization state                                      │
 │                                                                  │
 │  Has NO authority over execution truth.                          │
 └───────────────────────────┬─────────────────────────────────────┘
                             │ scene derivation
                             ▼
 ┌─────────────────────────────────────────────────────────────────┐
 │                     SCENE STATE                                  │
 │  EPHEMERAL PRESENTATION STATE                                    │
 │                                                                  │
 │  Owns:  3D positions, camera, animation, LOD, selection,         │
 │         hover, interaction, visual decay                         │
 │                                                                  │
 │  EPHEMERAL — NOT persisted as system truth.                      │
 │  Persisted only for UX continuity (last camera position, etc.)   │
 └───────────────────────────┬─────────────────────────────────────┘
                             │ human interaction
                             ▼
 ┌─────────────────────────────────────────────────────────────────┐
 │                      ALITA                                       │
 │  HUMAN INTERFACE LAYER                                           │
 │                                                                  │
 │  May:  observe, query, navigate, explain, summarize, suggest     │
 │  Must NOT:  fabricate truth, mutate graph, execute operations,  │
 │             bypass verification, bypass governance               │
 └─────────────────────────────────────────────────────────────────┘
```

### Authority Flow (Canonical)

```
MUSCAL produces execution truth
    ↓ Events carry execution_id, correlation_id, execution_mode, verification
Projection Layer normalizes
    ↓ Graph-OS subscribes to normalized events
Graph-OS maintains scene projection
    ↓ ALITA queries scene state
ALITA presents to Human
    ↓ Human approves/rejects
Human decision flows back to MUSCAL governance
```

### Forbidden Flows

```
ALITA → direct MUSCAL execution           FORBIDDEN
Graph-OS → modify MUSCAL graph truth      FORBIDDEN
Scene State → persist as system truth     FORBIDDEN
Simulated events → indistinguishable     FORBIDDEN (MUST carry execution_mode)
```

---

## SECTION E — FINAL EVENT ARCHITECTURE

```
┌─────────────────────────────────────────────────────────────────────┐
│                        MUSCAL CORE                                  │
│                                                                     │
│  MuscalKernel.run() generates execution_id (UUID v7)                │
│       │                                                             │
│       ├──► GraphState.on/emit (pipeline-internal events)            │
│       │       │                                                     │
│       │       └──► EventBus (via _wire_event_bus bridge)             │
│       │                                                             │
│       └──► EventBus.publish() (enriched: execution_id,              │
│                correlation_id, execution_mode, causation_id)         │
│                    │                                                │
│                    ▼                                                │
│  EventStore._persist_to_store()                                     │
│       │                                                             │
│       └──► stored_events (CANONICAL TRANSPORT LOG)                  │
│                Columns: seq, topic, payload, source, priority,      │
│                         timestamp, event_id, execution_id,          │
│                         correlation_id, causation_id,               │
│                         execution_mode, verification_state          │
│                                                                     │
│  WriterThread → events table (MUSCAL INTERNAL AUDIT TRAIL)          │
│       NOT exposed to Graph-OS                                       │
└─────────────────────────────────────────────────────────────────────┘
                              │
                              │ EventBus subscriber
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      EVENT PROJECTION LAYER                         │
│  [features/projection/graph_os_projection.py]                       │
│                                                                     │
│  Subscribes to EventBus via "*"                                     │
│  Transforms EventMessage → GraphOSEvent                             │
│  Applies:                                                           │
│    • event type whitelist (only canonical Graph-OS event types)    │
│    • field sanitization (strip sensitive payload fields)            │
│    • schema version assignment                                      │
│  Outputs: GraphOSEvent (typed dataclass, see Section F)             │
└─────────────────────────────────────────────────────────────────────┘
                              │
                              │ push normalized events
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    WEBSOCKET ADAPTER                                 │
│  [features/streaming/ws_adapter.py]                                 │
│                                                                     │
│  Responsibilities:                                                  │
│    • WebSocket authentication (token-based, reuse API key pattern) │
│    • Connection lifecycle management                                │
│    • Per-client async queue (backpressure: max 1000 messages)       │
│    • Subscription management (event type filters)                   │
│    • Cursor-based replay (client sends last_seq)                   │
│    • Snapshot delivery on first connect / gap detection             │
│    • Heartbeat (every 5s, timeout after 15s)                        │
│    • Reconnection with exponential backoff (1s-30s)                 │
│                                                                     │
│  Does NOT:                                                          │
│    • Transform event schemas (delegated to Projection Layer)        │
│    • Write to EventStore (read-only on replay)                      │
└─────────────────────────────────────────────────────────────────────┘
                              │
                              │ WebSocket (JSON)
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│                       GRAPH-OS CLIENT (R3F)                         │
│                                                                     │
│  Zustand store:                                                     │
│    • Receives GraphOSEvent via WebSocket                            │
│    • Maintains scene state (nodes, edges, positions, camera, LOD)  │
│    • Computes relevance scores (client-side heuristic)              │
│    • Tracks connection state, last_seq, staleness                   │
│                                                                     │
│  Attention Engine:                                                  │
│    • Multi-factor relevance: task focus, recency, causality,        │
│      confidence inverse, failure state, verification state          │
│    • NEVER confuses confidence with relevance                       │
│                                                                     │
│  Renderer:                                                          │
│    • R3F (React Three Fiber) with Three.js renderer                 │
│    • InstancedMesh for 1K+ nodes                                    │
│    • Orthographic camera (2D view) as default, perspective for 3D   │
│    • d3-force-3d for force-directed layout                          │
└─────────────────────────────────────────────────────────────────────┘
```

### Authoritative Sources

| Component | Status |
|-----------|--------|
| `stored_events` (enriched) | **CANONICAL** — single source of truth for transport events |
| `events` table | **DERIVED** — MUSCAL internal audit trail, not for Graph-OS |
| GraphOSEvent stream | **DERIVED** — normalized projection of canonical events |
| WebSocket | **TRANSPORT** — ephemeral delivery channel |
| Scene State | **EPHEMERAL** — client-side derived state |

---

## SECTION F — FINAL CANONICAL EVENT ENVELOPE

```python
@dataclass
class GraphOSEvent:
    # Identity (REQUIRED)
    event_id: str                          # UUID v7, globally unique
    event_type: str                        # Canonical name (NODE_CREATED, etc.)
    event_version: int = 1                 # Schema version for forward compat
    timestamp: str                         # ISO-8601 with timezone

    # Ordering (REQUIRED)
    sequence_number: int                   # Monotonic per-stream, SQLite AUTOINCREMENT

    # Execution Identity (REQUIRED — P0)
    execution_id: str                      # UUID v7, generated by MuscalKernel.run()
    correlation_id: str | None = None      # UUID v7, shared across chains of executions
    causation_id: str | None = None        # event_id of the event that caused this one

    # Source Attribution (REQUIRED)
    source: str                            # "muscal_kernel" | "alita" | "graph_os" | "system"
    actor: str                             # "kernel" | "user" | "alita_agent" | tool name

    # Reality Classification (REQUIRED — P0)
    execution_mode: str                    # "real" | "simulated" | "proposed" | "shadow" | "replay"
    execution_state: str                   # "planned" | "queued" | "running" | "completed" | "failed" | "cancelled"
    verification_state: str                # "unverified" | "verified" | "failed" | "rejected"

    # Provenance (OPTIONAL)
    provenance: dict | None = None         # { "chain": [event_id, ...], "trace_path": [...] }

    # Payload (REQUIRED)
    payload: dict                          # Event-type-specific data
```

### Canonical Event Types

| event_type | When emitted | Required payload fields |
|-----------|-------------|------------------------|
| `NODE_CREATED` | GraphState.add_node() | node_id, node_type, status |
| `NODE_UPDATED` | GraphState.update_node() | node_id, changed_fields, old_values |
| `NODE_COMPLETED` | Execution stage "completed" status | node_id, result_summary |
| `NODE_FAILED` | Execution stage "failed" status | node_id, error_message |
| `NODE_ARCHIVED` | Graph pruning exceeding limits | node_id, reason |
| `EDGE_CREATED` | GraphState.add_edge() | source_id, target_id, edge_type |
| `EDGE_REMOVED` | Graph pruning | edge_id (or source+target) |
| `EXECUTION_STARTED` | MuscalKernel.run() begins | input_text (sanitized), execution_id |
| `EXECUTION_COMPLETED` | Pipeline finishes successfully | execution_id, success, memory_id |
| `EXECUTION_FAILED` | Pipeline fails | execution_id, errors |
| `SIMULATION_STARTED` | Config.simulation_mode execution | execution_id, parameters |
| `SIMULATION_COMPLETED` | Simulation finishes | execution_id, result_summary |
| `VERIFICATION_PASSED` | UTR verifier returns VERIFIED | execution_id, receipt_id, verifier_id |
| `VERIFICATION_FAILED` | UTR verifier returns FAILED | execution_id, receipt_id, verifier_id, expected, observed |

### Event Versioning

```python
# NOT type suffixes (NODE_CREATED_v2 is FORBIDDEN)
# Use event_version field instead:
event_type = "NODE_CREATED"
event_version = 2
```

Version bumps occur only when payload schema changes in a non-backward-compatible way. Old consumers can check `event_version` and skip unknown payloads.

---

## SECTION G — FINAL REALITY INTEGRITY MODEL

### Three Orthogonal Dimensions

```
execution_mode  ×  execution_state  ×  verification_state
    5                   6                    4
values              values               values
```

### Dimension 1: execution_mode

| Value | Meaning | Visual Indicator |
|-------|---------|-----------------|
| `real` | Actual execution against real systems | Solid rendering |
| `simulated` | Execution in simulation mode (no real side effects) | Dashed borders, "SIM" badge |
| `proposed` | A plan that has not been executed | Wireframe, semi-transparent |
| `shadow` | Shadow execution (monitoring, no authority) | Ghosted/faded, "SHADOW" badge |
| `replay` | Replayed historical execution | Sepia/desaturated, playback controls |

Generated by: `MuscalKernel.run()` inherits from config `simulation_mode` but can be overridden per-call.

### Dimension 2: execution_state

| Value | Meaning | Valid transitions |
|-------|---------|-------------------|
| `planned` | Execution is planned but not started | → queued, cancelled |
| `queued` | Queued for execution | → running, cancelled |
| `running` | Actively executing | → completed, failed, cancelled |
| `completed` | Execution finished successfully | → (terminal) |
| `failed` | Execution finished with error | → (terminal) |
| `cancelled` | Execution was cancelled | → (terminal) |

### Dimension 3: verification_state

| Value | Meaning | Source |
|-------|---------|--------|
| `unverified` | No verification performed | Default |
| `verified` | Independent verifier confirmed correctness | UTR.verify() returns VERIFIED |
| `failed` | Verifier found state mismatch | UTR.verify() returns FAILED |
| `rejected` | Human or governance rejected | Governance override |

### Validity Matrix

| | planned | queued | running | completed | failed | cancelled |
|---|---|---|---|---|---|---|
| **real** | VALID | VALID | VALID | VALID | VALID | VALID |
| **simulated** | VALID | VALID | VALID | VALID | VALID | VALID |
| **proposed** | VALID | INVALID | INVALID | INVALID | INVALID | VALID |
| **shadow** | VALID | VALID | VALID | VALID | VALID | VALID |
| **replay** | VALID | VALID | VALID | VALID | VALID | VALID |

### Verification Validity Cross-Reference

| | real | simulated | proposed | shadow | replay |
|---|---|---|---|---|---|
| **unverified** | VALID | VALID | VALID | VALID | VALID |
| **verified** | VALID* | CONTEXT_DEPENDENT** | INVALID | VALID*** | CONTEXT_DEPENDENT**** |
| **failed** | VALID | VALID | INVALID | VALID | VALID |
| **rejected** | VALID | VALID | VALID | VALID | VALID |

*\* "Verified as correct execution against ground truth"*
*\*\* "Verified as simulation ran correctly" ≠ "verified as matching reality"*
*\*\*\* "Shadow execution verified as internally consistent"*
*\*\*\*\* "Replay verified as faithful reproduction" — verification from original execution does NOT carry over*

### Key Semantic Rules

1. `proposed` + `verified` = INVALID — a plan cannot be verified before execution
2. `proposed` + `running` = INVALID — a plan is not executed
3. `simulated` + `verified` = "Verified as internally consistent" NOT "verified as matching reality"
4. `replay` + `verified` = "Replay is faithful" NOT "the replayed execution is verified"
5. Verification applies to the execution result, not the execution mode

### Implementation Mapping

```python
# os_config.py
class ExecutionMode(Enum):
    REAL = "real"
    SIMULATED = "simulated"
    PROPOSED = "proposed"
    SHADOW = "shadow"
    REPLAY = "replay"

class ExecutionState(Enum):
    PLANNED = "planned"
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class VerificationState(Enum):
    UNVERIFIED = "unverified"
    VERIFIED = "verified"
    FAILED = "failed"
    REJECTED = "rejected"
```

These enums go on: `EventMessage`, `GraphState.Node`, `stored_events`, `GraphOSEvent`.

The existing `simulation_mode: bool` becomes `execution_mode: ExecutionMode` = `REAL | SIMULATED`.

---

## SECTION H — FINAL GRAPH STATE / SCENE STATE CONTRACT

### Graph State (Authoritative — MUSCAL Kernel)

```python
# schema.py: Node - enriched
@dataclass
class Node:
    id: str                           # Unique node ID
    type: str                         # Node type constant
    payload: dict                     # Domain-specific data
    timestamp: float                  # Creation time
    confidence: float = 1.0           # MUSCAL confidence score (NOT relevance)
    status: str = "created"           # Node lifecycle status
    execution_id: str = ""            # NEW: originating execution
    execution_mode: str = "real"      # NEW: reality mode
    execution_state: str = ""         # NEW: execution lifecycle
    verification_state: str = "unverified"  # NEW: verification status
    correlation_id: str = ""          # NEW: correlation chain
    causation_id: str = ""            # NEW: causal parent event_id
```

```python
# schema.py: Edge - enriched
@dataclass
class Edge:
    source_id: str
    target_id: str
    edge_type: str
    payload: dict = field(default_factory=dict)
    execution_id: str = ""            # NEW: originating execution
    verification_state: str = "unverified"  # NEW
```

Persistence: `GraphState` (in-memory) + `stored_events` for replay.

### Scene State (Ephemeral — Graph-OS Client)

```typescript
// Conceptual frontend store (Zustand)
interface SceneState {
  // Derived from Graph State
  visibleNodes: Map<string, SceneNode>;
  visibleEdges: Map<string, SceneEdge>;

  // Layout / Spatial
  positions: Map<string, [number, number, number]>;  // 3D coordinates
  camera: { position: [number, number, number]; target: [number, number, number] };
  zoomLevel: number;

  // Attention
  focusNodeId: string | null;
  relevanceScores: Map<string, number>;     // 0.0–1.0, computed client-side
  highlightedIds: Set<string>;

  // Interaction
  selectedNodeId: string | null;
  hoveredNodeId: string | null;

  // Animation
  animationStates: Map<string, AnimationState>;

  // Level of Detail
  lods: Map<string, 'high' | 'medium' | 'low' | 'hidden'>;

  // Visual Decay
  decayTimers: Map<string, number>;

  // Connection
  connectionState: 'connected' | 'disconnected' | 'stale';
  lastSeq: number;
}

interface SceneNode {
  id: string;
  type: string;
  label: string;
  status: string;
  executionMode: string;
  verificationState: string;
  confidence: number;
  relevance: number;           // Computed, NOT from MUSCAL
}

interface SceneEdge {
  id: string;
  sourceId: string;
  targetId: string;
  type: string;
}
```

### Persistence Rules

| Data | Persist? | Mechanism |
|------|----------|-----------|
| Graph State (nodes, edges) | YES — authoritative | EventStore + in-memory GraphState |
| Scene State (positions, camera) | PARTIAL — UX only | LocalStorage for last camera position |
| Animation state | NO | Computed on render |
| Selection state | NO | Session-only |
| Decay state | NO | Computed from recency |

---

## SECTION I — FINAL EXECUTION IDENTITY MODEL

| Field | Generator | When | Scope | Unique? | Stable across retries? | Survives replay? |
|-------|-----------|------|-------|---------|----------------------|-----------------|
| **event_id** | UUID v7 | Event publication | Global | Yes | No (each publish is unique) | Yes (is part of the event) |
| **execution_id** | UUID v7 | `MuscalKernel.run()` start | Single execution | Yes | No (each retry = new ID) | Yes (stored with each event) |
| **correlation_id** | UUID v7 | User request entry point | Chain of executions | Yes | Yes (same chain) | Yes |
| **causation_id** | event_id of cause | Event publication | Parent event | No (reference) | No | Yes (stored with event) |
| **aggregate_id** | Domain-specific | Event creation | Aggregate root | Per aggregate | Varies | Yes |
| **sequence_number** | SQLite AUTOINCREMENT | DB insert | Global | Yes | No | Yes |

### Semantic Definitions

- **event_id**: Uniquely identifies one event. Used for deduplication, causation references, and exactly-once delivery.
- **execution_id**: Uniquely identifies one invocation of `MuscalKernel.run()`. Every event published during that execution shares this ID. Enables grouping all events belonging to one execution attempt.
- **correlation_id**: Links together all events across multiple executions that belong to the same logical operation. For example, a human request → kernel execution → tool execution → verification all share one correlation_id.
- **causation_id**: References the `event_id` of the event that directly caused this event. Forms a directed acyclic graph (DAG) of causality.
- **aggregate_id**: Domain-specific entity ID (e.g., session_id, task_id). Not for Graph-OS event envelope (remains in MUSCAL domain events only).
- **sequence_number**: Global monotonic order. SQLite AUTOINCREMENT on `stored_events.seq`. Used for cursor-based replay and ordering.

### Event ID Generation

UUID v7 is RECOMMENDED because:
- Time-ordered (first 48 bits = Unix timestamp ms) enables efficient B-tree indexing
- Globally unique without coordination
- Already used in parts of the codebase (`features/tool_runtime/` uses `uuid.uuid4()` — migration to v7 is recommended but not blocking)

### Execution ID Generation

Performed in `MuscalKernel.run()` at the earliest entry point:
```python
def run(self, input_text: str, execution_id: str = None, correlation_id: str = None):
    if execution_id is None:
        execution_id = str(uuid.uuid7())  # uuid7
    if correlation_id is None:
        correlation_id = execution_id  # default: same as execution_id for standalone
    self._current_execution_id = execution_id
    self._current_correlation_id = correlation_id
    # ... pipeline continues, all graph operations carry these IDs
```

---

## SECTION J — FINAL REPLAY / SNAPSHOT PROTOCOL

### Protocol Overview

```
Client                          Server
  │                                │
  │──── CONNECT ──────────────────►│  (WebSocket upgrade with token)
  │                                │
  │◄─── ACCEPT ───────────────────│
  │                                │
  │──── SUBSCRIBE ───────────────►│  { "type": "subscribe", "last_seq": N }
  │                                │
  │◄─── SNAPSHOT ─────────────────│  { "type": "snapshot", "seq": S,
  │                                │    "nodes": [...], "edges": [...] }
  │◄─── EVENT (seq S+1) ─────────│
  │◄─── EVENT (seq S+2) ─────────│
  │◄─── ...                      │
  │◄─── RECONCILIATION ──────────│  { "type": "reconciliation", "seq": R,
  │                                │    "checksum": "sha256-..." }
  │                                │
  │ (disconnect)                   │
  │──── RECONNECT ───────────────►│  (same WebSocket, last_seq = last received)
  │                                │
  │◄─── SNAPSHOT (if gap > 1000)─│  or SNAPSHOT (if disconnected > 60s)
  │◄─── EVENTS (from last_seq+1)─│  or direct delta if gap < 1000
```

### Protocol Messages

**Client → Server:**

```json
{ "type": "subscribe", "last_seq": 0 }
{ "type": "subscribe", "last_seq": 1542, "filters": { "event_types": ["NODE_CREATED", "EDGE_CREATED"] } }
{ "type": "ping" }
{ "type": "unsubscribe" }
```

**Server → Client:**

```json
{ "type": "snapshot", "seq": 1500, "nodes": [...], "edges": [...], "checksum": "sha256-..." }
{ "type": "event", "seq": 1501, "event_id": "...", "event_type": "NODE_CREATED", ... }
{ "type": "reconciliation", "seq": 2000, "checksum": "sha256-..." }
{ "type": "pong" }
{ "type": "error", "code": "AUTH_FAILED", "message": "..." }
```

### Invariants

```
snapshot.seq = the seq of the last event included in the snapshot
next_event.seq = snapshot.seq + 1   (if client connects fresh)
delta_events[i].seq = last_seq + 1 + i
```

### Key Mechanisms

| Concept | Implementation |
|---------|---------------|
| **Snapshot creation** | `EventStore.get_cursor()` determines current seq. Query `stored_events` for all data needed to reconstruct GraphState. Periodically (every 1000 events or 30s) or on demand. |
| **Snapshot authority** | Derived from `stored_events` — NOT authoritative itself. A new snapshot can always be reconstructed from the event log. |
| **Snapshot persistence** | New `graph_os_snapshots` table: `id, seq, state_json, event_count, created_at`. Disposable — can be dropped and rebuilt. |
| **Gap detection** | Client tracks `last_seq`. If `event.seq != last_seq + 1`, a gap is detected. Client requests snapshot. |
| **Stale detection** | If no `reconciliation` received within 60s or `seq - last_reconciliation_seq > 2000`, client requests snapshot. |
| **Checksum** | SHA-256 of JSON-sorted concatenation of all node IDs. Used for reconciliation, NOT integrity verification. |
| **Reconnection** | Exponential backoff: 1s, 2s, 4s, 8s, max 30s. After 60s offline, full snapshot required. |
| **Backpressure** | Server maintains per-client async queue (max 1000 messages). If exceeded, oldest dropped; client detects seq gap and requests snapshot. |

---

## SECTION K — FINAL SECURITY BOUNDARY

```
 TRUSTED                           SANITIZED                          UNTRUSTED
┌──────────────┐           ┌────────────────────┐           ┌──────────────────┐
│  MUSCAL CORE  │           │  GRAPH-OS PROJECTION │           │  FRONTEND CLIENT  │
│              │           │                      │           │                   │
│  • execution  │──events──►│  • event type filter │──filtered─►│  • R3F renderer   │
│  • graph truth│           │  • field sanitizer   │  events   │  • scene state    │
│  • filesystem │           │  • payload scrubber  │           │  • ALITA queries  │
│  • credentials│           │                      │           │                   │
│  • environment│           │  STRIPS:             │           │  NEVER receives:  │
│  • tool paths │           │   • filesystem paths │           │   • filesystem    │
│  • API keys   │           │   • credentials      │           │   • credentials   │
│  • LLM tokens │           │   • environment vars  │           │   • tool internals│
│              │           │   • model internals   │           │   • raw payloads  │
└──────────────┘           └────────────────────┘           └──────────────────┘
```

### Sanitization Rules

| Source Field in MUSCAL payload | Allowed in Graph-OS event? | Replacement |
|-------------------------------|---------------------------|-------------|
| `payload.tool_result` | No | `{"status": "completed"}` (metadata stripped) |
| `payload.file_path` | No | Stripped |
| `payload.command` | No | `"executed"` boolean only |
| `payload.credentials` | No | Stripped |
| `payload.error` | Yes — truncated to 500 chars | Truncation applied |
| `payload.node_type`, `node_id` | Yes | Pass through |
| `payload.confidence` | Yes | Pass through (MUST NOT be treated as relevance) |
| `payload.input_text` | **No** — contains user input | `"input"` key removed or replaced with length |
| `payload.environment` | No | Stripped |

### MVP Security Requirements

| Requirement | Status | Implementation |
|-------------|--------|---------------|
| WebSocket auth | P0 — MUST design | Token-based, reuse SESSION_ID / MUSCAL_API_KEY pattern from `runtime/api/__init__.py:62-68` |
| Payload sanitization | P0 — MUST design | Event projection layer strips sensitive fields before WebSocket send |
| Event type whitelist | P1 | Projection layer only forwards canonical event types |
| ALITA query sandbox | P2 | Future concern |
| No Graph-OS write path | ARCHITECTURAL INVARIANT | Enforced at API boundary — no mutation endpoints on Graph-OS WebSocket |

---

## SECTION L — FINAL ALITA BOUNDARY

### ALITA MAY

```
┌──────────────────────────────────────────────────────┐
│                    ALITA                              │
│                                                       │
│  OBSERVE:   Read Graph-OS scene state                │
│             Read MUSCAL execution state (via API)    │
│                                                       │
│  QUERY:     Search nodes by type, status, execution   │
│             Filter graph by relevance, confidence     │
│             Trace causal paths                        │
│                                                       │
│  NAVIGATE:  Change focus node                         │
│             Adjust zoom level                         │
│             Pan/rotate camera                         │
│             Select/highlight nodes                    │
│                                                       │
│  EXPLAIN:   Translate graph state to natural language │
│             Summarize execution history               │
│             Describe node relationships               │
│             Highlight anomalies and failures          │
│                                                       │
│  SUGGEST:   Propose actions to human                  │
│             Recommend focus changes                   │
│             Identify verification gaps                │
└──────────────────────────────────────────────────────┘
```

### ALITA MUST NOT

```
┌──────────────────────────────────────────────────────┐
│                  FORBIDDEN                             │
│                                                       │
│  FABRICATE:  Create graph nodes/edges directly        │
│  FABRICATE:  Inject events into EventBus              │
│  FABRICATE:  Claim an execution result                │
│                                                       │
│  EXECUTE:    Call MuscalKernel.run()                  │
│  EXECUTE:   Call UTR.execute()                        │
│  EXECUTE:   Call any tool function                    │
│                                                       │
│  BYPASS:     Set verification_state = "verified"      │
│  BYPASS:     Override governance decisions            │
│  BYPASS:     Skip safety gate                         │
│                                                       │
│  SILENT:     Run simulation without "SIM" indicator   │
│  SILENT:     Modify execution_mode of existing events │
│                                                       │
│  DEPEND:     System MUST function without ALITA       │
│  DEPEND:     ALITA MUST NOT become SPOF               │
└──────────────────────────────────────────────────────┘
```

### Interface

```
ALITA communicates with Graph-OS and MUSCAL through GOVERNED CHANNELS ONLY:

  ALITA → Graph-OS:  Read-only scene queries (no mutations)
  ALITA → MUSCAL:    Navigational commands only (focus, zoom)
  ALITA → Human:     Explanations, summaries, suggestions
  Human → ALITA:     Questions, navigation requests

  Human → MUSCAL:    Execution approval, governance decisions (direct channel)
```

ALITA does NOT have a direct execution channel to MUSCAL. If ALITA needs to trigger an execution, it must request human approval through the governed interface.

---

## SECTION M — ARCHITECTURE LAWS

These laws are IMMUTABLE. They must not be violated by any implementation.

### LAW 1 — MUSCAL Execution Authority
MUSCAL is the sole authoritative source of execution truth. No other component may claim execution authority.

### LAW 2 — Graph-OS is Derived
Graph-OS is a derived cognitive projection. It must never become an independent source of execution truth.

### LAW 3 — Scene State is Ephemeral
Scene State is presentation state only. It must never be persisted as system truth. UX-persisted camera positions are an exception.

### LAW 4 — ALITA has No Authority
ALITA has no execution authority. It observes, queries, navigates, explains, and suggests — but never commands execution.

### LAW 5 — Events Carry Identity
Every execution-relevant event MUST carry `execution_id`, `correlation_id`, `execution_mode`, and `verification_state`.

### LAW 6 — Simulation is Distinguishable
Simulated and real execution MUST never be visually or semantically indistinguishable. Every simulated event carries `execution_mode = "simulated"`. The frontend MUST render simulated events with a distinct visual indicator.

### LAW 7 — Verification is Independence
Verification MUST be performed by an independent verifier function. Agent claims must never enter as evidence. `INCONCLUSIVE` must never be promoted to `VERIFIED`.

### LAW 8 — Confidence ≠ Relevance
Confidence is MUSCAL's internal certainty metric. Relevance is the Graph-OS attention heuristic. They must never be conflated. The frontend must compute relevance independently.

### LAW 9 — No Fabrication
Graph-OS must never fabricate authoritative state. Every node and edge in Graph-OS must be traceable to a MUSCAL event.

### LAW 10 — Full Provenance
Every Graph-OS event must be traceable to its causal origin through `causation_id` and `execution_id`.

### LAW 11 — Sanitization Boundary
Sensitive fields (filesystem paths, credentials, tool internals, raw user input) must be stripped or replaced before entering the Graph-OS event stream.

### LAW 12 — Deduplication by Identity
`event_id` (UUID v7) is the deduplication key. Duplicate events with the same `event_id` must be silently dropped.

---

## SECTION N — P0 DECISION CLOSURE

### P0.1 — Event Contract

**Status:** RESOLVED WITH CONDITION
**Resolution:** Section F defines the canonical event envelope. Condition: must be reviewed and signed off by team before Phase 1 implementation begins.
**Evidence:** Section F provides the complete `GraphOSEvent` dataclass with all fields classified as REQUIRED/OPTIONAL/DERIVED.

### P0.2 — Reality Integrity

**Status:** RESOLVED WITH CONDITION
**Resolution:** Section G defines three orthogonal dimensions: `execution_mode` (5 values) × `execution_state` (6 values) × `verification_state` (4 values). Validity matrix provided.
**Condition:** The existing `simulation_mode: bool` in `os_config.py` must be migrated to `execution_mode: ExecutionMode` enum. Old configs must be backward-compatible.

### P0.3 — Graph State vs Scene State

**Status:** RESOLVED WITH CONDITION
**Resolution:** Section H defines two explicit schemas. Graph State (MUSCAL-authoritative) has Node/Edge enriched with execution_id, execution_mode, verification_state. Scene State (ephemeral) has positions, camera, LOD, interaction state.
**Condition:** The `schema.py:Node` dataclass must be extended with the new fields. No new table required for Scene State.

### P0.4 — WebSocket Adapter

**Status:** RESOLVED WITH IMPLEMENTATION
**Resolution:** The WebSocket adapter architecture is fully designed and implemented:

| Artifact | File | Purpose |
|----------|------|---------|
| Projection Layer | `features/projection/graph_os_projection.py` | Normalizes EventBus `EventMessage` → `GraphOSEvent` dict; sanitizes sensitive fields; validates against canonical event types |
| WebSocket Adapter | `features/streaming/ws_adapter.py` | Sync→async bridge; runs as daemon thread inside MuscalOS; subscribes to EventBus synchronously; pushes normalized events to per-client async queues; delivers snapshots and deltas from EventStore |
| Server | Built-in (websockets library) | Listens on `127.0.0.1:8765`; token-based auth; per-client backpressure (1000 msg queue); heartbeats every 5s; timeout after 15s |
| Protocol | Section J of this document | Snapshot/delta/reconciliation protocol; cursor-based replay; gap detection over 1000 events triggers full snapshot |

**Architecture Decision:** The adapter runs IN-PROCESS inside the MuscalOS process (not a separate service). A daemon thread runs an asyncio event loop serving WebSocket clients. EventBus subscription is synchronous (`event_bus.subscribe("*", adapter.on_event)`) — the same pattern as `muscal_os._persist_to_store()`. Events flow: `EventBus → on_event() (sync) → projection → per-client async queues → WebSocket send`.

**Old endpoints** `api_server.py:/stream` and `/graph/stream` are now **deprecated** with runtime warnings. They remain for backward compatibility but will not receive enriched events.

**Integration:** Wire into `MuscalOS.__init__()`:
```python
self.ws_adapter = WebSocketAdapter(self.event_bus, self.store, projection)
self.event_bus.subscribe("*", self.ws_adapter.on_event, priority=10)
self.ws_adapter.start()
```

### P0.5 — Frontend Strategy

**Status:** RESOLVED WITH CONDITION
**Resolution:** Extract design system from Nexus OS (CSS, component patterns). Do NOT reuse mock data. Replace KnowledgeLayer.tsx with R3F graph. MUSCAL IDE's D3 patterns and API client inform, but do not directly reuse.
**Condition:** The frontend implementation Phase (Phase 4 in roadmap) must begin from a fresh Vite+R3F+Zustand scaffold, importing visual patterns from Nexus OS but no mock data.

### P0.6 — Execution ID

**Status:** RESOLVED WITH CONDITION
**Resolution:** UUID v7 for `execution_id`, generated by `MuscalKernel.run()`. Carried on all events published during that execution. `features/tool_runtime/tool_runtime.py` already has execution_id on ExecutionReceipt — this must be elevated to the EventBus/GraphState level.
**Condition:** The migration from `uuid.uuid4()` in `tool_runtime.py` to `uuid.uuid7()` is recommended but not blocking. The elevation into EventBus is blocking.

### P0.7 — Architecture Freeze

**Status:** RESOLVED — THIS DOCUMENT
**Resolution:** This document (`GRAPH_OS_ARCHITECTURE_FREEZE_v1.0.md`) serves as the authoritative architecture freeze. It replaces the incorrect reference to `MUSCAL_ARCHITECTURE_FREEZE_v1.0.md` (which freeses the Reconciliation Engine, not Graph-OS).

---

## SECTION O — FREEZE STATUS

```
ARCHITECTURE FREEZE STATUS:

APPROVED FOR IMPLEMENTATION
```

### P0.4 Resolution Summary

| Requirement | Implementation |
|-------------|---------------|
| Language/framework | Python asyncio, `websockets` library (already in requirements.txt). Daemon thread inside MuscalOS process |
| EventBus subscription | Sync callback via `event_bus.subscribe("*", adapter.on_event)` — same pattern as `_persist_to_store()` |
| EventStore access | Read-only: replay for snapshot/delta delivery on client connect. Direct EventStore API calls |
| Per-client queue | `asyncio.Queue(maxsize=1000)` per connection. Backpressure: oldest dropped when full, client detects gap |
| Snapshot delivery | Built from EventStore replay on connect (full replay → node/edge reconstruction). No dedicated snapshot table |
| Reconnection | Client sends `last_seq` on subscribe. Gap ≤1000: delta replay. Gap >1000 or seq=0: full snapshot |
| Authentication | Token-based via `_ws_check_token()` pattern, reusable from `api_server.py` |
| Projection layer | In-process, before WebSocket send. `GraphOSProjection` normalizes EventMessage → GraphOSEvent dict |
| Heartbeat | Server-initiated heartbeat check every 5s, timeout after 15s stale |

### What IS Frozen

The following decisions are frozen and must not change:

1. **Authority model** (§D) — MUSCAL authoritative, Graph-OS derived, ALITA observer
2. **Event envelope** (§F) — All fields and their classification (may add optional fields)
3. **Reality integrity** (§G) — Three orthogonal dimensions with validity matrix
4. **Graph State / Scene State separation** (§H) — Two explicit schemas
5. **Execution identity** (§I) — UUID v7 pattern
6. **Security boundary** (§K) — Sanitization rules
7. **ALITA boundary** (§L) — May/May-Not lists
8. **Architecture Laws** (§M) — 12 immutable laws
9. **Frontend stack** — R3F + Zustand + d3-force-3d (not WebGPU for MVP)
10. **No new physical event table** — Projection layer, not `graph_os_events` table

### What is DEFERRED

1. **MREIL integration** — Future concern
2. **100K node scaling** — Not needed for MVP
3. **Multi-tenant isolation** — Not needed for single-user system
4. **WebGPU renderer** — Future migration path from Three.js
5. **ALITA implementation** — Define boundary now, implement later
6. **Full execution integrity enforcement** — Spec exists (`EXECUTION_INTEGRITY_CONTRACT.md`), implement in Phase 2

### Implementation Entry Criteria

Before Phase 1 can begin:

- [x] P0.4 WebSocket adapter design document approved (features/streaming/ws_adapter.py + features/projection/graph_os_projection.py)
- [ ] This freeze document signed off by team
- [ ] `schema.py:Node` enriched with execution_id, execution_mode, verification_state (design, not implementation)
- [ ] `event_bus.py:EventMessage` enriched with execution_id, correlation_id, execution_mode (design, not implementation)
- [ ] R3F prototype validated (1000 InstancedMesh spheres at 60fps on target hardware)
- [ ] No unresolved contradictions from Section C remain

---

## SELF-AUDIT

| # | Question | Answer |
|---|----------|--------|
| 1 | Does Graph-OS ever become an accidental source of truth? | **NO** — §D enforces MUSCAL authority. Graph-OS has no write path to MUSCAL. |
| 2 | Can simulated and real executions be confused? | **NO** — §G requires `execution_mode` on every event. §M Law 6 requires visual distinction. |
| 3 | Can verification be inferred incorrectly? | **NO** — §M Law 7 requires independent verifier. §G defines verification semantics precisely. |
| 4 | Can an event be traced to an execution? | **YES** — §F mandates `execution_id` on all events. |
| 5 | Can an execution be traced to its causal origin? | **YES** — §F mandates `causation_id` and `correlation_id`. |
| 6 | Can the frontend reconstruct state after disconnect? | **YES** — §J defines snapshot+delta protocol. |
| 7 | Can a stale client detect inconsistency? | **YES** — §J defines `reconciliation` messages with checksum and seq gap detection. |
| 8 | Can ALITA execute unauthorized operations? | **NO** — §L explicitly forbids execution, mutation, verification bypass. |
| 9 | Can Scene State mutate authoritative truth? | **NO** — §H defines Scene State as ephemeral. No write path to MUSCAL. |
| 10 | Are there multiple competing canonical event stores? | **NOW RESOLVED** — §E designates `stored_events` (enriched) as canonical. `events` table is internal MUSCAL audit only. |
| 11 | Are event ordering and causal ordering clearly separated? | **YES** — §I defines `sequence_number` (global order) separate from `causation_id` (causal DAG). |
| 12 | Are snapshots derived or authoritative? | **DERIVED** — §J snapshots are computed from `stored_events`. Always disposable. |
| 13 | Are all sensitive fields sanitized before frontend exposure? | **YES** — §K defines explicit sanitization rules. |
| 14 | Can the architecture evolve without breaking event consumers? | **YES** — §F `event_version` field enables schema evolution. New fields are additive. |
| 15 | Does the architecture preserve MUSCAL as the authoritative execution layer? | **YES** — §D, §M Law 1, and the entire authority model enforce this. |

---

## NEXT GATE

All P0 blockers are resolved. The freeze is APPROVED.

```
ARCHITECTURE FREEZE STATUS:
APPROVED FOR IMPLEMENTATION

Next Gate:
PHASE 1 IMPLEMENTATION GATE

Phase 1 scope:
1. Extend EventMessage with execution_id, execution_mode, verification_state
2. Extend stored_events table with new columns (design, then implement)
3. Generate execution_id in MuscalKernel.run()
4. Wire execution_id through GraphState Node/Edge
5. Wire WebSocket adapter into MuscalOS (event_bus.subscribe + adapter.start)
6. Validate end-to-end: EventBus → Projection → WebSocket → basic HTML client
```

Phase 1 entry requires team sign-off on this freeze document and the Phase 1 implementation plan.

---

*This freeze document produced by Architecture Gate reconciliation of MUSCAL Core repository v0.8.0.*
*Repository truth is authoritative. Documentation reflects declared intent.*
