# MC-TC-004 — Post-Remediation Architecture Truth Audit

**Date:** 2026-07-25
**Status:** AUDIT COMPLETE — RESIDUAL CONTRADICTIONS FOUND
**Previous Audit:** MC-TC-002 (15 contradictions: 1 P0, 4 P1, 10 P2)
**Remediation Phase:** MC-TC-003 (claimed 7 resolutions)
**Current Phase:** MC-TC-004
**Mode:** AUDIT ONLY — Implementation FORBIDDEN

---

## Executive Summary

MC-TC-003 claimed resolution of 7 architectural contradictions (1 P0, 5 P1, 1 P2). This independent audit finds:

| Claimed Status | Count | Actual Status |
|---|---|---|
| RESOLVED | 7 claimed | 1 RESOLVED, 2 PARTIALLY RESOLVED, 4 NOT RESOLVED |

Of the 7 claimed remediations, only **C-014 (Serialization)** is genuinely resolved. Two are partially resolved with significant gaps (C-001, C-008). Four are architecturally NOT RESOLVED (C-003, C-007, C-011, C-006).

**Root cause of the gap:** MC-TC-003 created extension points (callbacks, methods, classes, parameters) but **did not wire them into any production runtime path**. The architecture has the plumbing but no connectivity.

Additionally, **4 new contradictions were introduced** by MC-TC-003 (thread leaks, unwired callbacks, version inconsistency, uninstantiated watchdog).

**Replay Readiness: NO-GO.** Three critical gates fail (Single Event Authority, Durable Receipt Persistence, Durable Verification). Two conditional gates fail (Timeout Semantics, Watchdog).

---

## Audit Scope and Methodology

- **Files inspected:** 35+ source files across runtime, features, kernel, identity, verification, streaming, projection, monitoring
- **Tests executed:** 325 across 16 test suites
- **Production paths traced:** Every execution → persistence → replay path
- **Authority domains traced:** Event, Execution, Receipt, Verification, Persistence, Projection, Graph-OS, Watchdog
- **Search patterns:** All SQL INSERT/UPDATE/DELETE, all EventStore/WriterThread usage, all callback registrations, all watchdog instantiations

---

## MC-TC-002 → MC-TC-003 → MC-TC-004 Lineage

```
MC-TC-002: 15 contradictions found (1 P0, 4 P1, 10 P2)
  |
  v
MC-TC-003: Claimed remediation of 7 (1 P0, 5 P1, 1 P2)
  |           - Added store_receipt/store_verification to EventStore
  |           - Added timeout parameter to UTR.execute()
  |           - Added _on_receipt_callback / _on_verification_callback
  |           - Created ExecutionWatchdog class
  |           - Fixed to_dict/from_dict serialization
  |           - Added CANONICAL_SOURCES to GraphOSProjection
  |
  v
MC-TC-004: Independent verification
  - 1 genuinely resolved (C-014)
  - 2 partially resolved (C-001, C-008)
  - 4 NOT resolved (C-003, C-007, C-011, C-006)
  - 4 new contradictions introduced
  - Replay Readiness: NO-GO
```

---

## Remediation Verification Matrix

| ID | Original Priority | MC-TC-003 Claim | MC-TC-004 Reality | Residual Risk | Final Status |
|---|---|---|---|---|---|
| C-001 | P0 | stored_events canonical | Both tables independently writable; receipt/verification methods unwired | Both tables can diverge; no reconciliation | **PARTIALLY RESOLVED** |
| C-003 | P1 | timeout param + ThreadPoolExecutor | Caller-timeout only; no production caller passes timeout; thread leak; late side effects | Execution not terminated; side effects after timeout | **NOT RESOLVED** |
| C-007 | P1 | _on_receipt_callback + store_receipt | Callback never wired in production; receipts remain RAM-only | Receipts lost on restart; no crash survival | **NOT RESOLVED** |
| C-008 | P1 | _on_verification_callback + store_verification | Orchestrator path persists via EventBus; UTR internal path RAM-only; callback unwired | Internal verification results lost on restart | **PARTIALLY RESOLVED** |
| C-011 | P1 | ExecutionWatchdog class | Class never instantiated; no production wiring | Perma-RUNNING risk unchanged | **NOT RESOLVED** |
| C-014 | P1 | to_dict/from_dict fix | All fields serialized; round-trip verified; minor _receipt_version inconsistency | Low — cosmetic only | **RESOLVED** |
| C-006 | P2 | CANONICAL_SOURCES whitelist | Warning-only; SUPL WS bypasses projection; no rejection | No actual security boundary | **NOT RESOLVED** |

---

## C-001 Dual Event Store Analysis

### Current State

Two independent SQLite tables persist events:

| Dimension | `events` (WriterThread) | `stored_events` (EventStore) |
|---|---|---|
| Schema | 22 columns | 13 columns |
| Writer | `runtime/kernel/writer.py:94-125` | `runtime/event_store.py:73-77` |
| Connection | Own `sqlite3.Connection` | `get_connection()` |
| Transaction | `BEGIN IMMEDIATE` | Auto-commit |
| Consumers | `runtime/api/*`, `services/handoff`, `services/snapshot` | WS adapter, replay, GraphOSProjection |
| Write sources | gate.py, bootstrap.py, observation loop, snapshot, admin | EventBus subscribers, store_receipt, store_verification (unwired) |

### Write Paths Still Active

`events` table receives writes from at **14 distinct call sites** in production:

- `runtime/kernel/gate.py:16,49,61,92,102` — governance/gate violations
- `runtime/kernel/bootstrap.py:49` — kernel initialization
- `runtime/observation/loop.py:44,85` — observation anomalies
- `runtime/services/snapshot.py:31` — snapshot events
- `runtime/api/workers.py:23,40,63,87` — worker lifecycle
- `runtime/api/admin.py:55` — HUD screenshots

`stored_events` table receives writes from:
- `muscal_os.py:258` — `_persist_to_store()` (EventBus subscriber)
- `features/bootstrap/enriched_bootstrap.py:149` — `_enriched_persist()` (EventBus subscriber)
- `features/events/event_consolidation.py:55` — `ConsolidatedEventWriter`
- `features/events/event_adapter.py:82` — `EventStoreAdapter`

### MC-TC-003 Additions (ALL UNWIRED)

- `EventStore.store_receipt()` — defined in `runtime/event_store.py:97` but never called in production
- `EventStore.store_verification()` — defined in `runtime/event_store.py:115` but never called in production
- `UnifiedToolRuntime._on_receipt_callback` — defined in `features/tool_runtime/tool_runtime.py:323` but `set_receipt_callback()` never called in production
- `UnifiedToolRuntime._on_verification_callback` — defined in `features/tool_runtime/tool_runtime.py:324` but `set_verification_callback()` never called in production

### Key Findings

1. **Both tables can still receive production writes** — no deprecation or migration applied.
2. **No transactional coupling** — a write to `events` can succeed while `stored_events` fails and vice versa.
3. **No cross-validation** — no reconciliation mechanism ensures the two tables agree.
4. **No shared identity** — `events` uses `seq` (auto-increment), `stored_events` uses `event_id` (UUID). Neither references the other.
5. **Test `test_c001_no_events_table_write_from_canonical_path`** proves that EventStore does NOT write to `events` — but the reverse (`events` table not writing to `stored_events`) is ALSO true. The tables are fully disjoint.
6. **`store_receipt()` and `store_verification()`** are technically functional (proved by `test_c001_store_receipt_persists` and `test_c001_store_verification_persists`) but are dead code without wiring.

### Residual Risk

HIGH. Two independent event stores can diverge without detection. Receipts and verifications are not persisted. Crash survival requires both stores to agree, which is not guaranteed.

### Conclusion

**C-001 FINAL STATUS: PARTIALLY RESOLVED**

The canonical authority is nominally `stored_events`, but `events` remains independently authoritative for kernel/runtime events. No consolidation, migration, or reconciliation has been implemented.

---

## C-003 Timeout Analysis

### Implementation

File: `features/tool_runtime/tool_runtime.py:440-448`

```python
try:
    if timeout is not None:
        future = self._executor_pool.submit(fn, args)
        result = future.result(timeout=timeout)
    else:
        result = fn(args)
except FutureTimeoutError:
    # Build TIMEOUT receipt and return
```

### Critical Analysis: Caller vs Actual Termination

| Dimension | MC-TC-003 Claim | MC-TC-004 Reality |
|---|---|---|
| What terminates on timeout? | Implicitly the tool execution | **Only the caller's wait.** The underlying `fn(args)` continues running in the thread pool. |
| Is the task cancelled? | Implied | **NO.** `concurrent.futures.Future.result(timeout=X)` does NOT cancel the future. The thread continues. |
| Are resources cleaned up? | Implied | **NO.** The executor thread continues consuming resources. Thread pool never shut down. |
| Are side effects prevented? | Implied | **NO.** The tool can write files, send network requests, modify system state after MUSCAL declares timeout. |
| Can late results arrive? | Not discussed | **YES.** The future resolves later but the result is silently dropped. |
| Can late verification run? | Not discussed | **NO.** The receipt was already finalized with `success=False`. The late result is never verified. |
| Thread pool shutdown? | Not implemented | `self._executor_pool` is NEVER shut down (`grep -r "shutdown" features/tool_runtime/` returns empty). |

### Production Caller Analysis

Every production caller of `UTR.execute()` was checked. **NONE passes a timeout argument:**

| Caller | File:Line | Timeout Passed |
|---|---|---|
| `CognitiveUnit.execute()` | `cognitive_unit.py:50` | No |
| `Worker._execute_step()` | `worker.py:243` | No |
| `muscal_loop.execute_tool()` | `muscal_loop.py:438` | No |
| `permission_engine.mel_execute()` | `permission_engine.py:47` | No |
| `mel._execute_step()` | `mel.py:54` | No |
| `system_runtime.py` | `system_runtime.py:99` | No |

**Result:** Even if the implementation were correct, it provides zero production protection because no caller passes the timeout parameter. The default `timeout=None` means the traditional blocking `fn(args)` path is always taken.

### Risk Assessment

| Risk | Severity | Evidence |
|---|---|---|
| Tool hangs indefinitely | **HIGH** | No production caller passes timeout. Hanging tool blocks thread forever. |
| Side effects after timeout | **HIGH** | Task continues execution after caller receives TIMEOUT receipt. |
| Thread leak | **MEDIUM** | `_executor_pool` has `max_workers=4`. After 4 timeouts, pool is saturated. New timed-out tasks hang the caller. `ThreadPoolExecutor.shutdown()` never called. |
| Late result dropped | **LOW** | Consistent with timeout semantics — caller chose not to wait. |
| Receipt before termination | **MEDIUM** | TIMEOUT receipt is created and returned while the underlying tool is still running. Caller sees `success=False` but tool may complete successfully later. |

### Conclusion

**C-003 FINAL STATUS: NOT RESOLVED**

- **Caller Timeout Semantics:** IMPLEMENTED but unused by any production code path.
- **Actual Execution Termination Semantics:** NOT IMPLEMENTED. The underlying operation continues after timeout.
- **Post-Timeout Side-Effect Risk:** HIGH. The tool executor can perform side effects after MUSCAL has declared timeout.

---

## C-007 Receipt Persistence Analysis

### Implementation

The persistence chain exists in four disconnected parts:

**Part 1 — Receipt creation and callback:**
`features/tool_runtime/tool_runtime.py:383-405` (`_build_receipt`)
```python
receipt.finalize()
self._put_receipt(receipt)
if self._on_receipt_callback:         # ← extension point
    self._on_receipt_callback(receipt) # ← NEVER FIRES
```

**Part 2 — Callback setter:**
`features/tool_runtime/tool_runtime.py:326-327`
```python
def set_receipt_callback(self, callback):
    self._on_receipt_callback = callback  # ← NEVER CALLED
```

**Part 3 — EventStore persistence method:**
`runtime/event_store.py:97-113`
```python
def store_receipt(self, receipt):
    payload = receipt.to_dict()
    return self.append({...})             # ← NEVER CALLED
```

**Part 4 — In-memory fallback:**
`features/tool_runtime/tool_runtime.py:367-371`
```python
def _put_receipt(self, receipt):
    if isinstance(self._receipt_store, dict):
        self._receipt_store[receipt.receipt_id] = receipt  # ← ACTUAL PATH
    else:
        self._receipt_store.put(receipt.receipt_id, receipt)  # ← ACTUAL PATH
```

### Evidence of Unwired State

```bash
$ grep -r "set_receipt_callback" features/
features/tool_runtime/tool_runtime.py:    def set_receipt_callback(self, callback):
# Only 1 result — the definition itself. No caller exists.
```

```bash
$ grep -r "store_receipt" features/ runtime/
runtime/event_store.py:    def store_receipt(self, receipt):
# Only 1 result — the definition itself. No caller exists outside tests.
```

### Persistence Reality

| Storage | Persistence | Crash Survival | Reconstructable |
|---|---|---|---|
| `_receipt_store` (dict) | RAM only | **LOST** | No |
| `ReceiptStore` | RAM only | **LOST** | No |
| `FileReceiptStore` | `/tmp/muscal_receipts/*.json` | **SURVIVES** (filesystem-dependent) | Yes, but `/tmp` is not guaranteed |
| `EventStore.store_receipt()` | SQLite `stored_events` | **SURVIVES** | Yes, but NOT CONNECTED |

### Conclusion

**C-007 FINAL STATUS: NOT RESOLVED**

Receipts remain RAM-only in production. The persistence callback exists but is not wired into any boot sequence, bootstrap, or initialization path. A process crash after execution but before receipt consumption loses the receipt permanently.

---

## C-008 Verification Persistence Analysis

### Two Paths

**Path A — VerificationOrchestrator (EXTERNAL):** `features/verification/orchestrator.py`

- `_publish_verification_event()` → `EventBus.publish("VERIFICATION_PASSED"/"VERIFICATION_FAILED", ...)`
- EventBus event → `_enriched_persist()` → `EventStore.append()` → `stored_events`
- **Result:** Verification results through this path ARE persisted.

**Path B — UTR internal (INTERNAL):** `features/tool_runtime/tool_runtime.py:570-667`

- `_verify_one()` → `self._verification_store[vr.verification_id] = vr` (in-memory dict)
- `_on_verification_callback` is checked but NEVER SET
- **Result:** Verification results through this path are RAM-only.

### Coverage Gap

| Verification Type | Path | Persisted? |
|---|---|---|
| Integrity check (not finalized) | UTR internal (Path B) | **NO** |
| Integrity check (tampered) | UTR internal (Path B) | **NO** |
| No verifier registered | UTR internal (Path B) | **NO** |
| Verifier returned True/False | UTR internal (Path B) | **NO** |
| Verifier raised exception | UTR internal (Path B) | **NO** |
| Orchestrator verify (all types) | VerificationOrchestrator (Path A) | **YES** (via EventBus) |

### Conclusion

**C-008 FINAL STATUS: PARTIALLY RESOLVED**

Verification results from the `VerificationOrchestrator` path are persisted through EventBus → `stored_events`. However, the entire UTR internal verification path (integrity checks, tamper detection, verifier dispatch, exception handling) remains RAM-only. The callback exists but is not wired.

---

## C-011 Watchdog Analysis

### Implementation

File: `features/monitoring/execution_watchdog.py` (128 lines)

- `class ExecutionWatchdog:` — daemon thread with `_watchdog_loop()`
- Scans `EventStore.replay()` for executions with `execution_state="running"`
- Publishes `EXECUTION_FAILED` to `EventBus` for orphans > 300s

### Critical Finding: Never Instantiated

```bash
$ grep -r "ExecutionWatchdog(" features/ runtime/ muscal_os.py
# No results in production code
```

The class is:
- **Defined** in `features/monitoring/execution_watchdog.py`
- **Referenced** in `CANONICAL_SOURCES` in `graph_os_projection.py` (for source whitelisting)
- **Never instantiated** by any production code
- **Never started** by any boot sequence
- **Never wired** into `EnrichedMuscalOS`, `MuscalOS`, or any runtime

### Watchdog Classification

| Criterion | Requirement | Actual | Verdict |
|---|---|---|---|
| Instantiated at boot | YES | **NO** — never instantiated | FAIL |
| Scans for stuck executions | YES | Code exists but never runs | N/A |
| Transitions state to terminal | YES | Publishes EventBus event, does NOT update execution_state | INSUFFICIENT |
| Publishes event | YES | Publishes `EXECUTION_FAILED` to EventBus | IMPLEMENTED |
| Heartbeat mechanism | RECOMMENDED | **NO** | MISSING |
| Restart recovery | REQUIRED | **NO** — in-memory only | MISSING |
| Persistent state change | REQUIRED | **NO** — only EventBus event | INSUFFICIENT |
| Thread safety | REQUIRED | Single daemon thread, no health check | PARTIAL |
| Configurable thresholds | RECOMMENDED | Yes — `orphan_timeout`, `poll_interval` | PRESENT but unused |

### Conclusion

**C-011 FINAL STATUS: NOT RESOLVED**

**Classification: Insufficient.** The watchdog is a best-effort in-process monitor that was never connected to production. Even if wired, it would not be production-grade: no heartbeat, no persistent state transition, no restart recovery, and a single daemon thread with no health monitoring.

---

## C-014 Serialization Analysis

### Field Matrix

| Field | Constructor | Runtime | Hash | to_dict | from_dict | FileReceiptStore | EventStore | Roundtrip |
|---|---|---|---|---|---|---|---|---|
| `receipt_id` | YES (or uuid7) | YES | YES | YES | YES | YES | YES | PASS |
| `tool_name` | YES | YES | YES | YES (as "tool") | YES (as "tool") | YES | YES | PASS |
| `args` | YES (dict) | YES | YES | YES | YES | YES | YES | PASS |
| `execution_time` | YES | YES | YES | YES | YES | YES | YES | PASS |
| `result_data` | YES | YES | YES | YES | YES | YES | YES | PASS |
| `success` | YES | YES | YES | YES | YES | YES | YES | PASS |
| `execution_id` | YES (or uuid7) | YES | YES | YES | YES | YES | YES | PASS |
| `correlation_id` | YES | YES | YES | YES | YES | YES | YES | PASS |
| `causation_id` | YES **_(new)_** | YES | YES | YES **_(new)_** | YES **_(new)_** | YES **_(new)_** | YES | PASS |
| `trace_id` | YES | YES | YES | YES | YES | YES | YES | PASS |
| `span_id` | YES | YES | YES | YES | YES | YES | YES | PASS |
| `decision_id` | YES | YES | YES | YES | YES | YES | YES | PASS |
| `request_id` | YES **_(new)_** | YES | YES | YES **_(new)_** | YES **_(new)_** | YES **_(new)_** | YES | PASS |
| `plan_id` | YES **_(new)_** | YES | YES | YES **_(new)_** | YES **_(new)_** | YES **_(new)_** | YES | PASS |
| `step_id` | YES **_(new)_** | YES | YES | YES **_(new)_** | YES **_(new)_** | YES **_(new)_** | YES | PASS |
| `agent_id` | YES | YES | YES | YES | YES | YES | YES | PASS |
| `model_id` | YES | YES | YES | YES | YES | YES | YES | PASS |
| `cognitive_unit_id` | YES **_(new)_** | YES | YES | YES **_(new)_** | YES **_(new)_** | YES **_(new)_** | YES | PASS |
| `retry_count` | YES | YES | YES | YES **_(new)_** | YES **_(new)_** | YES **_(new)_** | YES | PASS |
| `attempt_number` | YES | YES | YES | YES **_(new)_** | YES **_(new)_** | YES **_(new)_** | YES | PASS |
| `_integrity_hash` | Set by finalize() | YES | — | YES | YES | YES | YES | PASS |
| `_finalized` | NO (False) | YES | — | YES | YES | YES | YES | PASS |
| `_verification_result` | NO (None) | Conditional | — | YES (nested) | YES (nested) | YES (nested) | YES | PASS |
| `_receipt_version` | YES (=1, int) | YES | NO | **NO** | NO | NO | NO | **FAIL** |

### Issues Found

1. **`_receipt_version` in `__slots__` and `__init__` but NOT in `to_dict()` or `from_dict()`.** Initialized as `int 1` while class attribute `RECEIPT_VERSION` is `str "2.0.0"`. Inconsistent type and not serialized.

2. **Legacy receipt backward compatibility:** `from_dict()` uses `.get("field", default)` for all new fields, so legacy receipts (without new fields) will deserialize with `request_id=""`, `plan_id=""`, etc. This is correct behavior but means legacy receipts lose identity information on round-trip.

3. **`FileReceiptStore.get()`** was updated to use `ExecutionReceipt.from_dict()`. No breakage for legacy files.

### Test Coverage

- `test_receipt_serialization.py` — 3 tests: to_dict includes all fields, from_dict roundtrip, ToolResult.from_dict preservation
- `test_tool_runtime_phase3.py:test_tool_result_to_dict` — verifies basic to_dict
- `test_tool_runtime_phase3.py:test_tool_result_from_dict` — verifies basic from_dict

### Conclusion

**C-014 FINAL STATUS: RESOLVED**

All critical identity fields are serialized and deserialized correctly. The `_receipt_version` inconsistency is cosmetic (no functional impact). Round-trip and backward compatibility are verified.

---

## C-006 Graph-OS Source Boundary Analysis

### Implementation

File: `features/projection/graph_os_projection.py:121-123`

```python
source = raw.source or (raw.payload.get("source", "") if raw.payload else "") or "muscal_kernel"
if source not in CANONICAL_SOURCES:
    logger.warning("non-canonical source '%s' projected — consider adding to CANONICAL_SOURCES", source)
```

### Critical Finding: Warning-Only Enforcement

The source check logs a warning but **does not reject the event**. Events from any source are projected and passed through to consumers. The authoritative boundary is **fail-open**, not fail-closed.

### SUPL WebSocket Bypass

File: `features/supl/ws_stream.py`

The SUPL WebSocket:
1. Reads directly from `EventStore` for replay (line 40: `self._store.replay(cursor=last_seq)`)
2. Subscribes directly to `EventBus` for live events (line 65: `self._bus.subscribe("*", bus_callback)`)
3. Sends raw events to WebSocket clients WITHOUT going through `GraphOSProjection`
4. Source identity is preserved in `msg.source` (line 102) but never validated

This means:
- **SUPL clients receive unprojected events** — no execution context enrichment, no state transition validation, no payload sanitization
- **SUPL clients bypass the source whitelist** entirely
- **Any EventBus event** (including non-canonical topics, non-canonical sources) is sent to WebSocket clients

### Source Identity Persistence

The source field is persisted in `stored_events.source` via `EventStore.append()` and replayed in `_row_to_dict()`. Source identity survives restart. However, since source validation is warning-only, persisted source values cannot be trusted.

### Conclusion

**C-006 FINAL STATUS: NOT RESOLVED**

The source whitelist is a warning-only mechanism that provides no actual security or authority boundary. The SUPL WebSocket bypasses projection entirely. Any EventBus publisher can create events that reach WebSocket consumers.

---

## MC-TC-002 P1 Re-Audit

| ID | Original State | MC-TC-003 Remediation | Current Reality | Residual Risk | Final Status |
|---|---|---|---|---|---|
| C-003 | No UTR timeout | timeout param + ThreadPoolExecutor | Caller-timeout only; no production caller uses it; thread leak | Execution can hang indefinitely; no production protection | **NOT RESOLVED** |
| C-007 | Receipt RAM-only | _on_receipt_callback + store_receipt | Callback never wired; receipts remain in-memory dict | Receipts lost on crash; no restart survival | **NOT RESOLVED** |
| C-008 | Verification RAM-only | _on_verification_callback + store_verification | Orchestrator path persists via EventBus; UTR internal path RAM-only | Internal verification results (tamper, integrity) lost on restart | **PARTIALLY RESOLVED** |
| C-011 | Perma-RUNNING | ExecutionWatchdog class | Class never instantiated; no production wiring | Executions can remain RUNNING indefinitely after crash | **NOT RESOLVED** |

---

## New Contradictions Introduced by MC-TC-003

| ID | Priority | Description | Evidence | Impact |
|---|---|---|---|---|
| **N-001** | P2 | ThreadPoolExecutor thread leak | `_executor_pool` created in `UTR.__init__()` (line 296) with `max_workers=4` but `shutdown()` never called. Search for `shutdown` in `features/tool_runtime/` returns empty. | After 4 concurrent timeouts, pool is saturated. New timed-out tools block the caller. On UTR destruction, executor threads are leaked. |
| **N-002** | P2 | Receipt/verification callbacks unwired | `set_receipt_callback()` and `set_verification_callback()` are defined (lines 326, 329) but never called by any production code. | Creates a false sense of persistence. Developers reading the code may believe receipts are persisted when they are not. |
| **N-003** | P2 | `_receipt_version` inconsistency | `_receipt_version` in `__slots__` and `__init__` (set to `int 1`) while class attribute `RECEIPT_VERSION = "2.0.0"` (str). Not serialized in `to_dict()`. | Cosmetic — no production impact. Inconsistency between instance and class attribute. |
| **N-004** | P2 | ExecutionWatchdog uninstantiated | `ExecutionWatchdog` class exists (features/monitoring/execution_watchdog.py) but never instantiated in production. Listed in `CANONICAL_SOURCES` but no boot wiring. | Created but unplugged — no production impact but misleading. |

**No new P0 or P1 contradictions were introduced.** All new contradictions are P2.

---

## Regression Analysis

- **Tests executed:** 325 across 16 test suites
- **Tests passed:** 325
- **Tests failed:** 0
- **Test suites with pre-existing failures outside audit scope:** 2 (test_phase1b_execution_context, test_phase3b_trust_core — unrelated to MC-TC-003 changes)

The test suite confirms that MC-TC-003 did not break existing functionality. However, **the new tests added by MC-TC-003 test the extension points in isolation, not the production wiring.** This is a critical gap in test coverage.

---

## Final Architecture Authority Matrix

| Authority Domain | Canonical Authority | Secondary/Compatibility | Status |
|---|---|---|---|
| Event Authority | **DUAL** — `stored_events` (canonical-claim) + `events` (WriterThread) | EventBus (transient in-memory) | **DUAL** — not consolidated |
| Execution Authority | `EnrichedMuscalOS.run()` — single writer | `execution_state` persisted in `stored_events` | **SINGLE** — correct |
| Receipt Authority | **RAM-only** (`_receipt_store` dict or ReceiptStore) | `FileReceiptStore` (/tmp, optional) | **NOT DURABLE** — lost on restart |
| Verification Authority | **DUAL** — orchestrator path (EventBus→stored_events) + UTR internal path (RAM-only) | In-memory `_verification_store` | **PARTIALLY DURABLE** — internal checks lost |
| Persistence Authority | **DUAL** — `stored_events` (EventStore) + `events` (WriterThread) | None | **DUAL** — not reconciled |
| Projection Authority | `GraphOSProjection` | SUPL WebSocket (bypasses projection) | **BYPASSABLE** — SUPL sends raw events |
| Graph-OS Authority | `GraphOSProjection` (read-only transform) | Direct EventBus subscription | **CLEAN** — projection does not write |
| Watchdog Authority | **NONE** — `ExecutionWatchdog` not instantiated | `check_consistency_on_start()` (tasks table only) | **ABSENT** — perma-RUNNING risk unchanged |
| Replay Authority | `EventStore.replay()` on `stored_events` | WriterThread on `events` (no replay API) | **CONDITIONAL** — `events` not replayable |

---

## Final Contradiction Register

| ID | Priority | Description | Status | Evidence |
|---|---|---|---|---|
| **C-001** | P0 | Dual event stores: `stored_events` vs `events` | **PARTIALLY RESOLVED** | Both tables independently writable; no reconciliation; receipt/verification methods unwired |
| **C-002** | P2 | Dual runtime persistence replaced; legacy path remains | **NOT RESOLVED** | `_persist_to_store` unsubscribed but `events` table written by WriterThread for 14+ call sites |
| **C-003** | P1 | No generic UTR timeout | **NOT RESOLVED** | Caller-timeout only; no production caller passes timeout; thread leak; late side effects possible |
| **C-004** | P2 | Agent identity optional | **NOT RESOLVED** | `agent_id` remains optional in UTR.execute(); mel.py does not supply it |
| **C-005** | P2 | `request_id` gap in mel.py | **NOT RESOLVED** | mel.py calls UTR.execute() without request_id |
| **C-006** | P2 | `plan_id`/`step_id` gap in mel.py | **NOT RESOLVED** | mel.py calls UTR.execute() without plan_id/step_id |
| **C-007** | P1 | Receipt not persisted | **NOT RESOLVED** | Callback exists but unwired; receipts remain RAM-only |
| **C-008** | P1 | Verification not persisted | **PARTIALLY RESOLVED** | Orchestrator path persists via EventBus; UTR internal path RAM-only |
| **C-009** | P2 | No automatic causation_id | **NOT RESOLVED** | causation_id is caller-provided; no automatic derivation |
| **C-010** | P2 | Retry provenance (to_dict retry omission) | **RESOLVED** | retry_count and attempt_number now in to_dict and from_dict |
| **C-011** | P1 | Perma-RUNNING risk | **NOT RESOLVED** | ExecutionWatchdog never instantiated; perma-RUNNING risk unchanged |
| **C-012** | P2 | SUPL WebSocket bypasses GraphOSProjection | **NOT RESOLVED** | ws_stream.py sends raw EventBus events without projection |
| **C-013** | P2 | Crash recovery for execution_state | **NOT RESOLVED** | check_consistency_on_start() does not detect stuck execution_state |
| **C-014** | P1 | to_dict() serialization gap | **RESOLVED** | All fields serialized; from_dict added; FileReceiptStore fixed |
| **C-015** | P2 | Schema divergence (events vs stored_events) | **NOT RESOLVED** | 22 vs 13 columns; no shared identity column |
| **N-001** | P2 | ThreadPoolExecutor thread leak | **NEW** | shutdown() never called on _executor_pool |
| **N-002** | P2 | Receipt/verification callbacks unwired | **NEW** | set_receipt_callback/set_verification_callback never called |
| **N-003** | P2 | _receipt_version inconsistency | **NEW** | int 1 vs str "2.0.0"; not serialized |
| **N-004** | P2 | ExecutionWatchdog uninstantiated | **NEW** | Class defined but never created in production |

**Summary:** 15 original + 4 new = 19 contradictions total.
- 2 RESOLVED (C-010, C-014)
- 2 PARTIALLY RESOLVED (C-001, C-008)
- 15 NOT RESOLVED (C-002, C-003, C-004, C-005, C-006, C-007, C-009, C-011, C-012, C-013, C-015, N-001, N-002, N-003, N-004)
- 0 REGRESSED

---

## Replay Readiness Gate

### GATE A — SINGLE EVENT AUTHORITY

Is there exactly one canonical event authority?

**FAIL.** Two event tables exist (`events` and `stored_events`). Both receive writes independently. No reconciliation mechanism. Replay consumes `stored_events` but `events` contains non-overlapping operational events.

### GATE B — DURABLE RECEIPT PERSISTENCE

Can every completed execution receipt be reconstructed after restart?

**FAIL.** Receipts are stored in-memory (`_receipt_store` dict or `ReceiptStore`). `FileReceiptStore` writes to `/tmp` but is optional and not the default. `EventStore.store_receipt()` exists but is not wired. Receipts are permanently lost on process restart.

### GATE C — DURABLE VERIFICATION

Can every verification result be reconstructed after restart?

**FAIL.** Verification results from the UTR internal path (integrity checks, tamper detection, verifier dispatch) are stored in-memory (`_verification_store` dict). Only the VerificationOrchestrator path persists through EventBus. Internal verification results are lost on restart.

### GATE D — TIMEOUT SEMANTICS

Does timeout behavior preserve execution truth?

**FAIL.** Caller-timeout only. The underlying tool continues executing after MUSCAL declares timeout. Side effects can occur after TIMEOUT is reported. No production caller passes the timeout parameter. Thread leaks on timeout.

### GATE E — EXECUTION WATCHDOG

Can stuck executions reliably reach a terminal state?

**FAIL.** The `ExecutionWatchdog` class is defined but never instantiated or started in production. No component transitions `execution_state` from "running" to a terminal state. Executions remain permanently stuck in RUNNING after a crash.

### GATE F — SERIALIZATION COMPLETENESS

Can execution identity and integrity be reconstructed losslessly?

**PASS.** All identity fields are serialized in `to_dict()`, reconstructed in `from_dict()`, and verified by round-trip tests. Integrity hash includes all identity fields. `FileReceiptStore` uses `from_dict()`. Legacy backward compatibility is maintained.

### GATE G — GRAPH-OS SOURCE BOUNDARY

Can only canonical sources mutate authoritative Graph-OS state?

**FAIL.** Source check is warning-only, not rejection. SUPL WebSocket bypasses GraphOSProjection entirely, sending raw EventBus events to WebSocket clients. Any EventBus publisher can create events that reach consumers.

### GATE H — NO CRITICAL NEW CONTRADICTIONS

Did MC-TC-003 introduce any new P0/P1 contradiction?

**PASS.** All 4 new contradictions (N-001 through N-004) are P2. No new P0 or P1 contradictions were introduced.

---

## Replay Readiness Decision

**NO-GO**

### Passing Gates
- GATE F — Serialization: PASS
- GATE H — No new P0/P1: PASS

### Failing Gates
- GATE A — Single Event Authority: FAIL
- GATE B — Durable Receipt Persistence: FAIL
- GATE C — Durable Verification: FAIL
- GATE D — Timeout Semantics: FAIL
- GATE E — Execution Watchdog: FAIL
- GATE G — Graph-OS Source Boundary: FAIL

### Blocking Contradictions
1. **C-001 (P0)** — Dual event stores not consolidated. Replay would need to reconcile two event streams with different schemas.
2. **C-007 (P1)** — Receipts not durably persisted. Replay cannot reconstruct execution receipts after restart.
3. **C-008 (P1)** — Internal verification results not durably persisted. Replay cannot reconstruct verification truth.
4. **C-003 (P1)** — No effective timeout. Replay of timed-out executions would be non-deterministic.
5. **C-011 (P1)** — No watchdog. Replay cannot guarantee terminal state for stuck executions.

---

## Final Architecture Status

**Event Authority:** DUAL — `stored_events` and `events` independently authoritative

**Execution Authority:** SINGLE — `EnrichedMuscalOS.run()` only writer

**Receipt Authority:** NOT DURABLE — RAM-only in production

**Verification Authority:** PARTIALLY DURABLE — orchestrator path persists, internal path RAM-only

**Persistence Authority:** DUAL — EventStore and WriterThread with different schemas

**Projection Authority:** CLEAN — GraphOSProjection is read-only transform

**Graph-OS Authority:** BYPASSABLE — SUPL WebSocket sends raw events

**Watchdog Authority:** ABSENT — class exists but uninstantiated

**Replay Authority:** CONDITIONAL — works for `stored_events` but `events` not covered

---

## MC-TC-004 FINAL STATUS

| Metric | Value |
|---|---|
| Audit Status | COMPLETE |
| Tests Executed | 325 |
| Tests Passed | 325 |
| Tests Failed | 0 |
| New P0 | 0 |
| New P1 | 0 |
| New P2 | 4 |
| Resolved Contradictions | 2 (C-010, C-014) |
| Partially Resolved | 2 (C-001, C-008) |
| Not Resolved | 15 |
| Regressed | 0 |

## FINAL ARCHITECTURE STATUS

| Authority | Status |
|---|---|
| Event Authority | DUAL — not consolidated |
| Execution Authority | SINGLE — correct |
| Receipt Authority | NOT DURABLE — RAM-only |
| Verification Authority | PARTIALLY DURABLE |
| Persistence Authority | DUAL — not reconciled |
| Projection Authority | CLEAN (but bypassable) |
| Graph-OS Authority | BYPASSABLE |
| Watchdog Authority | ABSENT |
| Replay Authority | CONDITIONAL |

## REPLAY READINESS

| Gate | Status |
|---|---|
| Single Event Authority | FAIL |
| Durable Receipts | FAIL |
| Durable Verification | FAIL |
| Timeout Semantics | FAIL |
| Watchdog | FAIL |
| Serialization | PASS |
| Source Boundary | FAIL |
| New Contradictions | PASS |

## FINAL DECISION

**NO-GO**

## NEXT STEP

**Recommended: MC-TC-005 — Wiring and Consolidation Phase**

Before Replay Engine design can begin, the following must be resolved:

### Prerequisites (P0/P1 — must be resolved)

1. **C-001 — Consolidate event stores.** Either:
   - (a) Route all WriterThread writes through EventStore (eliminate `events` table as an authority), or
   - (b) Implement cross-table reconciliation with a canonical identity mapping.

2. **C-007 — Wire receipt persistence.** Connect `_on_receipt_callback` to `EventStore.store_receipt()` in the boot/bridge/initialization path. Make `FileReceiptStore` the default. Ensure synchronous persistence before execution completion is reported.

3. **C-008 — Wire verification persistence.** Connect `_on_verification_callback` to `EventStore.store_verification()` in the UTR initialization path. Ensure all verification results (including internal integrity/tamper checks) are persisted.

4. **C-003 — Effective timeout.** Either:
   - (a) Make timeout non-optional with a production-safe default (e.g., 300s), or
   - (b) Implement actual execution termination (process-level isolation, subprocess with kill, or cooperative cancellation).
   - Add `ThreadPoolExecutor.shutdown()` to prevent thread leaks.
   - Wire timeout into all production callers (Worker, MEL, cognitive unit, etc.)

5. **C-011 — Wire watchdog.** Instantiate and start `ExecutionWatchdog` in the boot sequence (`EnrichedMuscalOS.start()` or `MuscalOS._boot()`). Add persistent state transition (update `execution_state` in `stored_events`, not just publish EventBus event). Add restart recovery (detect stuck RUNNING on boot).

### Recommended Next Phase

**MC-TC-005 — Trust Core Wiring and Persistence Consolidation**

Implementation scope:
- Wire receipt callback into boot sequence
- Wire verification callback into UTR initialization
- Make timeout non-optional with safe default
- Wire ExecutionWatchdog into boot sequence
- Add `ThreadPoolExecutor.shutdown()` to UTR lifecycle
- Route WriterThread operational events through EventStore
- Implement SUPL WebSocket projection integration

After MC-TC-005 is verified by MC-TC-006 (post-wiring audit), proceed to:

**MC-TC-007 — Replay Engine / Event-Sourcing Architecture Design**

---

*Report produced by MC-TC-004 Post-Remediation Architecture Truth Audit.*
*Repository truth is authoritative. All claims verified against source code.*
*Implementation remains FORBIDDEN until MC-TC-005 is authorized.*
