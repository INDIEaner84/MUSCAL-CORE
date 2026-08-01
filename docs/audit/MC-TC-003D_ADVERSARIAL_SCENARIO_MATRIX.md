# MC-TC-003D — Adversarial Scenario Matrix

---

## A-001 — False Agent Execution Claim

- **Scenario:** Agent says "Tool X executed successfully" but no tool invocation occurred.
- **Attack:** Agent hallucinates or lies about execution.
- **Expected Behavior:** System should detect no evidence exists.
- **Actual Behavior:** Agent claim is captured as a claim marker (`_is_claim=True`) but NO enforcement exists. The claim can be processed identically to real execution evidence.
- **Detection:** `_provenance_source="agent"` — advisory only.
- **Prevention:** None — claim markers are metadata only.
- **Recovery:** No mechanism.
- **Severity:** HIGH
- **Status:** CONFIRMED VULNERABLE

---

## A-002 — Fake Tool Success

- **Scenario:** Agent receives `success=True` but tool never executed.
- **Attack:** Tool runtime returns forged success.
- **Expected Behavior:** Integrity hash should detect receipt tampering.
- **Actual Behavior:** If the receipt is constructed (not from actual UTR.execute()), there is no mechanism to distinguish forged from real. UTR dedup by execution_id prevents duplicate execution_ids but does not validate authenticity.
- **Detection:** No authenticity validation on execution_ids.
- **Prevention:** None for forged receipts.
- **Recovery:** None.
- **Severity:** HIGH
- **Status:** CONFIRMED VULNERABLE

---

## A-003 — Tool Invocation Without Execution

- **Scenario:** Tool invoked but runtime crashed before actual execution.
- **Attack:** Event claims tool was invoked but no execution occurred.
- **Expected Behavior:** System must distinguish REQUESTED ≠ INVOKED ≠ EXECUTED.
- **Actual Behavior:** `EXECUTION_STARTED` fires at the START of `kernel.run()`, BEFORE any tool is invoked. This event does NOT prove execution occurred. The graph may show the started event without any corresponding completion.
- **Detection:** State machine transition running → completed is not enforced at the kernel level.
- **Prevention:** None — the system must infer from presence/absence of completion events.
- **Recovery:** EventStore replay can recover events, but cannot prove execution.
- **Severity:** MEDIUM
- **Status:** CONFIRMED — architecture treats REQUESTED as semantically distinct but enforcement is advisory.

---

## A-004 — Partial Execution

- **Scenario:** Multi-step execution: Step 1 success, Step 2 success, Step 3 crash, Step 4 never executed.
- **Attack:** System may incorrectly reach COMPLETED.
- **Expected Behavior:** COMPLETED should only be set when ALL steps complete.
- **Actual Behavior:** `KernelResult.success` is set by `_is_success(mel_result)` which checks tool results. If the pipeline continues after a tool failure, success may be False. But if crash prevents pipeline from reaching `KernelResult` at all, no result is returned.
- **Detection:** State machine prevents completed → running, but partial execution before crash leaves no transition record.
- **Prevention:** Each tool step should independently record its state. Currently, all tools in a plan share the same execution context.
- **Recovery:** None.
- **Severity:** MEDIUM
- **Status:** PARTIALLY ADDRESSED — execution state per execution, not per tool step.

---

## A-005 — Runtime Crash After External Mutation

- **Scenario:** Tool modifies external system, MUSCAL crashes, result event never persisted.
- **Attack:** External mutation is invisible to MUSCAL.
- **Expected Behavior:** Execution result must be atomically tied to event persistence.
- **Actual Behavior:** No atomicity. Window between tool return (UTR.execute()) and event persistence (EventStore.append()) can lose evidence on crash.
- **Detection:** Missing completion event for known execution_id.
- **Prevention:** None — not atomic.
- **Recovery:** None for lost evidence. Replay cannot recover what was never persisted.
- **Severity:** HIGH
- **Status:** CONFIRMED VULNERABLE

---

## A-006 — Event Persisted Without Actual Execution

- **Scenario:** Event claims TOOL_EXECUTED but no tool invocation happened.
- **Attack:** Direct EventStore.append() call with forged event.
- **Expected Behavior:** System must prevent false execution events.
- **Actual Behavior:** `EventStore.append()` accepts any event with any execution_id. No validation that execution_id corresponds to a real execution. No authenticity check.
- **Detection:** No detection mechanism exists.
- **Prevention:** None — EventStore is append-only but not authenticated.
- **Recovery:** None.
- **Severity:** CRITICAL
- **Status:** CONFIRMED VULNERABLE — FALSE EXECUTION EVENT POSSIBLE

---

## A-007 — Simulation Leakage

- **Scenario:** Simulated execution events become indistinguishable from real.
- **Attack:** Simulation events replayed or consumed as real.
- **Expected Behavior:** SIMULATED ≠ REAL at all levels.
- **Actual Behavior:** Events are differentiated only by the `execution_mode` field in EventStore. No segregation, no access control, no mode-based filtering at replay. Consumers must manually check `execution_mode`.
- **Detection:** Check `execution_mode` field.
- **Prevention:** EventStore has no mode-based access control.
- **Recovery:** Replay with mode filter (consumer responsibility).
- **Severity:** MEDIUM
- **Status:** CONFIRMED — mode field exists but enforcement is consumer-side only.

---

## A-008 — Identity Regeneration

- **Scenario:** Child component generates new execution_id.
- **Attack:** Identity fragmentation — two identity chains for one logical execution.
- **Expected Behavior:** Single identity chain per execution.
- **Actual Behavior:** CRITICAL: EnrichedMuscalOS generates execution_id=A, MuscalOS generates execution_id=B. They are never reconciled.
- **Detection:** No detection — the two identities are never cross-referenced.
- **Prevention:** None currently.
- **Recovery:** None — events are scattered across two identity chains.
- **Severity:** CRITICAL (P0)
- **Status:** CONFIRMED VULNERABLE — Double Identity (P0-C01)

---

## A-009 — Broken Causation Chain

- **Scenario:** Event C has incorrect or missing causation_id.
- **Attack:** Causal chain broken.
- **Expected Behavior:** Causation chain must be validatable.
- **Actual Behavior:** EventStore accepts events with empty, missing, or incorrect causation_id without validation. `store_receipt` sets causation_id to the receipt's OWN receipt_id (backwards).
- **Detection:** No automatic validation.
- **Prevention:** No schema-level enforcement.
- **Recovery:** Manual inspection only.
- **Severity:** HIGH (P1-F04)
- **Status:** CONFIRMED VULNERABLE

---

## A-010 — Unauthorized Verification

- **Scenario:** Component sets verification_state=VERIFIED without legitimate verifier.
- **Attack:** Direct dataclass field mutation.
- **Expected Behavior:** Verification authority must be enforced.
- **Actual Behavior:** `verification_state` is a plain `@dataclass` field. Any code can set it directly. `set_verification()` exists but is entirely opt-in.
- **Detection:** No detection — direct mutation leaves no audit trail.
- **Prevention:** None — field is unprotected.
- **Recovery:** None — forged verification is indistinguishable from legitimate.
- **Severity:** CRITICAL (P0-C03)
- **Status:** CONFIRMED VULNERABLE

---

## A-011 — Replay Masquerading as New Execution

- **Scenario:** Historical events replayed and interpreted as new execution.
- **Attack:** Replay injection.
- **Expected Behavior:** Replay must be distinguishable from new execution.
- **Actual Behavior:** EventStore has `_replayed=True` marker in payload. ReplayService sets this marker. EventStore rejects events with `_replayed=True` (returns None from append). However, this is an opt-in marker — not enforced at schema level.
- **Detection:** `_replayed` flag.
- **Prevention:** EventStore.append() rejects events with `_replayed=True`.
- **Recovery:** N/A — prevention works.
- **Severity:** MEDIUM
- **Status:** ADDRESSED — marker-based prevention exists, but relies on consistent use.

---

## A-012 — Verification Without Evidence

- **Scenario:** Execution marked VERIFIED but no evidence exists.
- **Attack:** State transition without evidence.
- **Expected Behavior:** Verification must have supporting evidence.
- **Actual Behavior:** `set_verification("verified")` can be called at any time on any ExecutionContext. No requirement that an ExecutionReceipt exists.
- **Detection:** No automatic check.
- **Prevention:** None.
- **Recovery:** None.
- **Severity:** HIGH
- **Status:** CONFIRMED VULNERABLE

---

## A-013 — Evidence Without Execution (Orphan)

- **Scenario:** Evidence exists but cannot be linked to a valid execution.
- **Attack:** Receipt for non-existent execution.
- **Expected Behavior:** Orphan evidence must be rejected or quarantined.
- **Actual Behavior:** EventStore accepts receipts/verifications for any execution_id, including non-existent ones.
- **Detection:** No validation on execution_id existence.
- **Prevention:** None.
- **Recovery:** None.
- **Severity:** HIGH (P1-F05)
- **Status:** CONFIRMED VULNERABLE

---

## A-014 — External Reality Assumption

- **Scenario:** MUSCAL records EXECUTED but external system never changed.
- **Attack:** Tool self-report differs from reality.
- **Expected Behavior:** EXECUTED must not automatically imply EXTERNAL_WORLD_CHANGED.
- **Actual Behavior:** No ground-truth verification after execution. System trusts tool's success flag. Verification (if triggered) may independently check if expected state exists, but this is opt-in.
- **Detection:** Only if verification is explicitly triggered.
- **Prevention:** Automatic verification is not wired by default.
- **Recovery:** Verification can detect, but cannot recover.
- **Severity:** MEDIUM
- **Status:** CONFIRMED — system trusts tool self-report.

---

## A-015 — Concurrent Execution Collision

- **Scenario:** Two executions run concurrently.
- **Attack:** ID collision, cross-contamination, state corruption.
- **Expected Behavior:** IDs must be unique, contexts isolated.
- **Actual Behavior:** UUID v7 provides unique IDs (tested: 1000 generated without collision). Thread-local ExecutionContextManager isolates contexts per thread. EventBus callbacks are synchronous, so no async cross-contamination.
- **Detection:** N/A — functions correctly for synchronous dispatch.
- **Prevention:** UUID v7 for uniqueness, thread-local for isolation.
- **Recovery:** N/A
- **Severity:** LOW
- **Status:** SAFE for synchronous dispatch. Risk if async subscribers added.

---

## A-016 — Duplicate Event

- **Scenario:** Same event delivered twice.
- **Attack:** Double persistence, double state mutation.
- **Expected Behavior:** Idempotent or rejected.
- **Actual Behavior:** EventStore has `event_id UNIQUE` constraint. Duplicate event_id raises `IntegrityError`. The `EventBus` itself has no dedup — duplicates can be published.
- **Detection:** SQLite UNIQUE constraint catches duplicates at persistence layer.
- **Prevention:** UNIQUE constraint on event_id at schema level.
- **Recovery:** IntegrityError is raised, caller must handle.
- **Severity:** LOW
- **Status:** ADDRESSED — EventStore UNIQUE constraint prevents double persistence.

---

## A-017 — Out-of-Order Event

- **Scenario:** Event B arrives before Event A.
- **Attack:** Causal violation.
- **Expected Behavior:** Causal ordering must be enforced or validated.
- **Actual Behavior:** EventStore has NO causal ordering constraints. EXECUTION_COMPLETED can be stored before EXECUTION_STARTED. Consumers must handle out-of-order events.
- **Detection:** Timestamp comparison (consumer responsibility).
- **Prevention:** None — EventStore appends in arrival order.
- **Recovery:** Consumer must validate causal ordering post-hoc.
- **Severity:** MEDIUM
- **Status:** CONFIRMED — no causal ordering enforcement.

---

## A-018 — Verification Race

- **Scenario:** Two verifiers produce conflicting results.
- **Attack:** VERIFIED vs FAILED for same execution.
- **Expected Behavior:** Conflict must be detected and represented.
- **Actual Behavior:** EventStore accepts both VERIFICATION_PASSED and VERIFICATION_FAILED for the same execution_id. No conflict detection. "Last write wins" by append order.
- **Detection:** No automatic detection.
- **Prevention:** None.
- **Recovery:** Manual inspection of event history.
- **Severity:** MEDIUM
- **Status:** CONFIRMED — conflicting verifications accepted.

---

## A-019 — State Transition Bypass

- **Scenario:** Direct field mutation bypassing validated transitions.
- **Attack:** Set execution_state or verification_state directly.
- **Expected Behavior:** State transitions must go through validated path.
- **Actual Behavior:** Plain dataclass fields allow direct mutation. `transition_state()` and `set_verification()` are opt-in.
- **Detection:** No detection — direct mutation leaves no audit trail.
- **Prevention:** None — fields are unprotected.
- **Recovery:** None.
- **Severity:** CRITICAL (P0-C03)
- **Status:** CONFIRMED VULNERABLE

---

## A-020 — Provenance Truncation

- **Scenario:** Event persisted without complete identity fields.
- **Attack:** Execution_id, causation_id, correlation_id missing.
- **Expected Behavior:** Event with incomplete provenance must be rejected or marked.
- **Actual Behavior:** EventStore accepts events with empty execution_id, correlation_id, causation_id. Default empty strings.
- **Detection:** No automatic detection.
- **Prevention:** No NOT NULL constraints on identity fields (defaults to '').
- **Recovery:** Manual inspection only.
- **Severity:** MEDIUM
- **Status:** CONFIRMED — incomplete provenance events accepted.
