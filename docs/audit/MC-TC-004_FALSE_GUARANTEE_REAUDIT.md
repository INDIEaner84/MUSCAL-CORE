# MC-TC-004 — False Guarantee Re-Audit

---

## Methodology

Each false guarantee from MC-TC-003F (11 total) is re-evaluated against the
MC-TC-004 implementation. Only changes from MC-TC-003F are annotated.

| Status | Meaning |
|--------|---------|
| RESOLVED | Guarantee is now adequately supported |
| PARTIALLY RESOLVED | Some aspects addressed; residual gap remains |
| STILL FALSE | Guarantee remains unsupported |
| NOT APPLICABLE | Circumstances changed |
| **STRENGTHENED** | Guarantee was already RESOLVED; enforcement improved |

---

## FG-01: "execution_id is generated and propagated"

| Dimension | Detail |
|-----------|--------|
| **003F status** | RESOLVED — Single identity chain across all boundaries |
| **MC-TC-004 change** | None |
| **004 status** | **RESOLVED** — unchanged |

---

## FG-02: "verification_state is authoritative"

| Dimension | Detail |
|-----------|--------|
| **003F status** | RESOLVED — Property guard prevents direct mutation |
| **MC-TC-004 change** | **STRENGTHENED** — `set_verification("verified")` now requires `evidence_receipt_id` (S-03). Orchestrator passes `vr.receipt_id`. `store_verification()` validates receipt_id. |
| **004 status** | **RESOLVED** (strengthened) — verification_state is now more authoritative because VERIFIED requires evidence. A verification cannot reach VERIFIED status without a receipt_id. |
| **Evidence** | `execution_context.py:165-169`, `event_store.py:202-210`, `orchestrator.py:167` |

---

## FG-03: "execution_state follows validated transitions"

| Dimension | Detail |
|-----------|--------|
| **003F status** | RESOLVED — Property guard + transition_state() validation |
| **MC-TC-004 change** | None |
| **004 status** | **RESOLVED** — unchanged |

---

## FG-04: "Events are enriched with execution identity"

| Dimension | Detail |
|-----------|--------|
| **003F status** | RESOLVED — Both persistence paths propagate identity |
| **MC-TC-004 change** | None |
| **004 status** | **RESOLVED** — unchanged |

---

## FG-05: "store_receipt preserves execution mode"

| Dimension | Detail |
|-----------|--------|
| **003F status** | RESOLVED — execution_mode derived from receipt object |
| **MC-TC-004 change** | None |
| **004 status** | **RESOLVED** — unchanged |

---

## FG-06: "Causation chain is correctly maintained"

| Dimension | Detail |
|-----------|--------|
| **003F status** | RESOLVED — causation direction corrected (P1-F04) |
| **MC-TC-004 change** | None |
| **004 status** | **RESOLVED** — unchanged |

---

## FG-07: "Execution receipt proves tool execution"

| Dimension | Detail |
|-----------|--------|
| **003F status** | STILL ACCEPTABLE — Receipt proves data recorded, not tool executed |
| **MC-TC-004 change** | None |
| **004 status** | **STILL ACCEPTABLE** — Inherent architectural limitation. MC-TC-004 evidence requirement (S-03) requires a receipt_id for verification, but does not claim the receipt proves external execution. The epistemic boundary ACTUAL EXECUTION ≠ EVIDENCE is maintained. |

---

## FG-08: "Verification is independent"

| Dimension | Detail |
|-----------|--------|
| **003F status** | STILL ACCEPTABLE — Verifier independence depends on caller |
| **MC-TC-004 change** | None |
| **004 status** | **STILL ACCEPTABLE** — unchanged |

---

## FG-09: "Simulation vs Real is reliably distinguished"

| Dimension | Detail |
|-----------|--------|
| **003F status** | RESOLVED — execution_mode correctly persisted |
| **MC-TC-004 change** | None |
| **004 status** | **RESOLVED** — unchanged |

---

## FG-10: "EventStore append is authoritative"

| Dimension | Detail |
|-----------|--------|
| **003F status** | PARTIALLY RESOLVED — P1-F05 orphan prevention; no authentication |
| **MC-TC-004 change** | **IMPROVED** — verification events now have conflict detection (S-04). A conflicting verification cannot be silently appended. This strengthens the authority of verification events in EventStore. |
| **004 status** | **PARTIALLY RESOLVED** (improved): |
| | - P1-F05: execution_id required for execution topics (carried forward) |
| | - S-04: VerificationConflictError prevents conflicting overwrites **NEW** |
| | - Still no authentication on append (architectural scope boundary) |
| | - Still no semantic execution_id validation (EventStore does not cross-reference with ExecutionContextManager) |
| **Evidence** | `event_store.py:214-230` (conflict detection) |

---

## FG-11: "Tests prove correctness"

| Dimension | Detail |
|-----------|--------|
| **003F status** | RESOLVED — Adversarial coverage added; claim appropriately scoped |
| **MC-TC-004 change** | None — MC-TC-004 adds 103 targeted tests beyond the existing 362 Trust Core tests |
| **004 status** | **RESOLVED** — Test coverage expanded with verification evidence and conflict detection tests. The claim remains appropriately scoped: tests demonstrate consistent behavior, not absolute proof. |

---

## Summary

| ID | Description | 003F Status | 004 Status | Change |
|----|-------------|-------------|------------|--------|
| FG-01 | execution_id propagation | RESOLVED | RESOLVED | — |
| FG-02 | verification_state authoritative | RESOLVED | RESOLVED | ↑ STRENGTHENED |
| FG-03 | execution_state transitions | RESOLVED | RESOLVED | — |
| FG-04 | Events enriched with identity | RESOLVED | RESOLVED | — |
| FG-05 | store_receipt preserves mode | RESOLVED | RESOLVED | — |
| FG-06 | Causation chain maintained | RESOLVED | RESOLVED | — |
| FG-07 | Receipt proves execution | STILL ACCEPTABLE | STILL ACCEPTABLE | — |
| FG-08 | Verification independence | STILL ACCEPTABLE | STILL ACCEPTABLE | — |
| FG-09 | Simulation vs Real distinguishable | RESOLVED | RESOLVED | — |
| FG-10 | EventStore append authoritative | PARTIALLY RESOLVED | **PARTIALLY RESOLVED** | ↑ IMPROVED |
| FG-11 | Tests prove correctness | RESOLVED | RESOLVED | — |

### Key Findings

1. **No new false guarantees introduced.** All 11 remain in the same or better state.
2. **FG-02 (verification_state authoritative) STRENGTHENED** — evidence requirement added via S-03.
3. **FG-10 (EventStore authoritative) IMPROVED** — conflict detection added via S-04.
4. **No guarantee regressed** from MC-TC-003F to MC-TC-004.

**Proceeding to adversarial revalidation.**
