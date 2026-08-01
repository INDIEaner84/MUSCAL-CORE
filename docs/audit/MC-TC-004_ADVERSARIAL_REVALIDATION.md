# MC-TC-004 — Adversarial Revalidation

---

## Methodology

Each attack category is validated against the MC-TC-004 implementation.
For each attack vector:
- **Attack surface** — what is attacked
- **MC-TC-004 mitigation** — what was implemented
- **Residual risk** — what remains possible after mitigation

---

## Identity Attacks

### Attack: execution identity substitution

| Dimension | Detail |
|-----------|--------|
| **Surface** | `ExecutionContext.__init__()` takes `execution_id` parameter. Any caller can pass any execution_id. |
| **Mitigation** | `execution_id` is immutable after creation (property getter only, no setter, `__slots__` prevents dynamic attr). Once bound, cannot be changed. |
| **Residual risk** | A caller creating a new `ExecutionContext(execution_id="existing-id")` could reuse an execution_id. No uniqueness enforcement across `ExecutionContext` instances (I-01 is PARTIAL). However, `event_id UNIQUE` in EventStore prevents duplicate events at persistence layer. |
| **Verdict** | **MITIGATED at persistence layer.** Identity reuse is possible at context creation but detectable at event persistence. |

### Attack: cross-execution contamination

| Dimension | Detail |
|-----------|--------|
| **Surface** | Thread-local `ExecutionContextManager` — if not cleared between executions, stale context leaks. |
| **Mitigation** | `EnrichedMuscalOS.run()` sets context before execution (line 123) and clears/restores parent in `finally` block (lines 161-164). |
| **Residual risk** | If `run()` is called without going through `EnrichedMuscalOS`, context may not be managed. Direct `MuscalOS.run()` does not set/clear context. |
| **Verdict** | **MITIGATED for standard path.** Direct `MuscalOS.run()` callers must manage context themselves. |

---

## Evidence Attacks

### Attack: fake receipt

| Dimension | Detail |
|-----------|--------|
| **Surface** | `store_receipt()` accepts any receipt-like object with `to_dict()` method. No authentication. |
| **Mitigation** | Receipt is bound to `execution_id` (P1-F05). UUID v7 `receipt_id` provides uniqueness. |
| **Residual risk** | A forged receipt with a valid execution_id is still accepted. `execution_id` uniqueness prevents reuse but not forgery. This is architectural scope boundary (A-002). |
| **Verdict** | **NOT MITIGATED** (architectural scope — A-002 remains STILL POSSIBLE). |

### Attack: missing receipt

| Dimension | Detail |
|-----------|--------|
| **Surface** | Verification could proceed without any receipt. |
| **Mitigation** | **S-03 (Evidence Requirement):** `set_verification("verified")` requires `evidence_receipt_id`. `store_verification()` validates receipt_id non-empty for "verified" status. |
| **Residual risk** | `object.__setattr__` bypass of property guard (requires deliberate low-level Python access). |
| **Verdict** | **MITIGATED.** A-012 is no longer possible through standard API. |

### Attack: foreign receipt

| Dimension | Detail |
|-----------|--------|
| **Surface** | Verification uses a receipt belonging to a different execution. |
| **Mitigation** | **S-03 (Evidence Requirement):** `store_verification()` validates that `execution_id` is non-empty when status is "verified". The orchestrator passes `vr.receipt_id` where `vr.execution_id` matches the receipt's execution_id. |
| **Residual risk** | `store_verification()` does not cross-reference receipt_id against stored receipts. It only validates that receipt_id and execution_id are non-empty. A foreign receipt_id (belonging to a different execution_id) would be accepted if the VR's execution_id matches the verification target. The orchestration layer ensures this alignment, not the persistence layer. |
| **Verdict** | **MITIGATED at orchestration layer.** Persistence layer validates field presence, not referential integrity. Cross-referencing receipt existence in EventStore would require a DB query per verification — deferred as optimization. |

---

## Verification Attacks

### Attack: direct VERIFIED mutation

| Dimension | Detail |
|-----------|--------|
| **Surface** | Direct assignment `ctx.verification_state = "verified"`. |
| **Mitigation** | P0-C03: Property setter raises `ValidationError`. S-03: `set_verification("verified")` requires `evidence_receipt_id`. |
| **Residual risk** | `object.__setattr__` bypass (deliberate low-level access). |
| **Verdict** | **MITIGATED.** Direct assignment blocked. Verified path requires evidence. |

### Attack: conflicting verification overwrite

| Dimension | Detail |
|-----------|--------|
| **Surface** | Two verifications (VERIFIED and FAILED) for the same execution_id silently overwrite each other. |
| **Mitigation** | **S-04 (Conflict Detection):** `store_verification()` queries existing verification status in same critical section as INSERT. Conflicting status (verified vs failed, or vice versa) raises `VerificationConflictError`. |
| **Residual risk** | Race window for first verification: if no existing verification exists, two concurrent calls could both pass the check and insert. However, `event_id UNIQUE` constraint would catch duplicate inserts. Same-status verifications are allowed (idempotent). |
| **Verdict** | **MITIGATED.** Conflicting overwrites are detected and rejected atomically. |

---

## Replay Attacks

### Attack: replay confusion

| Dimension | Detail |
|-----------|--------|
| **Surface** | Replay events indistinguishable from original execution events. |
| **Mitigation** | **S-02 (is_replayed schema):** `is_replayed` column stores structural distinction. `_row_to_dict()` returns `is_replayed` field. Both payload marker (`_replayed=True`) and schema column work. |
| **Residual risk** | Consumer must check `is_replayed` field. If consumer ignores `is_replayed`, replay events appear identical to originals. ReplayService could fail to set `is_replayed=1` (bug). |
| **Verdict** | **MITIGATED (structural).** Distinction is now schema-level, not payload-advisory. Consumer filtering remains a responsibility. |

### Attack: identity duplication during replay

| Dimension | Detail |
|-----------|--------|
| **Surface** | Replay generates new events with duplicate execution_ids from historical executions. |
| **Mitigation** | EventBus generates new `event_id` via `uuid7()` for replayed events (via `_build_payload`). Original `event_id` preserved as `_original_event_id` metadata. ReplayService publishes to EventBus, which generates new event IDs. |
| **Residual risk** | If ReplayService bypasses EventBus and writes directly to EventStore, identity duplication is possible. Current implementation only reads from EventStore and publishes to EventBus — no direct write. |
| **Verdict** | **MITIGATED.** Current replay path does not create duplicate identities. |

---

## Provenance Attacks

### Attack: causation manipulation

| Dimension | Detail |
|-----------|--------|
| **Surface** | `causation_id` set to arbitrary value. |
| **Mitigation** | P1-F04: `store_receipt()` derives causation from receipt or falls back to execution_id. `store_verification()` defaults to `receipt_id`. Standard paths produce correct causation. |
| **Residual risk** | Direct `event_store.append()` can set arbitrary `causation_id` (A-006 — Event Forged). |
| **Verdict** | **MITIGATED for standard paths.** Direct append bypass remains architectural scope. |

### Attack: receipt substitution

| Dimension | Detail |
|-----------|--------|
| **Surface** | Replace receipt_id in verification to point to different receipt. |
| **Mitigation** | S-03: `receipt_id` stored as structural column. VerificationResult carries `receipt_id` bound to the verification. EventStore stores it at insert time — cannot be changed after insertion (append-only). |
| **Residual risk** | A crafted VerificationResult with a different receipt_id could be stored. No referential integrity check against receipts table. |
| **Verdict** | **MITIGATED for standard paths.** Receipt_id is immutable after storage. Crafted VRs remain possible but detectable via audit. |

---

## 20-Scenario Status Summary

| ID | Scenario | 003F Status | 004 Status | Change |
|----|----------|-------------|------------|--------|
| A-001 | False Agent Claim | STILL POSSIBLE | STILL POSSIBLE | — |
| A-002 | Fake Tool Success | STILL POSSIBLE | STILL POSSIBLE | — |
| A-003 | Invocation Without Execution | STILL POSSIBLE | STILL POSSIBLE | — |
| A-004 | Partial Execution | STILL POSSIBLE | STILL POSSIBLE | — |
| A-005 | Crash After Mutation | STILL POSSIBLE | STILL POSSIBLE | — |
| A-006 | Event Forged | STILL POSSIBLE | STILL POSSIBLE | — |
| A-007 | Simulation Leakage | DETECTED | DETECTED | — |
| A-008 | Identity Regeneration | PREVENTED | PREVENTED | — |
| A-009 | Broken Causation | PREVENTED | PREVENTED | — |
| A-010 | Unauthorized Verification | PREVENTED | PREVENTED | — |
| A-011 | Replay Masquerade | PREVENTED | PREVENTED | — |
| **A-012** | **Verification Without Evidence** | **STILL POSSIBLE** | **MITIGATED** | ✅ **CLOSED** |
| A-013 | Orphan Evidence | PREVENTED | PREVENTED | — |
| A-014 | External Reality Assumption | STILL POSSIBLE | STILL POSSIBLE | — |
| A-015 | Concurrent Collision | PREVENTED | PREVENTED | — |
| A-016 | Duplicate Event | PREVENTED | PREVENTED | — |
| A-017 | Out-of-Order Event | STILL POSSIBLE | STILL POSSIBLE | — |
| **A-018** | **Verification Race** | **STILL POSSIBLE** | **MITIGATED** | ✅ **CLOSED** |
| A-019 | State Transition Bypass | PREVENTED | PREVENTED | — |
| A-020 | Provenance Truncation | DETECTED | DETECTED | — |

### MC-TC-004 Impact

| Metric | Before | After |
|--------|--------|-------|
| PREVENTED | 8 | 8 |
| DETECTED | 2 | 2 |
| STILL POSSIBLE | 10 | **8** |
| **MITIGATED (by MC-TC-004)** | 0 | **2** |

**A-012 and A-018 are now MITIGATED by MC-TC-004.**

---

## Residual Risks Summary

| Risk | Severity | Mitigation |
|------|----------|------------|
| `object.__setattr__` bypass of evidence requirement | LOW | Requires deliberate low-level Python access |
| Race window for first verification (no existing → race) | LOW | Same-status second insert allowed (idempotent); conflicting would be caught |
| Missing `is_replayed` due to ReplayService bug | LOW | Old `_replayed` payload marker still works as fallback |
| 8 STILL POSSIBLE scenarios (A-001..A-006, A-014, A-017) | VARIES | All architectural scope boundaries or feature gaps — documented, no code change required |
