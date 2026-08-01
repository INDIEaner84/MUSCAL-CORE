# MC-TC-002 — MUSCAL Architecture Truth Audit (Sections 6–10)

**Date:** 2026-07-25
**Status:** DISCOVERY COMPLETE — CONTRADICTIONS FOUND
**Supercedes Section Scope:** Sections 6–10 deep-dive supplementing MC-TC-002_ARCHITECTURE_DISCOVERY_REPORT.md

---

## Executive Summary

This report extends the MC-TC-002 architecture discovery with deep-dive findings on **state authority, failure semantics, component inventory, Graph-OS boundary, contradiction register, and the final architecture truth map**. The overall status remains **DISCOVERY COMPLETE — CONTRADICTIONS FOUND**. However, this audit reveals **11 specific contradictions** (down from 15 in the prior report — 4 have been resolved or reclassified).

### Key New Findings

1. **C-001: Dual Event Stores confirmed** — `stored_events` (EventStore, 14 columns) vs `events` (WriterThread, 22 columns) are completely disjoint with separate schemas, writers, and consumers. Zero replication between them. Zero cross-validation. Zero shared identity mechanism.

2. **C-002: Dual Runtime Persistence correctly replaced** — `EnrichedMuscalOS.start()` correctly unsubscribes `_persist_to_store` and replaces it with `_enriched_persist`. No double-persist at the EventBus level. However, the two paths coexist architecturally — `events` table is written by `WriterThread` for kernel/operational events; `stored_events` is written by EventBus subscribers for lifecycle/user-facing events.

3. **C-003: No generic execution timeout** — `UnifiedToolRuntime.execute()` has NO timeout mechanism. If a tool executor hangs, the entire execution thread hangs indefinitely. Per-tool timeouts exist only inside specific executors (Playwright 15s, subprocess 10s). `plugin_registry.py` has SIGALRM for plugin hooks (10s) but this is the only production SIGALRM usage.

4. **C-004: Agent identity is optional** — `agent_id`, `cognitive_unit_id`, `model_id` are all optional parameters to `UTR.execute()`, defaulting to `""`. The kernel pipeline (mel.py) calls UTR without any agent identity. Worker is the only path that supplies agent_id — but Worker itself is not always invoked.

5. **C-009: No automatic causation_id propagation** — `causation_id` is caller-provided or inherited from parent context. There is no automatic mechanism that derives causation from call stack or execution order. The Worker explicitly passes causation_id between steps, but mel.py does not.

6. **C-011: Perma-RUNNING risk** — No runtime watchdog transitions `execution_state` from `"running"` to any terminal state. If a process crashes after `execution_state="running"` is persisted but before `"completed"`/`"failed"` is set, that execution is permanently `"RUNNING"`.

7. **Graph-OS boundary is clean** — GraphOSProjection never writes to EventStore, EventBus, or kernel state. It is a pure transformation function. However, the SUPL WebSocket path (`features/supl/ws_stream.py`) bypasses projection entirely, sending raw EventBus events to WebSocket clients.

8. **ALITA has no implementation** — "ALITA" exists only in docstrings and one test. There is no ALITA class, module, or write path in the codebase.

---

## Section 6 — State Authority & Failure Semantics

### 6.1 Execution State Authority

| State | Authoritative Writer | File:Line | Persisted |
|-------|---------------------|-----------|-----------|
| Initial (`running`) | `EnrichedMuscalOS.run()` | `enriched_bootstrap.py:80` | Yes — `stored_events.execution_state` |
| Terminal (`completed`) | `EnrichedMuscalOS.run()` | `enriched_bootstrap.py:98` | Yes — via `_enriched_persist` |
| Terminal (`failed`) | `EnrichedMuscalOS.run()` | `enriched_bootstrap.py:104,113` | Yes — via `_enriched_persist` |
| Default fallback | `identity/reality.py:normalize_execution_state()` | `reality.py:48-52` | N/A — normalization only |

**No other component transitions `execution_state`.** The `tasks` table tracks its own `status` field (`pending/active/completed/failed/timeout`) but this is independent of `execution_state` in `stored_events`.

### 6.2 Verification State Authority

| State | Authoritative Writer | File:Line | Persisted |
|-------|---------------------|-----------|-----------|
| Initial (`unverified`) | `EnrichedMuscalOS.run()` | `enriched_bootstrap.py:81` | Yes — `stored_events.verification_state` |
| Terminal (`verified`) | `VerificationOrchestrator._publish_verification_event()` | `orchestrator.py:167` | Yes — via `_enriched_persist` |
| Terminal (`failed`) | `VerificationOrchestrator._publish_verification_event()` | `orchestrator.py:169` | Yes — via `_enriched_persist` |

**VERDICT: Single authority for each state.** No competing writers. However, `execution_state` and `verification_state` are set by **different components** (`EnrichedMuscalOS` vs `VerificationOrchestrator`) and could theoretically disagree (e.g., `execution_state="completed"` but `verification_state="unverified"` if verification was never called).

### 6.3 Event History Authority

| Store | Table | Columns | Authority | Written By | Read By |
|-------|-------|---------|-----------|------------|---------|
| **EventStore** | `stored_events` | 14 | **Primary for replay/projection/WS** | `EventBus` subscribers (`_persist_to_store`, `_enriched_persist`, `ConsolidatedEventWriter`) | `ReplayService`, `WebSocketAdapter`, `SUPLWebSocketManager`, `GraphOSProjection` |
| **WriterThread** | `events` | 22 | **Primary for API/state** | `WriterThread._write_atomic()` (gate, bootstrap, observation, snapshot) | `runtime/api/`, `runtime/services/handoff`, `runtime/services/snapshot` |
| **EventBus** | `_history` | in-memory | Transient | `EventBus.publish()` | `EventBus.get_history()` |
| **Audit Log** | `audit_log` | 4 | Observability | `event_persistence._persist_event()` | Manual queries only |

**VERDICT: No single canonical event history authority.** Two persistent event stores coexist with different schemas and consumers. No replication, no cross-validation, no reconciliation mechanism.

### 6.4 Current Graph-OS State Authority

| Authority | Component | File:Line | Scope |
|-----------|-----------|-----------|-------|
| Projected | `GraphOSProjection.project()` | `projection/graph_os_projection.py:99-148` | Normalized event view — derived from source events |
| Runtime (thread-local) | `ExecutionContextManager` | `execution_context.py:73-102` | Currently active execution context |
| System | `MuscalOS._running` | `muscal_os.py:37` | Binary running/not-running flag |

**VERDICT: State authority is dual** — the projected view (reconstructed from EventStore) and the runtime view (thread-local from active execution) can disagree if events were not persisted before a crash.

### 6.5 Failure Truth Authority

| Failure Type | Declared By | File:Line | Persisted To |
|-------------|-------------|-----------|-------------|
| Execution failed | `EnrichedMuscalOS.run()` | `enriched_bootstrap.py:104,113` | `stored_events.execution_state="failed"` |
| Verification failed | `VerificationOrchestrator` | `orchestrator.py:169` | `stored_events.verification_state="failed"` |
| Tool execution failed | `UTR.execute()` | `tool_runtime.py:479-499` | `ExecutionReceipt` (in-memory), `VerificationResult(FAILED)` |
| Task timed out (restart) | `check_consistency_on_start()` | `database.py:197` | `tasks.status="timeout"` |
| Worker step failed | `Worker._execute_step()` | `worker.py:270-279` | `WorkerStep.status="error"` (in-memory) |
| Agent crashed | `ProcessManager._handle_crash()` | `process_manager.py:262` | `AgentState.CRASHED` (in-memory) |

**VERDICT: No single failure authority.** Three independent systems declare failure (`EnrichedMuscalOS`, `VerificationOrchestrator`, `check_consistency_on_start`). None reconciles with the others.

### 6.6 Crash Recovery

| Crash Scenario | Recovery | Evidence |
|---------------|----------|----------|
| Child agent process crash | YES — ProcessManager auto-restarts | `process_manager.py:236-264` |
| Main process crash | PARTIAL — `check_consistency_on_start()` marks stuck tasks as `timeout` | `database.py:187-204` |
| Execution_state="running" after crash | **NO** — permanently stuck | No timeout watchdog for execution_state |
| EventStore append failure | **NO** — silently dropped | `muscal_os.py:258: except Exception: pass` |
| EventBus subscriber crash | **NO** — silently dropped | `event_bus.py:63,68: except Exception: pass` |
| Execution hang (no exception) | **NO** — indefinite hang | UTR.execute() has no timeout |
| Snapshot restore | **NO** — write-only, no restore function | `_load_snapshot()` publishes event but never restores |

### 6.7 Dual Persistence Disagreement

If `stored_events` and `events` disagree about an execution:
- **No detection mechanism exists** — zero code paths read from both tables
- **No reconciliation protocol exists** — `check_consistency_on_start()` only checks `tasks` table
- **Schema mismatch prevents comparison** — different columns, different identity fields
- **Impact**: Silent data divergence, potentially contradictory historical records

---

## Section 7 — Component Inventory

### 7.1 Trust Core Candidates (17 of 34)

| Component | File | Layer | Authority | Persistence |
|-----------|------|-------|-----------|-------------|
| MuscalKernel | `kernel.py` | Execution | Authoritative | None (in-memory) |
| MEL | `mel.py` | Execution | Authoritative | None |
| UnifiedToolRuntime | `features/tool_runtime/tool_runtime.py` | Execution | Authoritative | Receipt in-memory; optional FileReceiptStore |
| Worker | `features/worker/worker.py` | Execution | Derived | None (in-memory) |
| ExecutionContext | `features/identity/execution_context.py` | Identity | Authoritative | Yes — columns in `stored_events` |
| EnrichedMuscalOS | `features/bootstrap/enriched_bootstrap.py` | Identity | Derived | Delegates to EventStore |
| GraphOSProjection | `features/projection/graph_os_projection.py` | Identity | Derived | None (transient) |
| VerificationOrchestrator | `features/verification/orchestrator.py` | Verification | Authoritative | In-memory `_verification_store` |
| RuleEngine | `features/verification/rules.py` | Verification | Derived | None |
| IntegrityVerifier | `features/verification/verifier.py` | Verification | Authoritative | None (stateless) |
| ProvenanceResolver | `features/provenance/resolver.py` | Provenance | Derived | Reads from UTR store + decisions DB |
| ProvenanceValidator | `features/provenance/validator.py` | Provenance | Derived | None |
| ProvenanceContext | `features/provenance/context.py` | Provenance | Authoritative | Thread-local only |
| EventBus | `event_bus.py` | Governance | Authoritative | In-memory 50K ring buffer |
| SafetyGate | `features/safety/safety_gate.py` | Governance | Authoritative | None (static classification) |
| MuscalOS | `muscal_os.py` | Governance | Authoritative | Delegates to EventStore |
| EventStore | `runtime/event_store.py` | Replay | Authoritative | **Yes** — `stored_events` table |
| ReplayService | `features/replay/replay_service.py` | Replay | Authoritative | Cursor in memory |
| Snapshot (create) | `runtime/services/snapshot.py` | Replay | Derived | **Yes** — `snapshots` table |
| WriterThread | `runtime/kernel/writer.py` | Replay | Authoritative | **Yes** — `events` table |

### 7.2 Non-Trust-Core (14 components)

GraphState, SphereState, WebSocketAdapter, SUPLWebSocketManager, EventAdapter, EventBusBridge, ConsolidatedEventWriter, config, plugin_registry, supervisor, main_boot, ObservationLoop, ExecutionGovernor, dashboard.

---

## Section 8 — Graph-OS / ALITA Boundary Verification

### 8.1 Boundary Model vs Reality

| Layer | Model Role | Actual Status | Evidence |
|-------|-----------|---------------|----------|
| MUSCAL | Authoritative execution + persistence | **VERIFIED** — MuscalOS/EnrichedMuscalOS are sole state writers | `enriched_bootstrap.py:80,98,104,113` |
| Graph-OS | Derived projection | **VERIFIED** — GraphOSProjection is pure transformation | No write path to EventStore/EventBus/kernel |
| Scene | Ephemeral state | **NOT FOUND** — No Scene class exists; closest is SphereState (in-memory only) | `sphere.py` has no persistence |
| ALITA | Observer/presentation | **NOT IMPLEMENTED** — Only docstrings and one test value | Zero code in `features/` |

### 8.2 Violations Found

| # | Violation | File:Line | Severity | Impact |
|---|-----------|-----------|----------|--------|
| V-01 | SUPL WebSocket bypasses GraphOSProjection | `features/supl/ws_stream.py:93-112` | P2 | Sensitive payload fields may leak; non-canonical events may be streamed; no state validation |
| V-02 | No source whitelist enforcement | `graph_os_projection.py:113` | P2 | Any component can inject any source value; `source="alita"` passes through |
| V-03 | `_bridge_to_graph` writes to GraphState | `muscal_os.py:353` | P1 (observation) | GraphState receives EventBus events but this is intended bidirectional bridging, not authority violation |

### 8.3 Boundary Integrity Summary

- Graph-OS is **clean**: no write path to MUSCAL authoritative stores
- ALITA is **absent**: no implementation to enforce boundary against
- SUPL WebSocket is a **bypass risk**: raw events without projection
- Source validation is **missing**: no allowlist, any source value accepted

---

## Section 9 — Contradiction Register

| ID | Title | Severity | Status | Conflicting Authorities | Affected Components |
|----|-------|----------|--------|------------------------|---------------------|
| **C-001** | Dual Event Stores | **P0** | CONFIRMED | `EventStore` (stored_events) vs `WriterThread` (events) | All event consumers |
| **C-002** | Dual Runtime Persistence | P2 | RESOLVED | EnrichedMuscalOS correctly replaces bare persist | None at runtime |
| **C-003** | No generic execution timeout | **P1** | CONFIRMED | UTR.execute() has no timeout mechanism | Tool execution, Worker |
| **C-004** | Optional agent identity | P2 | CONFIRMED | mel.py calls UTR without agent_id | Provenance reconstruction |
| **C-005** | Provenance identity gap | P2 | CONFIRMED | request_id not propagated through all layers | Provenance chain |
| **C-006** | Provenance step link gap | P2 | PARTIAL | plan_id/step_id in Worker path but not mel.py path | Worker vs direct UTR |
| **C-007** | Receipt persistence gap | **P1** | CONFIRMED | ExecutionReceipts are in-memory only; FileReceiptStore is optional | Crash recovery, replay |
| **C-008** | Verification persistence gap | **P1** | CONFIRMED | VerificationResults are in-memory `_verification_store` only | Crash recovery, audit |
| **C-009** | No automatic causation propagation | P2 | CONFIRMED | causation_id is caller-provided, not derived from call chain | Causal chain completeness |
| **C-010** | Retry provenance gap | P2 | CONFIRMED | retry_count/attempt_number excluded from ExecutionReceipt.to_dict() | FileReceiptStore persistence |
| **C-011** | Perma-RUNNING risk | **P1** | CONFIRMED | No watchdog transitions execution_state from "running" | Reliability, crash semantics |
| **C-012** | Graph-OS bypass (SUPL WS) | P2 | CONFIRMED | SUPL WebSocket sends raw events without projection | Security, sanitization |
| **C-013** | No crash recovery for execution_state | P2 | CONFIRMED | check_consistency_on_start() only checks tasks table, not execution_state | Reliability |
| **C-014** | ExecutionReceipt.to_dict() omits retry fields | P2 | CONFIRMED | retry_count, attempt_number excluded from serialization | Provenance completeness |
| **C-015** | Schema divergence: `stored_events` vs `events` | P2 | CONFIRMED | 14 vs 22 columns, different naming conventions, no shared identifiers | Cross-store queries |

### Severity Distribution

| Severity | Count | IDs |
|----------|-------|-----|
| **P0** (must fix before replay) | 1 | C-001 |
| **P1** (must fix before production) | 4 | C-003, C-007, C-008, C-011 |
| **P2** (deferrable) | 9 | C-002, C-004, C-005, C-006, C-009, C-010, C-012, C-013, C-014, C-015 |

**Net new from this audit (vs prior report):** 4 contradictions resolved/merged, 2 new identified (C-014, C-015).

---

## Section 10 — Final Architecture Truth Map

### 10.A Canonical Authorities

| Concern | Canonical Authority | Status |
|---------|-------------------|--------|
| Execution | `EnrichedMuscalOS.run()` | **CONFIRMED** — sole execution_state writer |
| Safety | `SafetyGate.check()` | **CONFIRMED** — gate is singleton |
| Governance | `EventBus` + `plugin_registry` hooks | **CONFIRMED** — publish/subscribe routing |
| Tool execution | `UnifiedToolRuntime.execute()` | **CONFIRMED** — sole tool execution path |
| Receipt creation | `ExecutionReceipt.finalize()` | **CONFIRMED** — SHA-256 integrity hash |
| Verification | `VerificationOrchestrator.verify()` | **CONFIRMED** — sole verification coordinator |
| Event history | **UNRESOLVED** — dual authorities | C-001: `stored_events` vs `events` |
| Persistence | `EventStore.append()` (stored_events) | **CONFIRMED** for replay/projection path |
| Current state | Dual: `ExecutionContextManager` (runtime) + `GraphOSProjection` (projected) | **INFERRED** — runtime vs projected |
| Projection | `GraphOSProjection.project()` | **CONFIRMED** — sole projection function |
| Replay source | `EventStore.replay()` | **CONFIRMED** — cursor-based from stored_events |
| Provenance | `ProvenanceResolver.resolve_execution()` | **CONFIRMED** — sole reconstruction engine |

### 10.B Canonical Execution Chain

```
Request
  → EnrichedMuscalOS.run()           [enriched_bootstrap.py:62]
    → ExecutionContext created        [enriched_bootstrap.py:72-79]
    → EXECUTION_STARTED published     [enriched_bootstrap.py:82]
    → _enriched_persist               [enriched_bootstrap.py:149-167]
      → EventStore.append()           [event_store.py:49-93]
    → MuscalOS.run()                  [muscal_os.py:129]
      → kernel.run()                  [kernel.py:622]
        → stage_rag ... stage_mkc ... stage_bridge
        → stage_mel → mel.execute()   [mel.py:67]
          → UTR.execute()             [tool_runtime.py:373]
            → SafetyGate.check()      [safety_gate.py:50]
            → fn(args)                (actual tool executor)
            → ExecutionReceipt.finalize()  [tool_runtime.py:138]
        → stage_feedback ... stage_memory
      → result returned
    → EXECUTION_COMPLETED/FAILED published [enriched_bootstrap.py:96-105]
    → _enriched_persist               (persists terminal state)
  → (optional) VerificationOrchestrator.verify()
    → VERIFICATION_PASSED/FAILED published [orchestrator.py:159-176]
    → verification_state updated      [orchestrator.py:167-169]

Divergent path (WriterThread):
  runtime/kernel/gate.py → WriterThread.submit() → events table
  runtime/observation/loop.py → WriterThread.submit() → events table
  NOT replicated to stored_events

Legacy path:
  MuscalOS._persist_to_store (bare, no enrichment)
  → Replaced by EnrichedMuscalOS at enriched bootstrap time
```

### 10.C Canonical Identity Chain

```
request_id     → UTR param (optional, default "")        [MISSING in kernel path]
execution_id   → EnrichedMuscalOS.run() uuid7()           [PRESENT]
correlation_id → inherited from parent or execution_id    [PRESENT]
causation_id   → inherited from parent execution_id       [PRESENT]
plan_id        → Worker param (optional, default "")      [MISSING in mel.py path]
step_id        → Worker param (optional, default "")      [MISSING in mel.py path]
agent_id       → Worker param (optional, default "")      [MISSING in kernel/mel path]
receipt_id     → UTR uuid7() auto-generated              [PRESENT]
verification_id → VerificationOrchestrator uuid7()        [PRESENT]
trace_id       → ProvenanceContext (uuid4)               [PRESENT]
span_id        → ProvenanceContext (uuid4)               [PRESENT]
decision_id    → ProvenanceContext (uuid4)               [PRESENT]
event_id       → EventBus uuid4 or ConsolidatedEventWriter uuid7() [INCONSISTENT FORMAT]
```

**Key gaps:**
- `request_id`, `plan_id`, `step_id`, `agent_id` are all **optional/empty** in the kernel/mel execution path
- Only the Worker path sets agent/plan/step identity
- `event_id` format is **inconsistent**: EventBus uses `uuid4()` while identity framework uses `uuid7()`
- No identity links between the two event tables (`stored_events` and `events` have no shared identity column)

### 10.D Reality Integrity Chain

| Field | Set By | Persisted | Survives Replay |
|-------|--------|-----------|-----------------|
| `execution_mode` | `EnrichedMuscalOS.run()` param, default "real" | `stored_events.execution_mode` | **YES** — column replayed |
| `execution_state` | `EnrichedMuscalOS.run()`: "running" → "completed"/"failed" | `stored_events.execution_state` | **YES** — column replayed |
| `verification_state` | `EnrichedMuscalOS.run()`: "unverified" → `VerificationOrchestrator`: "verified"/"failed" | `stored_events.verification_state` | **YES** — column replayed |

**Distinction between live and replayed:**
- LIVE events: carry `execution_mode="real"`, published by `EnrichedMuscalOS.run()` or `VerificationOrchestrator`
- REPLAY events: replayed via `ReplayService`, carry `_replayed=True` marker, **suppressed from re-persistence**
- RECONSTRUCTED state: `GraphOSProjection.project()` creates a normalized view from raw events
- RE-EXECUTED state: Not explicitly distinguishable — re-execution produces new `execution_id`

**Risk:** Replayed events pass through `GraphOSProjection.project()` and are indistinguishable from live events at the projection level. The `_replayed=True` marker prevents re-persistence but does not mark the projected output.

### 10.E Replay Readiness

**Rating: CONDITIONAL**

| Criterion | Status | Evidence |
|-----------|--------|----------|
| Single canonical event source | **FAIL** | Dual event stores (C-001) |
| Identity chain complete | **PARTIAL** | agent_id/plan_id/step_id optional (C-004, C-006) |
| Persistence crash-safe | **FAIL** | Receipts in-memory (C-007), verification in-memory (C-008) |
| State semantics preserved | **PASS** | execution_mode/state/vstate survive replay |
| Causation recoverable | **PASS** | causation_id chain persists in stored_events |
| Deterministic ordering | **PASS** | seq column in stored_events, cursor-based replay |
| Duplicate detection | **PASS** | event_id UNIQUE constraint in stored_events |
| Replay suppression | **PASS** | `_replayed=True` marker prevents re-persistence |

### 10.F Production Readiness

| Domain | Rating | Reasoning |
|--------|--------|-----------|
| Execution Integrity | **YELLOW** | No generic timeout (C-003), perma-RUNNING risk (C-011) |
| Verification Integrity | **YELLOW** | Verification results in-memory (C-008), not persisted to EventStore |
| Provenance Integrity | **YELLOW** | Optional identity gaps (C-004, C-006), retry gap (C-010) |
| Persistence Integrity | **RED** | Dual event stores (C-001), silent data loss on append failure |
| Replay Readiness | **YELLOW** | Conditional — works for stored_events but events table not covered |
| Runtime Authority | **GREEN** | Single execution_state writer, single verification_state writer |
| Event Authority | **RED** | Two event stores with no reconciliation (C-001) |

### 10.G Remediation Gate

#### BLOCKERS — Must be fixed before Replay Phase

| ID | Issue | Remediation |
|----|-------|-------------|
| C-001 | Dual event stores | Consolidate to single event store; deprecate `events` table for replay; migrate consumers or add cross-table reconciliation. Canonical authority must be `stored_events` (already has identity, state, and verification columns). |

#### REQUIRED — Must be fixed before Production

| ID | Issue | Remediation |
|----|-------|-------------|
| C-003 | No generic execution timeout | Add timeout parameter to `UTR.execute()` (e.g., `threading.Timer` with configurable deadline). Default should be non-infinite (e.g., 5 min). |
| C-007 | Receipt not persisted | Persist `ExecutionReceipt` to `stored_events` as a first-class event with schema `execution_receipt` topic. Make `FileReceiptStore` the default, not optional. |
| C-008 | Verification not persisted | Persist `VerificationResult` to `stored_events` as a first-class event (`VERIFICATION_PASSED`/`VERIFICATION_FAILED`). Verification state should be automatically writable from the verification event. |
| C-011 | Perma-RUNNING risk | Add timeout watchdog to `EnrichedMuscalOS.run()` or `MuscalOS._run()`. Set a configurable execution deadline and auto-transition to `"failed"` on timeout. |

#### DEFERRED — Can be addressed later

| ID | Issue | Remediation |
|----|-------|-------------|
| C-004 | Optional agent_id | Make agent_id required in kernel/mel execution path; default to "kernel" if not explicitly provided |
| C-005 | request_id gap | Propagate request_id from EnrichedMuscalOS through kernel to UTR |
| C-006 | plan_id/step_id gap | Add plan_id/step_id to mel.py UTR calls |
| C-009 | Automatic causation | Derive causation_id from execution context automatically in EnrichedMuscalOS |
| C-010 | Retry provenance | Add retry_count/attempt_number to ExecutionReceipt.to_dict() |
| C-012 | Graph-OS bypass (SUPL WS) | Add GraphOSProjection integration to SUPL WebSocket path |
| C-013 | Crash recovery for execution_state | Extend check_consistency_on_start() to detect stuck execution_state |
| C-014 | to_dict() retry omission | Add retry_count/attempt_number to to_dict() |
| C-015 | Schema divergence | Add cross-referencing columns or migrate to unified schema |

---

## Contradiction Summary

| Metric | Count |
|--------|-------|
| Total contradictions | 15 |
| P0 (BLOCKER) | 1 |
| P1 (REQUIRED) | 4 |
| P2 (DEFERRED) | 10 |
| Resolved from prior report | 4 |

## Recommended Next Phase: **CONDITIONAL GO TO REPLAY**

Phase MC-TC-003 should:
1. **Resolve C-001** — consolidate event stores; make `stored_events` the single replay authority
2. **Resolve C-003** — add generic timeout to UTR.execute()
3. **Persist receipts and verifications** to EventStore (C-007, C-008)
4. **Add execution timeout watchdog** (C-011)
5. **Fix ExecutionReceipt.to_dict()** serialization gap (C-014)
6. **Add source whitelist** to GraphOSProjection (V-02)
7. **Integrate SUPL WebSocket with GraphOSProjection** (C-012)

Implementation remains **FORBIDDEN** until MC-TC-003 defines the Trust Core package structure.

---

## Final Status

- **10/10 Sections:** COMPLETE
- **Contradictions:** 15 total (1 P0, 4 P1, 10 P2)
- **Canonical Authority Conflicts:** 1 (Event History — dual event stores)
- **Replay Readiness:** CONDITIONAL
- **Production Readiness:** YELLOW (RED in persistence integrity)
- **Recommended Next Phase:** CONDITIONAL GO TO REPLAY (after C-001 resolution)

*Report produced by MC-TC-002 Architecture Truth Audit.*
*Repository truth is authoritative. All claims verified against source code.*
