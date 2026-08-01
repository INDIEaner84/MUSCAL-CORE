# MC-TC-003D — False Guarantee Audit

---

## Classification

| Classification | Meaning |
|----------------|---------|
| SAFE | Guarantee is adequately supported |
| ACCEPTABLE | Guarantee is reasonable within scope |
| RISK | Guarantee is overstated or has known counterexamples |
| CRITICAL | Guarantee is unsupported by architecture |

---

## Findings

### FG-01: "execution_id is generated and propagated"

**Claim:** Execution ID is generated once and propagated to all events.
**Actual:** Double identity (P0-C01) — EnrichedMuscalOS and MuscalOS generate different IDs. `_persist_to_store` drops identity (P0-C02).
**Classification:** CRITICAL

---

### FG-02: "verification_state is authoritative"

**Claim:** Verification state represents actual verification status.
**Actual:** Plain dataclass field — any code can set it directly. No verifier requirement (P0-C03).
**Classification:** CRITICAL

---

### FG-03: "execution_state follows validated transitions"

**Claim:** Execution state changes go through transition validation.
**Actual:** Direct field mutation bypasses all validation (P0-C03).
**Classification:** CRITICAL

---

### FG-04: "Events are enriched with execution identity"

**Claim:** All persisted events carry execution_id, correlation_id, etc.
**Actual:** Only when `_enriched_persist` is used. Default `_persist_to_store` drops all identity fields (P0-C02).
**Classification:** CRITICAL

---

### FG-05: "store_receipt preserves execution mode"

**Claim:** Receipts are stored with correct execution_mode.
**Actual:** `execution_mode='real'` hardcoded regardless of actual mode (P1-F02).
**Classification:** RISK

---

### FG-06: "Causation chain is correctly maintained"

**Claim:** causation_id correctly points to the cause of an event.
**Actual:** `store_receipt` sets causation_id to receipt's own id (backwards) (P1-F04).
**Classification:** RISK

---

### FG-07: "Execution receipt proves tool execution"

**Claim:** ExecutionReceipt with integrity hash proves tool was executed.
**Actual:** Receipt proves a result was recorded, not that the tool ran. Receipts can be forged via `EventStore.append()` (A-006). Receipt proves data, not physical execution.
**Classification:** ACCEPTABLE (with documentation)

**Note:** This is an inherent limitation, not an implementation defect. The architecture explicitly distinguishes evidence from proof. The receipt IS strong evidence, but is not cryptographically proven execution.

---

### FG-08: "Verification is independent"

**Claim:** Verification uses independent verifiers.
**Actual:** Some verifiers (FilesystemVerifier, OpenCodeRunVerifier) accept agent-provided expected content, reducing independence. Verification is not automatically triggered.
**Classification:** RISK

---

### FG-09: "Simulation vs Real is reliably distinguished"

**Claim:** Simulated and real executions are distinguishable.
**Actual:** `execution_mode` field exists but `store_receipt`/`store_verification` hardcode 'real'. EventStore has no mode-based segregation. Replay returns both modes interleaved.
**Classification:** RISK

---

### FG-10: "EventStore append is authoritative"

**Claim:** Events in EventStore are an authoritative record.
**Actual:** EventStore.append() has no authentication. Any code can write any event. Orphan events with non-existent execution_ids are accepted (P1-F05).
**Classification:** RISK

---

### FG-11: "359/359 tests prove correctness"

**Claim:** Passing tests validate the Trust Core architecture.
**Actual:** Tests validate specific behavior but do NOT test adversarial scenarios. 18 adversarial tests reveal 8 vulnerabilities that MC-TC-003B tests did not cover.
**Classification:** CRITICAL (overclaiming test coverage)

---

## Summary

| Classification | Count | IDs |
|----------------|-------|-----|
| SAFE | 0 | — |
| ACCEPTABLE | 1 | FG-07 |
| RISK | 6 | FG-05, FG-06, FG-08, FG-09, FG-10 |
| CRITICAL | 4 | FG-01, FG-02, FG-03, FG-04, FG-11 |

**Total: 11 false or overstated guarantees found. 4 CRITICAL, 6 RISK, 1 ACCEPTABLE.**
