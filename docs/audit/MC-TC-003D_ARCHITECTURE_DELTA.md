# MC-TC-003D — Architecture Delta

---

## Comparison: MC-TC-003A → MC-TC-003B → MC-TC-003D Review

| Aspect | MC-TC-003A (Approved) | MC-TC-003B (Implemented) | MC-TC-003D (Review) | Classification |
|--------|----------------------|--------------------------|---------------------|----------------|
| execution_id generation | Single point in kernel.run() | Generated in kernel.run() and muscal_os.run() | Double generation — EnrichedMuscalOS + MuscalOS conflict | CONTRADICTION (P0-C01) |
| execution_id propagation | Propagated to all events | kernel.py propagates via ctx, graph.py via add_node | Default persistence path drops identity (P0-C02) | CONTRADICTION (P0-C02) |
| Identity fields on Node | Node has execution_id | schema.py:Node.execution_id added | ENFORCED — field exists and is propagated | STRENGTHENED |
| State machine validation | Transition paths enforced | transition_state(), set_verification() implemented | Direct field mutation bypasses all validation (P0-C03) | WEAKENED |
| EventStore identity columns | 6 identity columns | All 6 columns exist + migration | Columns exist but default _persist_to_store doesn't populate them | WEAKENED |
| store_receipt mode handling | Use receipt's execution_mode | Hardcoded 'real' | Same as MC-TC-003B — not fixed | DEFERRED (P1-F02) |
| store_verification mode handling | Use verification's execution_mode | Hardcoded 'real' | Same as MC-TC-003B — not fixed | DEFERRED (P1-F03) |
| Causation direction in store_receipt | causation_id = execution_id of cause | causation_id = receipt's own receipt_id | Backwards — receipt points to itself | NEW GAP (P1-F04) |
| EventBus event_id | UUID v7 | Format string `{topic}_{counter}_{ts}` | Not UUID — cannot provide distributed uniqueness | WEAKENED (P1-F01) |
| Claim/evidence markers | Enforced semantic boundary | enrich_with_claim_boundary() creates advisory markers | Markers exist but have ZERO downstream enforcement | WEAKENED |
| Verification authority | Enforced verifier requirement | No enforcement — plain field mutation allowed | No change from MC-TC-003B | DEFERRED (P0-C03) |
| Orphan event rejection | Reject events for non-existent executions | No validation — all events accepted | No change from MC-TC-003B | NEW GAP (P1-F05) |
| Concurrency isolation | Thread-safe context | Thread-local ExecutionContextManager | Safe for synchronous dispatch. Async risk undocumented | CONFIRMED |
| Duplicate event detection | Idempotent | event_id UNIQUE constraint | ENFORCED — UNIQUE constraint works | STRENGTHENED |
| MC-TC-003A docs in repo | Must be present | NOT WRITTEN TO DISK | All MC-TC-003A documents missing from docs/audit/ | CONTRADICTION |
| Adversarial test coverage | Required before MC-TC-004 | Not written | 18 adversarial tests written, 8 vulnerabilities found | NEW GAP (now covered) |

---

## Classification Summary

| Classification | Count | Items |
|----------------|-------|-------|
| CONFIRMED | 2 | Concurrency isolation, duplicate detection |
| STRENGTHENED | 3 | Identity fields on Node, EventStore identity columns, duplicate detection |
| WEAKENED | 3 | State machine validation, EventBus event_id, EventStore identity propagation, claim markers |
| NEW GAP | 3 | Causation direction, orphan event acceptance, adversarial test coverage |
| CONTRADICTION | 3 | Double identity, identity propagation, MC-TC-003A docs missing |
| DEFERRED | 3 | store_receipt mode, store_verification mode, verification authority |

---

## MC-TC-003A Document Gap

**Finding:** None of the MC-TC-003A architecture documents exist in `docs/audit/`.

The following were declared as MC-TC-003A deliverables but are MISSING:

- MC-TC-003A_CONTRADICTION_RESOLUTION_REPORT.md ✗
- MC-TC-003A_TRUST_CORE_IDENTITY_MODEL.md ✗
- MC-TC-003A_EXECUTION_STATE_MACHINE.md ✗
- MC-TC-003A_CANONICAL_EVENT_CONTRACT.md ✗
- MC-TC-003A_EVIDENCE_CONTRACT.md ✗
- MC-TC-003A_VERIFICATION_CONTRACT.md ✗
- MC-TC-003A_EVENT_STORE_MIGRATION_PLAN.md ✗
- MC-TC-003A_ADR_PACKAGE.md ✗
- MC-TC-003A_ADVERSARIAL_REVIEW.md ✗
- MC-TC-003A_TEST_SPECIFICATION.md ✗
- MC-TC-003B_IMPLEMENTATION_REPORT.md ✗
- MC-TC-003B_IDENTITY_WIRING_MAP.md ✗
- MC-TC-003B_STATE_TRANSITION_AUDIT.md ✗
- MC-TC-003B_TRUST_SEMANTICS_TEST_REPORT.md ✗
- MC-TC-003B_ARCHITECTURE_DELTA.md ✗

**Impact:** The MC-TC-003B implementation was written without auditable approved architecture documents. This is a CI/governance violation.
