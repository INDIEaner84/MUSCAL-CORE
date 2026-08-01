# MC-TC-004 — Acceptance Criteria

---

## Purpose

Define specific, measurable, verifiable acceptance criteria for each MC-TC-004
scope item. Each criterion must be satisfiable by a test or inspection.

---

## S-01: Remove dead claim/evidence code

### Acceptance Criteria

| # | Criterion | Verification Method | Pass Condition |
|---|-----------|-------------------|----------------|
| AC-01 | `EventIdentity` class removed | Grep for `class EventIdentity` in `features/identity/` | Not found |
| AC-02 | `ProvenanceTag` enum removed | Grep for `class ProvenanceTag` in `features/identity/` | Not found |
| AC-03 | `enrich_with_claim_boundary` function removed | Grep for `def enrich_with_claim_boundary` in `features/identity/` | Not found |
| AC-04 | `EventIdentity`, `ProvenanceTag`, `enrich_with_claim_boundary` removed from `__init__.py` exports | Inspect `features/identity/__init__.py` | Not in `__all__` |
| AC-05 | No import of removed symbols in any production file | `grep -r "EventIdentity\|ProvenanceTag\|enrich_with_claim_boundary" --include="*.py"` excluding removed source | Zero matches |
| AC-06 | No import of removed symbols in any test file | Same grep across test files | Zero matches |
| AC-07 | All existing tests still pass | Run full Trust Core test suite | 362+ tests pass |

---

## S-02: Add `is_replayed` schema column

### Acceptance Criteria

| # | Criterion | Verification Method | Pass Condition |
|---|-----------|-------------------|----------------|
| AC-01 | `stored_events` table has `is_replayed INTEGER NOT NULL DEFAULT 0` column | `PRAGMA table_info(stored_events)` in EventStore | Column exists |
| AC-02 | Normal `append()` sets `is_replayed=0` | Append a normal event, replay it, check `is_replayed` field | `is_replayed == 0` |
| AC-03 | ReplayService append sets `is_replayed=1` | Trigger ReplayService, check `is_replayed` field in stored event | `is_replayed == 1` |
| AC-04 | `_row_to_dict()` includes `is_replayed` in output | Replay an event, inspect returned dict | `"is_replayed"` key present with correct value |
| AC-05 | Existing events without `is_replayed` default to 0 | Migration on existing DB | Legacy events return `is_replayed=0` |
| AC-06 | `_replayed` payload marker still works (backward compat) | Append with `_replayed=True` in payload (old ReplayService) | Returns None (suppressed) |
| AC-07 | All existing tests still pass | Run full Trust Core test suite | 362+ tests pass |

---

## S-03: Evidence requirement for verification

### Acceptance Criteria

| # | Criterion | Verification Method | Pass Condition |
|---|-----------|-------------------|----------------|
| AC-01 | `set_verification("verified")` without evidence_receipt_id raises `ValidationError` | Call `set_verification("verified")` on ExecutionContext | `ValidationError` raised |
| AC-02 | `set_verification("verified")` with valid evidence_receipt_id succeeds | Call `set_verification("verified", evidence_receipt_id="abc-123")` on ExecutionContext | `verification_state == "verified"` |
| AC-03 | `set_verification("failed")` without evidence_receipt_id succeeds (no evidence requirement for failure) | Call `set_verification("failed")` on ExecutionContext | `verification_state == "failed"` |
| AC-04 | `set_verification("unverified")` without evidence_receipt_id succeeds | Call `set_verification("unverified")` on ExecutionContext | `verification_state == "unverified"` |
| AC-05 | Existing `set_verification()` callers updated to pass evidence_receipt_id | Grep for `set_verification` in production code | All callers updated |
| AC-06 | `store_verification()` produces event with evidence_* fields (optional) | Store a verification, replay event | Event contains evidence info |

---

## S-04: Verification conflict detection

### Acceptance Criteria

| # | Criterion | Verification Method | Pass Condition |
|---|-----------|-------------------|----------------|
| AC-01 | First verification for an execution_id succeeds | Call `store_verification()` with `status="verified"` for a new execution_id | Event stored, no error |
| AC-02 | Second verification with same status for same execution_id succeeds (idempotent) | Call `store_verification()` again with `status="verified"` for same execution_id | Event stored, no error |
| AC-03 | Second verification with conflicting status raises `VerificationConflictError` | Call `store_verification()` with `status="failed"` for same execution_id after "verified" | `VerificationConflictError` raised |
| AC-04 | Conflict detection is per-execution_id, not global | Call conflicting verifications for different execution_ids | No cross-contamination |
| AC-05 | Backward compatible — existing verifications not affected | Run with existing DB containing verifications | No errors on existing data |
| AC-06 | All existing tests still pass | Run full Trust Core test suite | 362+ tests pass |

---

## System-Level Acceptance Criteria

| # | Criterion | Verification Method | Pass Condition |
|---|-----------|-------------------|----------------|
| AC-SYS-01 | No regressions in Trust Core scope | Compare test results before and after MC-TC-004 | Exactly same pass/fail (excluding new tests) |
| AC-SYS-02 | No new P0/P1 findings introduced | Architecture re-audit of changed files | Zero new P0/P1 findings |
| AC-SYS-03 | Identity continuity still holds across all 14 execution boundaries | Run identity continuity tests | All pass |
| AC-SYS-04 | EventStore append-only property preserved | Verify no UPDATE/DELETE added to EventStore API | Append-only API unchanged |

---

## Test Requirements

| Requirement | Detail |
|-------------|--------|
| **Each acceptance criterion must have a test** | Test or inspection script per AC |
| **New tests must use existing test patterns** | Follow `test_phase3d_identity.py` or similar |
| **All existing tests must continue to pass** | No regressions |
| **Test suite must run in CI** | Automated execution |
