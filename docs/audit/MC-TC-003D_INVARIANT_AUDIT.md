# MC-TC-003D — Architectural Invariant Audit

---

## Invariant Summary

| # | Invariant | Source | Enforcement | Test Coverage | Runtime | Persistence | Status | Risk |
|---|-----------|--------|-------------|---------------|---------|-------------|--------|------|
| I-01 | execution_id is unique | UUID v7 spec | Generation only | test_phase3b | NOT ENFORCED | ENFORCED (event_id UNIQUE) | PARTIAL | LOW |
| I-02 | execution_id is immutable after creation | Canonical Identity | No — plain field | test_phase3b | NOT ENFORCED | N/A | WEAKENED | MEDIUM |
| I-03 | execution_id is propagated to all events | Canonical Identity | Code convention | test_phase3b | NOT ENFORCED (P0-C02) | DEFAULT EMPTY | CONTRADICTED | CRITICAL |
| I-04 | Event identity is distinct from execution identity | Canonical Identity | Separate EventIdentity class | test_phase3b | NOT ENFORCED | N/A | DOCUMENTED ONLY | LOW |
| I-05 | Causation chain is reconstructable | Canonical Identity | causation_id field | test_phase3b | NOT ENFORCED (P1-F04) | NOT ENFORCED | WEAKENED | HIGH |
| I-06 | Correlation groups are isolated | Canonical Identity | correlation_id field | test_phase3b | NOT ENFORCED | NOT ENFORCED | DOCUMENTED ONLY | MEDIUM |
| I-07 | Simulation mode is distinct from real mode | Canonical Identity | execution_mode field | test_phase3b | NOT ENFORCED (P1-F02) | NOT ENFORCED | WEAKENED | HIGH |
| I-08 | State transitions follow validated path | State Machine | transition_state() | test_phase3b | NOT ENFORCED (P0-C03) | N/A | CONTRADICTED | CRITICAL |
| I-09 | Verification state changes follow verified path | State Machine | set_verification() | test_phase3b | NOT ENFORCED (P0-C03) | N/A | CONTRADICTED | CRITICAL |
| I-10 | Replay events are distinguishable | Replay Isolation | _replayed marker | Not tested | PARTIALLY ENFORCED | ENFORCED (append rejects) | PARTIALLY ENFORCED | LOW |
| I-11 | EventStore is append-only | Event Store | SQLite AUTOINCREMENT | test_event_store | ENFORCED | ENFORCED | ENFORCED | LOW |
| I-12 | EventStore has unique event IDs | Event Store | event_id UNIQUE | test_event_store | N/A | ENFORCED | ENFORCED | LOW |
| I-13 | Execution state transitions follow mode constraints | State Machine | validate_state_transition | test_phase3b | ENFORCED (via methods) | N/A | ENFORCED (when called) | MEDIUM |
| I-14 | Verification state transitions follow mode constraints | State Machine | validate_state_transition | test_phase3b | ENFORCED (via methods) | N/A | ENFORCED (when called) | MEDIUM |
| I-15 | Graph nodes carry execution_id | Graph State | schema.Node.execution_id | test_phase3b | ENFORCED (via add_node) | N/A | ENFORCED | LOW |
| I-16 | kernel.run() accepts execution context | Kernel Identity | kernel.py:631 parameter | test_phase3b | ENFORCED | N/A | ENFORCED | LOW |

---

## Detailed Audit

### I-01: execution_id is unique
- **Status:** PARTIALLY ENFORCED
- **Risk:** LOW
- **Detail:** UUID v7 provides probabilistic uniqueness. No uniqueness constraint exists at database level for execution_id (only event_id has UNIQUE constraint). In practice, UUID v7 collision probability is negligible.
- **Recommendation:** Add execution_id UNIQUE index on stored_events if execution_id must be non-repeating.

### I-02: execution_id is immutable after creation
- **Status:** WEAKENED
- **Risk:** MEDIUM
- **Detail:** `execution_id` is a plain dataclass field. Nothing prevents reassignment. Tests verify that the initial value is preserved (`test_execution_id_generated_once`) but do not verify that reassignment is prevented.
- **Recommendation:** Make execution_id a `@property` with a private backing field, or freeze the dataclass after creation.

### I-03: execution_id is propagated to all events
- **Status:** CONTRADICTED (P0-C02)
- **Risk:** CRITICAL
- **Detail:** `_persist_to_store` (default path) does NOT propagate execution_id to EventStore identity columns. Only `_enriched_persist` in EnrichedMuscalOS correctly propagates. Events written through the default path have empty identity columns.
- **Evidence:** `muscal_os.py:257-268` — six fields passed, none are identity fields.

### I-04: Event identity is distinct from execution identity
- **Status:** DOCUMENTED ONLY
- **Risk:** LOW
- **Detail:** `EventIdentity` class exists with `event_id` separate from `execution_id`. But `EventIdentity` is NOT used by EventBus — EventBus generates its own non-UUID id format. The `EventIdentity.from_context()` factory exists but is never called in any execution path.
- **Recommendation:** Wire EventIdentity into EventBus.publish() or EventStore.append().

### I-05: Causation chain is reconstructable
- **Status:** WEAKENED (P1-F04)
- **Risk:** HIGH
- **Detail:** `store_receipt` sets `causation_id` to the receipt's OWN receipt_id, which is semantically backwards. The causation_id should point to the execution or request that caused the receipt. This makes causal chain reconstruction unreliable.
- **Evidence:** `runtime/event_store.py:127` — `"causation_id": getattr(vr, "receipt_id", "")`.

### I-06: Correlation groups are isolated
- **Status:** DOCUMENTED ONLY
- **Risk:** MEDIUM
- **Detail:** correlation_id is a user-supplied or auto-generated field with no validation. Group isolation relies on correct assignment by calling code.
- **Recommendation:** Add correlation_id validation (non-empty, proper format).

### I-07: Simulation mode is distinct from real mode
- **Status:** WEAKENED (P1-F02, P1-F03)
- **Risk:** HIGH
- **Detail:** `store_receipt` hardcodes `execution_mode='real'`. `store_verification` also hardcodes `execution_mode='real'`. The mode distinction exists in `ExecutionContext` and EventBus events, but is lost at the persistence layer for receipts and verifications.
- **Evidence:** `runtime/event_store.py:110,128`.

### I-08: State transitions follow validated path
- **Status:** CONTRADICTED (P0-C03)
- **Risk:** CRITICAL
- **Detail:** `transition_state()` method validates via `validate_execution_state_change()` and `validate_state_transition()`. But direct field mutation (`ctx.execution_state = "completed"`) bypasses ALL validation. No property protection exists.
- **Evidence:** Adversarial test `test_execution_state_direct_mutation_bypasses_validator`.

### I-09: Verification state changes follow verified path
- **Status:** CONTRADICTED (P0-C03)
- **Risk:** CRITICAL
- **Detail:** Same as I-08 — `verification_state` is a plain dataclass field.
- **Evidence:** Adversarial test `test_verification_state_direct_mutation`.

### I-10: Replay events are distinguishable
- **Status:** PARTIALLY ENFORCED
- **Risk:** LOW
- **Detail:** ReplayService sets `_replayed=True` in event payload. EventStore.append() checks for this marker and returns None (event suppressed). However, this relies on the marker being consistently set — it is not a column-level constraint.

### I-11: EventStore is append-only
- **Status:** ENFORCED
- **Risk:** LOW
- **Detail:** SQLite AUTOINCREMENT primary key ensures append-only semantics. No UPDATE or DELETE operations are exposed by EventStore API.

### I-12: EventStore has unique event IDs
- **Status:** ENFORCED
- **Risk:** LOW
- **Detail:** `event_id TEXT NOT NULL UNIQUE` constraint on stored_events table.

### I-13: Execution state transitions follow mode constraints
- **Status:** ENFORCED (when called)
- **Risk:** MEDIUM
- **Detail:** `validate_state_transition()` correctly enforces mode×state×verification constraints. Called by `transition_state()` and `set_verification()`. Enforcement quality depends on these methods being used rather than direct field mutation.

### I-14: Verification state transitions follow mode constraints
- **Status:** ENFORCED (when called)
- **Risk:** MEDIUM
- **Detail:** Same as I-13 — validation exists but is bypassable.

### I-15: Graph nodes carry execution_id
- **Status:** ENFORCED
- **Risk:** LOW
- **Detail:** `schema.py:Node` has `execution_id` field. `graph.py:add_node()` accepts and propagates it. `get_snapshot()` includes it.

### I-16: kernel.run() accepts execution context
- **Status:** ENFORCED
- **Risk:** LOW
- **Detail:** `kernel.py:631` accepts `execution_context: Optional[ExecutionContext]`. Generates default if None.

---

## Enforcement Quality Summary

| Quality | Count | Invariants |
|---------|-------|------------|
| ENFORCED | 4 | I-11, I-12, I-15, I-16 |
| PARTIALLY ENFORCED | 2 | I-01, I-10 |
| ENFORCED (when called) | 2 | I-13, I-14 |
| DOCUMENTED ONLY | 2 | I-04, I-06 |
| WEAKENED | 3 | I-02, I-05, I-07 |
| CONTRADICTED | 2 | I-03, I-08, I-09 |
| NOT ENFORCED | 0 | — |

**Key finding:** 7/16 invariants (44%) are either weakened or contradicted.
