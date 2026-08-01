# MC-TC-003D — MUSCAL Trust Core Architecture Review Report

**Date:** 2026-07-26
**Status:** APPROVED WITH CONDITIONS
**Review Phase:** MC-TC-003D
**Previous Phase:** MC-TC-003B (Identity + Execution State Implementation)
**Next Phase:** MC-TC-004 — Evidence + Verification + Execution Truth

---

## Executive Verdict

**APPROVED WITH CONDITIONS**

The MUSCAL Trust Core architecture is fundamentally sound in its design concepts — the identity model (UUID v7), the 3D state machine (Mode × State × Verification), the state transition validation, and the claim/evidence boundary — but the MC-TC-003B implementation contains **three critical (P0) vulnerabilities** and **five high-severity (P1) findings** that must be resolved before MC-TC-004 can proceed safely.

The architecture CAN distinguish claims from execution in principle. The implementation does NOT reliably make this distinction in practice.

---

## Scope

This review covers:
- `features/identity/` — ExecutionContext, reality model, UUID v7
- `kernel.py` — MuscalKernel identity integration
- `muscal_os.py` — OS-layer execution orchestration
- `features/bootstrap/enriched_bootstrap.py` — EnrichedMuscalOS wrapper
- `runtime/event_store.py` — Event persistence
- `event_bus.py` — Event publish/subscribe
- `os_config.py` — Execution mode configuration
- `schema.py`, `graph.py` — Graph state identity propagation
- `tests/test_phase3b_trust_core.py` — MC-TC-003B tests
- `tests/test_phase3d_adversarial.py` — Adversarial reproduction tests (new)

### Out of Scope
- `features/verification/` — Pending MC-TC-004 review
- `features/tool_runtime/` — Tool runtime verification
- `runtime/kernel/writer.py` — WriterThread (deprecated for trust)
- `events` table — Parallel event store (deprecated for trust)
- ReplayService — Pending MC-TC-004 review

---

## Methodology

1. **Source code audit** — Read every file modified by MC-TC-003B
2. **Adversarial testing** — 18 targeted adversarial tests reproducing 15 attack scenarios
3. **Trust boundary analysis** — L0-L10 semantic ladder classification
4. **Invariant enforcement audit** — 16 invariants checked against code
5. **False guarantee audit** — Identified undocumented assumptions
6. **Hidden coupling audit** — Detected unintended semantic dependencies
7. **Formal trust model** — Defined allowed relationships between evidence levels

---

## Critical Findings

### P0-C01: Double Identity — EnrichedMuscalOS vs MuscalOS conflict

**Severity:** CRITICAL (P0)
**Location:** `features/bootstrap/enriched_bootstrap.py:76` + `muscal_os.py:137`
**Affected Contract:** MC-TC-003A Canonical Identity Model

`EnrichedMuscalOS.run()` generates `execution_id=A` (line 76), then delegates to `self._os.run(input_text)` (line 95) **WITHOUT passing the execution context**. `MuscalOS.run()` generates a **new** `ExecutionContext` with `execution_id=B` (line 137-140). The enriched wrapper publishes lifecycle events with identity A, but the kernel runs with identity B.

**Impact:** Two identity chains per single execution. Lifecycle events cannot be causally linked to kernel execution events. Provenance reconstruction from EventStore produces two disjoint identity trees.

**Evidence:** `features/bootstrap/enriched_bootstrap.py:94-95` calls `self._os.run(input_text)` — no `execution_context` or `execution_mode` parameter. `muscal_os.py:129` accepts `input_text: str, execution_mode: str = ""` but `EnrichedMuscalOS` never passes `execution_mode`. `muscal_os.py:137` generates `ExecutionContext(...)` unconditionally.

### P0-C02: Default persistence path drops identity

**Severity:** CRITICAL (P0)
**Location:** `muscal_os.py:257-268` (`_persist_to_store`)
**Affected Contract:** MC-TC-003A Canonical Event Contract

The default EventStore persistence subscriber `_persist_to_store` does NOT extract `execution_id`, `correlation_id`, `causation_id`, `execution_mode`, `execution_state`, or `verification_state` from events. It passes only `topic`, `payload`, `source`, `priority`, `timestamp`, and `id`. All identity columns in the `stored_events` table remain empty for events written through this path.

**Impact:** Events persisted through `MuscalOS._persist_to_store` (the default path when `EnrichedMuscalOS` is not used) have ZERO identity traceability. This negates the entire identity enrichment architecture.

**Evidence:** `muscal_os.py:257-268` shows six fields passed to `EventStore.append()` — none of the identity columns. Compare with `enriched_bootstrap.py:149-167` which correctly passes all identity fields.

### P0-C03: No authority enforcement on state fields

**Severity:** CRITICAL (P0)
**Location:** `features/identity/execution_context.py:44-54`
**Affected Contract:** MC-TC-003A Execution State Machine

`ExecutionContext` is a `@dataclass` with plain public fields. Any code can directly set `execution_state`, `verification_state`, or any identity field without going through `transition_state()`, `set_verification()`, or any validation. The validation methods exist but are entirely opt-in.

**Impact:** A component can set `verification_state = "verified"` without any verification process. The system has no mechanism to distinguish authorized state transitions from unauthorized mutations.

**Evidence:** Adversarial test `test_verification_state_direct_mutation` (test_phase3d_adversarial.py) and `test_execution_state_direct_mutation_bypasses_validator` confirm this.

---

## High-Severity Findings

### P1-F01: EventBus.id is not a UUID

**Severity:** HIGH (P1)
**Location:** `event_bus.py:51`
`msg.id` is formatted as `{topic}_{history_len}_{timestamp_ms}`. This is used as the `event_id` in EventStore's UNIQUE constraint. While unique locally, it is not a true UUID and cannot provide distributed uniqueness or time-ordered properties.

### P1-F02: store_receipt hardcodes execution_mode='real'

**Severity:** HIGH (P1)
**Location:** `runtime/event_store.py:110`
Receipts are always stored with `execution_mode='real'` regardless of the actual execution mode. Simulated execution receipts are mislabeled as real at the persistence layer.

### P1-F03: store_verification hardcodes execution_mode='real'

**Severity:** HIGH (P1)
**Location:** `runtime/event_store.py:128`
Same issue as P1-F02 for verification records.

### P1-F04: store_receipt causation direction error

**Severity:** HIGH (P1)
**Location:** `runtime/event_store.py:127`
`causation_id` is set to the receipt's own `receipt_id`, implying the receipt caused itself. The causation_id should point to the execution or request that caused the receipt.

### P1-F05: Orphan events accepted without validation

**Severity:** HIGH (P1)
**Location:** `runtime/event_store.py:50-95`
`EventStore.append()` accepts any `execution_id` without validating that the referenced execution exists. Events with non-existent or empty execution_ids are stored without warning or rejection.

---

## Medium-Severity Findings

### P2-F01: Claim markers (_is_claim) are advisory
### P2-F02: Simulated/real events indistinguishable at replay
### P2-F03: No causal ordering constraints in EventStore
### P2-F04: Conflicting verification results accepted without conflict detection
### P2-F05: No ground-truth verification after execution
### P2-F06: Execution and event persistence are not atomic
### P2-F07: Thread-local context can cross-contaminate under async dispatch

---

## Contradiction Summary

| ID | Status | Type | Source |
|----|--------|------|--------|
| P0-C01 | NEW | Double Identity | MC-TC-003B implementation defect |
| P0-C02 | NEW | Identity not persisted | MC-TC-003B implementation defect |
| P0-C03 | NEW | No authority enforcement | MC-TC-003B design limitation |
| P1-F01 | NEW | Non-UUID event IDs | MC-TC-003B (pre-existing) |
| P1-F02 | NEW | store_receipt mode leak | MC-TC-003B (pre-existing) |
| P1-F03 | NEW | store_verification mode leak | MC-TC-003B (pre-existing) |
| P1-F04 | NEW | Causation direction error | MC-TC-003B (pre-existing) |
| P1-F05 | NEW | Orphan event acceptance | MC-TC-003B (pre-existing) |
| P2-F01..P2-F07 | DOCUMENTED | Various | Cross-cutting |

---

## Recommendations

### Immediate (must precede MC-TC-004):

1. **Fix Double Identity:** `EnrichedMuscalOS.run()` must pass its `ExecutionContext` to `MuscalOS.run()`. Either pass the context object directly or add a method parameter.

2. **Fix _persist_to_store to propagate identity:** Extract `execution_id`, `correlation_id`, `causation_id`, `execution_mode`, `execution_state`, `verification_state` from `msg.payload` (or from a thread-local context) when persisting events.

3. **Add property protection or frozen fields:** Make `execution_state` and `verification_state` properties that route through validation when set externally. Alternatively, make the context frozen after creation.

4. **Fix EventBus.id to use UUID v7:** Replace the format-string ID with `uuid7()`.

5. **Fix store_receipt/store_verification mode propagation:** Use receipt/verification's actual execution_mode instead of hardcoded 'real'.

6. **Fix causation direction:** `store_receipt` should set `causation_id` to the execution_id or request_id that caused the receipt, not the receipt's own id.

### For MC-TC-004:

7. **Add causal ordering validation** to EventStore (reject events that violate causal constraints)
8. **Add execution existence validation** when storing receipts/verifications
9. **Add verification conflict detection** (reject conflicting verification results for same execution)
10. **Make execution→persistence atomic** (WAL journal, or two-phase commit)
