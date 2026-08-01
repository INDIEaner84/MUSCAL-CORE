# MC-TC-004 — Architecture Review Board Decision

---

## Decision

```
============================================================
MC-TC-004 PRE-IMPLEMENTATION ARCHITECTURE GATE
============================================================

RESULT: GO — MC-TC-004 IS AUTHORIZED TO PROCEED
------------------------------------------------------------

CONDITIONS:
  - Implementation is limited to the 4 scope items defined in
    MC-TC-004_SCOPE_PROPOSAL.md (S-01 through S-04)
  - No architectural changes outside approved scope
  - All acceptance criteria must be met before MC-TC-004 close
  - This is a HARDENING phase, not a new feature phase
------------------------------------------------------------
```

---

## Pre-Gate Analysis Summary

| Phase | Document | Result |
|-------|----------|--------|
| Phase 1 | MC-TC-004_PRE_GATE_VERIFICATION.md | **PASS** — all 003F claims verified against source code |
| Phase 2 | MC-TC-004_GOVERNANCE_GAP_ASSESSMENT.md | **NON-BLOCKING** — missing docs don't affect MC-TC-004 decisions |
| Phase 3 | MC-TC-004_FAILURE_DEBT_CLASSIFICATION.md | **ALL CLEAR** — 18 failures classified as A. TRULY UNRELATED |
| Phase 4 | MC-TC-004_EVENTSTORE_TRUST_BOUNDARY.md | **ACCEPTED** — EventStore trust model acceptable for in-process architecture; authentication deferred |
| Phase 5 | MC-TC-004_ADVERSARIAL_RESIDUAL_RISK_ANALYSIS.md | **CLEAR** — zero blocking scenarios; 2 candidates for MC-TC-004 scope |
| Phase 6 | MC-TC-004_INVARIANT_CLOSURE_PLAN.md | **CLEAR** — 3 of 4 gaps accepted; 1 (I-10) added to scope |
| Phase 7 | MC-TC-004_TRUST_CORE_MINIMALITY_REVIEW.md | **CLEAR** — dead code identified; added to scope for removal |
| Phase 8 | MC-TC-004_SCOPE_PROPOSAL.md | **APPROVED** — 4 scope items defined |
| Phase 9 | MC-TC-004_ACCEPTANCE_CRITERIA.md | **APPROVED** — acceptance criteria defined for all scope items |

---

## Basis for Decision

### 1. MC-TC-003F Certification is Verified

All 7 MC-TC-003F artifacts have been independently spot-checked against source code:
- P0-C01 (Identity Regeneration) — **Verified**: ExecutionContext v2.1.0 with property guards
- P0-C02 (Enrichment Gap) — **Verified**: `_extract_identity()` propagates through all paths
- P0-C03 (State Mutation Protection) — **Verified**: property setters raise ValidationError
- P1-F01 (UUID Format) — **Verified**: uuid7 in EventBus event generation
- P1-F02/F03 (Mode Hardening) — **Verified**: mode correctly derived in store_receipt and store_verification
- P1-F04 (Causation Fix) — **Verified**: causation_id now points to correct parent
- P1-F05 (Orphan Prevention) — **Verified**: execution_id required for execution-required topics

### 2. Trust Core is Architecturally Sound

- 12/16 invariants now ENFORCED (up from 6/16 in 003D)
- Zero invariants CONTRADICTED or WEAKENED
- Identity continuity holds across all 14 execution boundaries
- Causation chain is correctly directed
- State transitions are protected by property guards
- Simulation mode is structurally distinct from real mode

### 3. Remaining Gaps are Managed

All identified gaps are either:
- **Architectural scope boundaries** (EventStore authentication, claim/evidence enforcement) — deferred to future phases
- **Feature enhancements** (per-step tracking, causal ordering) — not correctness defects
- **Acceptable by design** (probabilistic execution_id uniqueness, advisory correlation_id)

### 4. Test Debt is Classified

All 18 pre-existing test failures are classified as A. TRULY UNRELATED — none
reference Trust Core components. These do not block MC-TC-004.

### 5. Governance Gap is Non-Blocking

The absence of MC-TC-003A/003B architecture documents does not affect any
MC-TC-004 decision. Governance docs will be produced in a future governance phase.

---

## Authorized Scope

MC-TC-004 implementation is limited to:

| ID | Item | Priority | Effort |
|----|------|----------|--------|
| S-01 | Remove dead claim/evidence code (`EventIdentity`, `ProvenanceTag`, `enrich_with_claim_boundary`) | HIGH | Low |
| S-02 | Add `is_replayed BOOLEAN NOT NULL DEFAULT 0` schema column | MEDIUM | Low |
| S-03 | Add evidence requirement to `set_verification()` (`evidence_receipt_id` parameter required for "verified") | MEDIUM | Medium |
| S-04 | Add verification conflict detection in `store_verification()` | LOW | Medium |

**Total estimated effort:** 4 items, 2 low + 2 medium.

---

## Hard Rules

1. **No architectural changes** — MC-TC-004 must not change the fundamental in-process architecture
2. **No scope expansion** — only the 4 items above; anything else requires separate ARB review
3. **No automatic implementation** — each item must meet its acceptance criteria before close
4. **No regression** — all existing tests must continue to pass
5. **EventStore must remain append-only** — no UPDATE, DELETE, or mutation API added
6. **Execution identity must remain intact** — no weakening of property guards or propagation

---

## Veto Rights

Any ARB member may veto MC-TC-004 if:
1. A new P0/P1 finding is discovered during implementation
2. An existing invariant becomes WEAKENED or CONTRADICTED
3. The scope expands beyond the 4 approved items without re-review
4. A regression is introduced in Trust Core tests

Veto must be documented in writing with specific evidence.

---

## Signatures

```
------------------------------------------------------------
Architecture Review Board
MC-TC-004 Pre-Implementation Gate
Date: 2026-07-27
------------------------------------------------------------

Decision: GO — Authorized with Conditions

Prepared by: OpenCode Architecture Audit
Review basis: Independent verification of all 9 pre-gate phases
------------------------------------------------------------
```
