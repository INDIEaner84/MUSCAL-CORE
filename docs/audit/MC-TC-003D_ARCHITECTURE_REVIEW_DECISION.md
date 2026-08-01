# MC-TC-003D — Architecture Review Decision

---

## Final Decision

```
╔══════════════════════════════════════════════╗
║ MC-TC-003D ARCHITECTURE REVIEW                ║
╚══════════════════════════════════════════════╝

ARCHITECTURE STATUS:
APPROVED WITH CONDITIONS

TRUST BOUNDARY:
PARTIAL

EXECUTION TRUTH:
FAIL

IDENTITY:
PARTIAL

PROVENANCE:
PARTIAL

EVIDENCE:
PARTIAL

VERIFICATION:
FAIL

REPLAY SAFETY:
PASS

ADVERSARIAL RESILIENCE:
FAIL

CRITICAL FINDINGS:
3

P0 CONTRADICTIONS:
3

P1 FINDINGS:
5

FALSE GUARANTEES:
11

MC-TC-004:
CONDITIONAL

NEXT ACTION:
Resolve P0-C01, P0-C02, P0-C03 before MC-TC-004 implementation
```

---

## Conditions for MC-TC-004 Authorization

MC-TC-004 is **CONDITIONALLY AUTHORIZED**. The following conditions must be satisfied before MC-TC-004 implementation can begin:

### Condition 1: Fix Double Identity (P0-C01)
`EnrichedMuscalOS.run()` must pass its `ExecutionContext` to `MuscalOS.run()`. This requires:
- Adding a parameter to `MuscalOS.run()` that accepts an `ExecutionContext` (or at minimum an `execution_id`)
- `EnrichedMuscalOS.run()` must pass its context rather than generating one in `MuscalOS.run()`
- Verify that a single execution produces exactly one `execution_id` across all abstraction layers

### Condition 2: Fix Default Identity Persistence (P0-C02)
`MuscalOS._persist_to_store()` must extract `execution_id`, `correlation_id`, `causation_id`, `execution_mode`, `execution_state`, and `verification_state` from the message and pass them to `EventStore.append()`. This requires:
- Extracting identity fields from `msg.payload` (where `enrich_with_context()` places them)
- Or reading from the transaction-local `ExecutionContext` (via `get_context_manager()`)
- The default persistence path must carry identity, not just the enriched path

### Condition 3: Protect State Fields (P0-C03)
Make `execution_state` and `verification_state` immutable via direct mutation. Options:
- Convert `ExecutionContext` from `@dataclass` to a class with `@property` setters that route through validation
- Or add write-once semantics (freeze after creation, allow mutation only via methods)
- Or use a private backing field with validated property setters

### Condition 4: Fix EventBus ID Generation (P1-F01)
Change `event_bus.py:51` from `f"{topic}_{len(self._history)}_{int(time.time() * 1000)}"` to `uuid7()`.

### Condition 5: Fix store_receipt/store_verification mode propagation (P1-F02, P1-F03)
Use the receipt/verification object's `execution_mode` instead of hardcoded `'real'`.

### Condition 6: Fix causation direction in store_receipt (P1-F04)
Set `causation_id` to the execution that caused the receipt, not the receipt's own id.

### Condition 7: Add MC-TC-003A documents to repository
All approved architecture documents must be committed to `docs/audit/` before MC-TC-004 begins.

---

## Rationale

The architecture is approved with conditions rather than blocked because:

1. **The design concepts are sound:** The 3D state machine, UUID v7 identity, state transition validation, EventStore architecture, and claim/evidence boundary are all correctly designed. The issues are in the **implementation** and **enforcement**, not the model.

2. **The P0 issues are fixable:** Double identity is a wiring defect (not passing context). Identity persistence is a missing field extraction. State protection is a dataclass-to-property conversion. None require architectural redesign.

3. **The adversarial resilience can be achieved:** The architecture CAN distinguish claims from execution — it just doesn't enforce the distinction today. Adding enforcement is feasible within the existing design.

4. **MC-TC-004 scope (Evidence + Verification) depends on identity integrity:** Before adding evidence and verification layers, the identity layer must be trustworthy. The three P0 conditions must be met to ensure MC-TC-004 builds on a solid foundation.

---

## Risk Acceptance

The following risks are ACCEPTED for MC-TC-004, provided the P0 conditions are met:

- P1-F01 (non-UUID event IDs) — acceptable if EventStore remains local
- P1-F05 (orphan events) — acceptable for MC-TC-004 but must be addressed before MC-TC-005
- Claim markers as advisory — acceptable for MC-TC-004, must be enforced in MC-TC-005

---

## Signature

This decision is based on:
- Source code audit of 13 files
- 18 adversarial tests executed
- 11 false guarantees documented
- 16 invariants audited
- L0-L10 trust boundary matrix completed
- 20 adversarial scenarios analyzed

**MC-TC-003D — APPROVED WITH CONDITIONS**
**MC-TC-004 — CONDITIONAL (7 conditions above)**
