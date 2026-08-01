# MC-TC-004 — Certification Report

---

## Meta

| Field | Value |
|-------|-------|
| **Phase** | MC-TC-004 |
| **Purpose** | Trust Core hardening — dead code removal, replay distinction, evidence binding, conflict detection |
| **Pre-gate decision** | GO (MC-TC-004_ARCHITECTURE_REVIEW_DECISION.md) |
| **Implementation status** | COMPLETE (MC-TC-004_IMPLEMENTATION_REPORT.md) |
| **Certification review date** | 2026-07-30 |
| **Reviewing body** | Architecture Review Board (ARB) |

---

## Scope Review

### Authorized Scope (4 items)

| ID | Item | Status |
|----|------|--------|
| S-01 | Remove dead claim/evidence code (EventIdentity, ProvenanceTag, enrich_with_claim_boundary, EVENT_IDENTITY_VERSION) | ✅ IMPLEMENTED |
| S-02 | Add `is_replayed` schema column to `stored_events` | ✅ IMPLEMENTED |
| S-03 | Evidence requirement for verification (`set_verification("verified")` requires `evidence_receipt_id`) | ✅ IMPLEMENTED |
| S-04 | Verification conflict detection (atomic check in `store_verification()`) | ✅ IMPLEMENTED |

### Scope Deviations

All 4 items implemented exactly per scope proposal. The `receipt_id` column
added during S-03 is an implementation detail of the evidence requirement,
not a scope deviation.

---

## Acceptance Criteria Satisfaction

### S-01: 7/7 criteria met (100%)

| # | Criterion | Evidence | Verdict |
|---|-----------|----------|---------|
| AC-01 | EventIdentity class removed | Grep: 0 matches | ✅ |
| AC-02 | ProvenanceTag enum removed | Grep: 0 matches | ✅ |
| AC-03 | enrich_with_claim_boundary removed | Grep: 0 matches | ✅ |
| AC-04 | Removed from `__init__.py` | Direct inspection | ✅ |
| AC-05 | No production imports | Full-repo grep | ✅ |
| AC-06 | No test imports | Full-repo grep | ✅ |
| AC-07 | All tests pass | 431/431 Trust Core pass | ✅ |

### S-02: 7/7 criteria met (100%)

| # | Criterion | Evidence | Verdict |
|---|-----------|----------|---------|
| AC-01 | Column exists in schema | `event_store.py:65` | ✅ |
| AC-02 | append() sets is_replayed=0 | `event_store.py:112` default | ✅ |
| AC-03 | ReplayService sets is_replayed=1 | `replay_service.py:110` | ✅ |
| AC-04 | _row_to_dict includes is_replayed | `event_store.py:387` | ✅ |
| AC-05 | Legacy events default to 0 | `event_store.py:295-297` migration | ✅ |
| AC-06 | _replayed marker backward compat | `event_store.py:94-95` | ✅ |
| AC-07 | All tests pass | 431/431 Trust Core pass | ✅ |

### S-03: 8/8 criteria met (100%)

| # | Criterion | Evidence | Verdict |
|---|-----------|----------|---------|
| AC-01 | set_verification("verified") without evidence raises | `execution_context.py:165-168` | ✅ |
| AC-02 | set_verification("verified") with evidence succeeds | `test_phase3e_remediation.py:267-268` | ✅ |
| AC-03 | set_verification("failed") without evidence succeeds | Idempotent behavior verified | ✅ |
| AC-04 | set_verification("unverified") without evidence succeeds | Idempotent behavior verified | ✅ |
| AC-05 | All callers pass evidence_receipt_id | `orchestrator.py:167,169` | ✅ |
| AC-06 | store_verification produces event with receipt_id | `event_store.py:265` | ✅ |
| EvidenceRequiredError defined | Exception class | `event_store.py:17-18` | ✅ |
| No regression | 431/431 Trust Core pass | ✅ |

### S-04: 7/7 criteria met (100%)

| # | Criterion | Evidence | Verdict |
|---|-----------|----------|---------|
| AC-01 | First verification succeeds | `event_store.py:214-269` | ✅ |
| AC-02 | Same-status second verification succeeds | Conflict check skips same status | ✅ |
| AC-03 | Conflicting status raises VerificationConflictError | `event_store.py:225-230` | ✅ |
| AC-04 | Per-execution_id conflict scope | `event_store.py:217` WHERE clause | ✅ |
| AC-05 | Backward compatible | Migration path | ✅ |
| AC-06 | All tests pass | 431/431 Trust Core pass | ✅ |
| VerificationConflictError defined | Exception class | `event_store.py:13-14` | ✅ |

### System: 4/4 criteria met (100%)

| # | Criterion | Evidence | Verdict |
|---|-----------|----------|---------|
| AC-SYS-01 | No Trust Core regressions | 431/431 pass | ✅ |
| AC-SYS-02 | No new P0/P1 findings | 0 CONTRADICTED invariants | ✅ |
| AC-SYS-03 | Identity continuity | All identity tests pass | ✅ |
| AC-SYS-04 | Append-only preserved | No UPDATE/DELETE in EventStore | ✅ |

---

## Certification Evidence Reviewed

| Document | ARB Finding |
|----------|-------------|
| MC-TC-004_IMPLEMENTATION_REPORT.md | 21 sections, all verified | ✅ |
| MC-TC-004_REQUIREMENT_TRACEABILITY_MATRIX.md | 33/33 requirements traced | ✅ |
| MC-TC-004_INVARIANT_REAUDIT.md | 14/16 ENFORCED, 0 CONTRADICTED | ✅ |
| MC-TC-004_FALSE_GUARANTEE_REAUDIT.md | 0 regressions, FG-02/FG-10 strengthened | ✅ |
| MC-TC-004_ADVERSARIAL_REVALIDATION.md | A-012/A-018 MITIGATED, 8 STILL POSSIBLE | ✅ |
| MC-TC-004_SECURITY_REVALIDATION.md | Mitigations structurally sound | ✅ |
| MC-TC-004_REGRESSION_FINAL_REPORT.md | 0 Trust Core regressions | ✅ |
| Source code: execution_context.py | S-01 removal, S-03 evidence guard | ✅ |
| Source code: event_store.py | S-02 schema, S-03 evidence, S-04 conflict | ✅ |
| Source code: replay_service.py | S-02 is_replayed flag | ✅ |
| Source code: orchestrator.py | S-03 evidence passthrough | ✅ |
| Test: test_phase3b_trust_core.py | 56/56 pass | ✅ |
| Test: test_phase3d_adversarial.py | 18/18 pass (A-012/A-018 covered) | ✅ |
| Test: test_phase3e_remediation.py | 37/37 pass (all evidence+conflict cases) | ✅ |

---

## Key Metrics

| Metric | Pre-MC-TC-004 | Post-MC-TC-004 | Change |
|--------|---------------|----------------|--------|
| Invariants ENFORCED | 12/16 (75%) | 14/16 (87.5%) | +12.5% |
| Invariants CONTRADICTED | 0 | 0 | — |
| False guarantees regressed | — | 0 | — |
| Adversarial MITIGATED | 0/20 | 2/20 (A-012, A-018) | +2 |
| Adversarial STILL POSSIBLE | 10/20 | 8/20 | -2 |
| Trust Core tests passing | 362+ | 431 | +69 |
| Dead code technical debt | EventIdentity, ProvenanceTag, enrich_with_claim_boundary | Removed | Clean |
| Evidence binding | Advisory (payload) | Structural (schema column) | Upgraded |
| Verification conflict | Silent overwrite | VerificationConflictError | Upgraded |
| Replay distinction | Payload marker only | Schema column + payload fallback | Upgraded |

---

## Residual Risks

All acknowledged and documented:

1. **First-verification race window** — two concurrent `store_verification()` calls
   for same execution_id with no prior verification could both pass the conflict check.
   Mitigation requires UNIQUE constraint or two-phase insert. Severity: LOW.

2. **`object.__setattr__` bypass** — direct Python attribute mutation can bypass
   property guards. Requires deliberate low-level introspection. Severity: LOW.

3. **8 STILL POSSIBLE adversarial scenarios** — all architectural scope boundaries.
   Severity: VARIES. Deferred.

4. **ReplayService is_replayed bug** — service could fail to set flag. The `_replayed`
   payload marker fallback still works. Severity: LOW.

---

## Certification Status: PENDING ARB DECISION
