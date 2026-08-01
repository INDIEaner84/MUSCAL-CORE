# MC-TC-004 — Scope Proposal

---

## Purpose

Define the minimal implementation scope for MC-TC-004 based on the findings
of all 7 pre-gate analysis phases.

---

## Current State

After MC-TC-003F certification:
- **All P0/P1 findings independently verified resolved**
- **12/16 invariants ENFORCED** (up from 6/16 at 003D)
- **Zero invariants CONTRADICTED or WEAKENED**
- **10/20 adversarial scenarios remain STILL POSSIBLE** — all architectural scope
  boundaries or feature gaps, not correctness defects
- **Trust Core is minimally sound** — only dead code identified (claim/evidence API)
- **EventStore trust model acceptable** for in-process single-tenant architecture
- **Governance gap is NON-BLOCKING**
- **18 pre-existing test failures are TRULY UNRELATED** to Trust Core

---

## Scope Principles

1. **Minimal** — only what is necessary for the next implementation phase
2. **Verified** — each item must have clear acceptance criteria
3. **Self-contained** — no dependency on deferred items
4. **No scope creep** — anything that requires architectural change is deferred

---

## MC-TC-004 Scope Items

### S-01: Remove or wire dead claim/evidence code (HIGH)

| Dimension | Detail |
|-----------|--------|
| **Source** | Phase 7 — Minimality Review, Finding M-01 |
| **Files** | `features/identity/execution_context.py:262-316` |
| **Current** | `EventIdentity`, `ProvenanceTag`, `enrich_with_claim_boundary` are defined and exported but never used by any production or test code |
| **Action** | Either: (a) **Remove** — delete the dead code and its exports, or (b) **Wire** — integrate into EventBus publish path or EventStore append path so claim events are structurally distinct |
| **Recommendation** | **Remove** — the claim/evidence boundary is an architectural scope boundary (Phase 5, A-001). Wiring it without enforcement would create the same advisory pattern. Removal is cleaner. |
| **Effort** | Low — ~50 lines of dead code + exports |

### S-02: Add `is_replayed` schema column (MEDIUM)

| Dimension | Detail |
|-----------|--------|
| **Source** | Phase 6 — Invariant Closure Plan, I-10 |
| **Files** | `runtime/event_store.py` (schema + append + _row_to_dict) |
| **Current** | Replay distinction relies on `_replayed=True` payload marker — opt-in, not structural |
| **Action** | Add `is_replayed BOOLEAN NOT NULL DEFAULT 0` column to `stored_events` schema. ReplayService sets `is_replayed=1` in event dict for append(). EventStore maps column in _row_to_dict. |
| **Effort** | Low — schema migration + append path change + replay path change |

### S-03: Add evidence requirement to verification (MEDIUM)

| Dimension | Detail |
|-----------|--------|
| **Source** | Phase 5 — Adversarial Residual Analysis, A-012 |
| **Files** | `runtime/event_store.py:store_verification()` or `execution_context.py:set_verification()` or both |
| **Current** | `set_verification("verified")` can be called with no supporting evidence. `store_verification()` accepts verification without checking that a receipt exists. |
| **Action** | Option A: `set_verification()` requires a `receipt_id` parameter — verification cannot succeed without referencing a receipt. Option B: `store_verification()` checks that an `execution.receipt` event exists for the same execution_id before storing `VERIFICATION_PASSED`. |
| **Recommendation** | **Option A** — simpler, no DB query per verification. `set_verification(target, evidence_receipt_id=None)` — if target is "verified", receipt_id is required. |
| **Effort** | Medium — method signature change + validation logic + test updates |

### S-04: Add verification conflict detection (LOW)

| Dimension | Detail |
|-----------|--------|
| **Source** | Phase 5 — Adversarial Residual Analysis, A-018 |
| **Files** | `runtime/event_store.py:store_verification()` |
| **Current** | Two verifications (PASSED and FAILED) for same execution_id are both accepted. Last-write-wins. |
| **Action** | Before storing a verification, check if a verification for the same execution_id already exists. If the new verification conflicts with the existing one, raise `VerificationConflictError`. |
| **Effort** | Medium — DB query per verification + error handling + consumer guidance |

---

## Scope Summary

| ID | Item | Priority | Effort | Type |
|----|------|----------|--------|------|
| S-01 | Remove dead claim/evidence code | HIGH | Low | Cleanup |
| S-02 | Add `is_replayed` schema column | MEDIUM | Low | Hardening |
| S-03 | Evidence requirement for verification | MEDIUM | Medium | Hardening |
| S-04 | Verification conflict detection | LOW | Medium | Hardening |

---

## Out of Scope (Deferred)

| Item | Reason | Target Phase |
|------|--------|-------------|
| EventStore authentication | Requires architectural change to multi-process/service | Future security hardening |
| Per-step execution tracking (A-003, A-004) | Feature enhancement, not correctness | MC-TC-005 or later |
| Atomic tool execution + persistence (A-005) | Requires transactional outbox pattern | MC-TC-005 or later |
| Causal ordering (A-017) | Requires distributed coordination | Future |
| Ground-truth verification (A-014) | Policy/application-level concern | Future |
| execution_id UNIQUE constraint (I-01) | Probabilistic uniqueness sufficient | Future schema migration |
| Correlation isolation (I-06) | Advisory grouping field — no enforcement needed | N/A |
| Causation referential integrity (I-05 sub-gap) | Intentionally flexible | N/A |
| Governance docs (MC-TC-003A/003B) | Non-blocking — no MC-TC-004 dependency | Future governance phase |

---

## Implementation Order

1. **S-01** (dead code removal) — no risk, no dependency
2. **S-02** (is_replayed column) — no risk, no dependency
3. **S-03** (evidence requirement) — medium risk, validate with tests
4. **S-04** (conflict detection) — low risk, validate with tests

Each item is self-contained and can be implemented independently.
