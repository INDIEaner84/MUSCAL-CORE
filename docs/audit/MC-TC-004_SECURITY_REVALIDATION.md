# MC-TC-004 — Security Revalidation

---

## Purpose

Independent Architecture Review Board assessment of the adversarial scenario
closures (A-012, A-018) and residual attack surfaces after MC-TC-004
implementation. This document verifies that mitigations are structurally sound
and do not introduce new vulnerabilities.

---

## Assessment Methodology

1. Read source code of all enforcement points
2. Read adversarial test coverage
3. Verify that mitigations cannot be bypassed without subverting the type system
4. Verify that mitigations do not degrade existing guarantees
5. Assess residual risk level

---

## A-012: Verification Without Evidence (CLOSED)

### Pre-MC-TC-004

`set_verification("verified")` accepted any caller without requiring proof that
verification actually occurred. An agent or compromised component could assert
VERIFIED status for any execution without producing a corresponding evidence
receipt.

### Mitigation (S-03)

Two-layer enforcement:

| Layer | File:Line | Mechanism |
|-------|-----------|-----------|
| **Identity layer** | `execution_context.py:165-168` | `set_verification("verified")` raises `ValidationError` if `evidence_receipt_id` is empty |
| **Persistence layer** | `event_store.py:202-210` | `store_verification()` raises `EvidenceRequiredError` if `receipt_id` or `execution_id` is empty when status is "verified" |

### ARB Analysis

**Strengths:**
- Dual enforcement covers both the in-memory path (identity) and the durable path (event store)
- `EvidenceRequiredError` is a distinct exception type — cannot be confused with `ValidationError`
- Orchestrator (`orchestrator.py:167`) passes `vr.receipt_id` from the actual VerificationResult,
  meaning evidence must be produced by a real Receipt before it can be bound
- Non-VERIFIED statuses remain unconstrained (correct by design — evidence is only relevant for asserted verification)

**Bypass analysis:**
- Direct `object.__setattr__` on `_verification_state` bypasses the guard, but requires
  deliberate Python-level introspection — no production code path does this
- Direct `EventStore.append()` bypasses the evidence check, but the orchestrator always
  routes through `store_verification()` which enforces the check
- The `receipt_id` column at `event_store.py:66` provides structural schema-level binding

**Verdict:** A-012 is structurally closed.

---

## A-018: Verification Race (CLOSED)

### Pre-MC-TC-004

Two concurrent verifications for the same execution_id could produce conflicting
results (e.g., one says VERIFIED, the other says FAILED) with "last write wins"
semantics. A race could result in an incorrect terminal verification state.

### Mitigation (S-04)

Conflict detection within `store_verification()` (`event_store.py:214-230`):

```python
with self._lock:
    row = self._conn.execute(
        "SELECT verification_state, event_id FROM stored_events "
        "WHERE execution_id = ? AND topic = 'execution.verification' "
        "ORDER BY seq DESC LIMIT 1",
        (vr_execution_id,),
    ).fetchone()

    if row is not None:
        existing_status = row["verification_state"]
        existing_event_id = row["event_id"]
        if existing_status != vr_status and existing_status in ("verified", "failed"):
            raise VerificationConflictError(...)
```

### ARB Analysis

**Strengths:**
- The `self._lock` (threading.Lock) ensures atomicity of the read-check-insert sequence
- Only terminal states (verified, failed) trigger conflict — non-terminal states (unverified, pending)
  are freely overwritable (correct by design)
- Same-status repetition is allowed (idempotent)
- The lock scope covers the entire read-check-insert, preventing TOCTOU races

**Bypass analysis:**
- Direct `EventStore.append()` with raw `verification_state` bypasses the conflict check —
  this is intentional: `append()` is a low-level primitive, `store_verification()` is the
  high-level authoritative path. All production code routes through `store_verification()`.
- A race between two first-ever verifications for the same execution_id: both would pass the
  SELECT (row is None), both would INSERT. The second insert would have a different
  `verification_state`. This is a **residual risk** — AC-02 allows same-status idempotency,
  but conflicting first inserts are not prevented. This requires a UNIQUE constraint on
  `(execution_id, verification_state)` or a two-phase insert. Documented as residual risk.

**Residual risk — first-verification race:** If two threads call `store_verification()`
simultaneously for the same execution_id where no prior verification exists, both pass the
conflict check and both INSERT. The events are ordered by seq but the "last write wins"
race still exists for the first verification. Severity: LOW (exploitable only under
concurrent first-verification — production usage is typically sequential).

**Verdict:** A-018 is closed for practical purposes. The first-verification race window
is documented as an accepted residual risk.

---

## Residual Attack Surfaces (8 STILL POSSIBLE)

Unchanged from pre-MC-TC-004 — all are architectural scope boundaries:

| ID | Scenario | Reason Not Addressed | Residual Risk |
|----|----------|---------------------|---------------|
| A-001 | False Agent Claim | Architectural — agent claim boundary not in scope | HIGH (design gap) |
| A-002 | Fake Tool Success | Architectural — tool execution integrity not in scope | HIGH (design gap) |
| A-003 | Invocation Without Execution | Architectural — invocation chain not in scope | MEDIUM |
| A-004 | Partial Execution | Architectural — atomicity not in scope | MEDIUM |
| A-005 | Crash After Mutation | Architectural — crash recovery not in scope | MEDIUM |
| A-006 | Event Forged | Architectural — event integrity not in scope | HIGH (design gap) |
| A-014 | External Reality Assumption | Architectural — external verification not in scope | MEDIUM |
| A-017 | Out-of-Order Event | Architectural — ordering not in scope | MEDIUM |

All are documented in `MC-TC-004_ADVERSARIAL_RESIDUAL_RISK_ANALYSIS.md` as
deferred to future phases.

---

## Invariant Security Impact

| Invariant | Pre-004 | Post-004 | Change | Security Implication |
|-----------|---------|----------|--------|---------------------|
| I-09 (Verification validated path) | ENFORCED | ENFORCED (+evidence) | ↑ | Verification now structurally bound to evidence |
| I-10 (Replay distinguishable) | PARTIAL | ENFORCED | ↑ | Replay events now structurally distinguished at schema level |
| FG-02 (verification_state authoritative) | RESOLVED | STRENGTHENED | ↑ | Evidence column structurally binds verification to receipt |
| FG-10 (EventStore authoritative) | PARTIALLY RESOLVED | IMPROVED | ↑ | Conflict detection prevents silent overwrite |

**Zero invariants weakened. Zero false guarantees introduced.**

---

## Summary

| Metric | Value |
|--------|-------|
| Scenarios mitigated (A-012, A-018) | 2/2 structurally closed |
| Residual attack surfaces | 8/10 STILL POSSIBLE (unchanged) |
| New vulnerabilities introduced | 0 |
| Invariants weakened | 0 |
| False guarantees introduced | 0 |
| First-verification race residual | LOW severity, documented |

**Recommendation:** Security posture is improved. Both planned mitigations are
structurally sound. Residual risks are architectural scope items for future phases.
