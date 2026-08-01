# MC-TC-004 — Adversarial Residual Risk Analysis

---

## Purpose

Analyze all adversarial scenarios classified as STILL POSSIBLE after MC-TC-003F
to determine:
1. Whether any can **silently create false authoritative state**
2. The severity of each residual risk
3. Whether any should block MC-TC-004

---

## Note on Discrepancy

The MC-TC-003F Architecture Re-Gating Decision document states "6/20 adversarial scenarios
remain possible" but the accompanying status table shows 10 scenarios as STILL POSSIBLE
(A-001 through A-006, A-012, A-014, A-017, A-018). This discrepancy exists because the
text count excludes 4 scenarios (A-003, A-004, A-012, A-017) that were already marked
CONFIRMED in 003D and were never claimed to be resolved by 003E remediation. For this
analysis, all 10 are evaluated.

---

## Residual Risk Analysis

### A-001: False Agent Claim

| Dimension | Assessment |
|-----------|------------|
| **Current behavior** | `enrich_with_claim_boundary()` sets `_provenance_source="agent"` and `_is_claim=True` as advisory metadata on events from agent claims. No enforcement — claim events are processed identically to real events through all normal paths. |
| **Can create false authoritative state?** | **YES** — if an EventStore replay consumer does not check `_is_claim`, claim events are indistinguishable from evidence events at the persistence layer. A consumer that replays all events for an execution_id would see claim and evidence interleaved with no differentiation. |
| **Severity** | MEDIUM — consumers that check `_is_claim` are safe; consumers that don't may treat claims as fact. The advisory marker pattern relies on consumer discipline. |
| **Status** | ARCHITECTURAL SCOPE BOUNDARY — the claim/evidence boundary is intentionally advisory in the current architecture. True enforcement requires semantic understanding of what constitutes evidence vs claim, which is beyond the scope of MC-TC-004. |

### A-002: Fake Tool Success

| Dimension | Assessment |
|-----------|------------|
| **Current behavior** | `store_receipt()` accepts any receipt-like object with `to_dict()` method. No validation that the receipt corresponds to an actual `UTR.execute()` call. Execution_id uniqueness prevents duplicate execution_ids but does not validate authenticity. |
| **Can create false authoritative state?** | **YES** — a forged receipt with `success=True` would be stored as `execution.receipt` with `execution_state="completed"` and appear identical to a legitimate receipt at the persistence layer. |
| **Severity** | HIGH — forged receipts can falsely mark executions as completed/verified. |
| **Status** | ARCHITECTURAL SCOPE BOUNDARY — receipt authenticity requires the UTR to be a trusted subsystem. In the current in-process architecture, any code can construct a receipt object. True authenticity requires either: (a) UTR as a separate authenticated service, or (b) cryptographic signing of receipts. |

### A-003: Tool Invocation Without Execution

| Dimension | Assessment |
|-----------|------------|
| **Current behavior** | `EXECUTION_STARTED` fires at the start of `kernel.run()`, BEFORE any tool invocation. The state machine does not enforce `running → completed` at the kernel level. An `EXECUTION_STARTED` event does not prove any tool executed. |
| **Can create false authoritative state?** | **NO** — the missing completion/del events would be detectable. No false terminal state can be created. The system can detect "started but never completed" by querying for orphan `EXECUTION_STARTED` events without corresponding `EXECUTION_FINISHED` events. |
| **Severity** | MEDIUM — the scenario creates orphan events, not false state. Detection is possible post-hoc. |
| **Status** | ACCEPTABLE — per-step execution tracking is a feature enhancement, not a correctness requirement for MC-TC-004. |

### A-004: Partial Execution

| Dimension | Assessment |
|-----------|------------|
| **Current behavior** | All tools in a plan share the same execution context. `KernelResult.success` is set by `_is_success(mel_result)`. If crash prevents pipeline from reaching `KernelResult`, no result is returned. No per-step execution tracking. |
| **Can create false authoritative state?** | **NO** — partial execution with crash produces no terminal state. The missing completion is detectable. If partial execution does complete (some steps succeed, some fail), the result accurately reflects partial failure. |
| **Severity** | MEDIUM — no false state, but loss of per-step granularity. |
| **Status** | ACCEPTABLE — per-step execution tracking is a feature enhancement for MC-TC-004 or later. |

### A-005: Crash After External Mutation

| Dimension | Assessment |
|-----------|------------|
| **Current behavior** | No atomicity between `UTR.execute()` (which may mutate external state) and `EventStore.append()` (which persists the event). A crash in the window between them creates external state without corresponding MUSCAL evidence. |
| **Can create false authoritative state?** | **NO** — MUSCAL's authoritative state would show the execution as incomplete (missing completion event). The external state would be inconsistent with MUSCAL state, but MUSCAL's own state would be correct (the event was never persisted). |
| **Severity** | HIGH (external inconsistency) — from MUSCAL's perspective, the execution was attempted but no result was recorded. From the external system's perspective, changes were made. This creates a reconciliation problem, but not false MUSCAL state. |
| **Status** | ACCEPTABLE — atomic persistence requires infrastructure changes (e.g., transactional outbox pattern, two-phase commit, or saga pattern) that are beyond MC-TC-004 scope. |

### A-006: Event Forged

| Dimension | Assessment |
|-----------|------------|
| **Current behavior** | `EventStore.append()` accepts any event with any `execution_id`, `topic`, `payload`. No authentication. No authorization. No validation that the caller is allowed to produce events for the given execution_id. The only constraint is `execution_id` required for execution-required topics (P1-F05). |
| **Can create false authoritative state?** | **YES** — a direct `event_store.append()` call can create any event indistinguishable from real events. Forged `EXECUTION_FINISHED`, `TOOL_EXECUTED`, `VERIFICATION_PASSED`, `execution.receipt`, and `execution.verification` events all possible. All would appear identical to legitimate events in replay queries. **This is the highest risk residual scenario.** |
| **Severity** | **CRITICAL** — but classified as architectural scope boundary, not a remediation defect (see EventStore Trust Boundary Analysis, Phase 4). |
| **Status** | ARCHITECTURAL SCOPE BOUNDARY — EventStore authentication requires architectural transition from in-process to authenticated IPC/service architecture. This is deferred to future security hardening phase, not MC-TC-004. |

### A-012: Verification Without Evidence

| Dimension | Assessment |
|-----------|------------|
| **Current behavior** | `set_verification("verified")` can be called at any time on any `ExecutionContext`. No check that evidence (receipt, verification result) exists. Property guards (P0-C03) prevent direct field assignment but do not enforce evidence requirement. |
| **Can create false authoritative state?** | **YES** — an execution can be marked `VERIFIED` with no supporting evidence. The `execution.verification` event in EventStore would show the verification status, but there would be no corresponding `execution.receipt` event or evidence payload. |
| **Severity** | HIGH — verification without evidence undermines the trust model. However, verification is an opt-in process — no component is forced to verify, and no component is forced to verify only with evidence. |
| **Status** | ACCEPTABLE — evidence-required verification is a policy decision. Adding evidence enforcement would require changes to the verification flow (e.g., `set_verification` requires a receipt_id, or `store_verification` checks for receipt existence). This is a candidate for MC-TC-004 scope. |

### A-014: External Reality Assumption

| Dimension | Assessment |
|-----------|------------|
| **Current behavior** | MUSCAL records `TOOL_EXECUTED` with `success=True` based on tool self-report. No automatic ground-truth verification after execution. Verification (if triggered) may independently check external state, but this is opt-in, not wired by default. |
| **Can create false authoritative state?** | **NO** — MUSCAL records are internally consistent: "tool reported success" is a fact about what the tool returned. MUSCAL does not claim "external state was modified". The authoritative state is about MUSCAL events, not external reality. |
| **Severity** | MEDIUM — from a semantic perspective, "tool said it worked" does not mean "it worked". But MUSCAL does not conflate these. |
| **Status** | ACCEPTABLE — ground-truth external verification is outside MUSCAL's scope for MC-TC-004. It is a policy/application-level concern, not an architecture correctness concern. |

### A-017: Out-of-Order Event

| Dimension | Assessment |
|-----------|------------|
| **Current behavior** | EventStore has no causal ordering constraints. Events are appended in arrival order. `EXECUTION_COMPLETED` can be stored before `EXECUTION_STARTED`. Consumers may see events in any order. |
| **Can create false authoritative state?** | **NO** — both events exist in EventStore. The consumer is responsible for ordering. The authoritative state (all events that occurred) is complete. Order is a consumer interpretation concern. |
| **Severity** | LOW — causal ordering affects interpretation, not completeness. |
| **Status** | ACCEPTABLE — causal ordering enforcement requires distributed coordination (Lamport clocks, vector clocks, or sequencer) that is beyond MC-TC-004 scope. |

### A-018: Verification Race

| Dimension | Assessment |
|-----------|------------|
| **Current behavior** | EventStore accepts both `VERIFICATION_PASSED` and `VERIFICATION_FAILED` for the same `execution_id`. No conflict detection. "Last write wins" by append order. The final `verification_state` in EventStore reflects whichever verification was stored last. |
| **Can create false authoritative state?** | **YES** — if verifier A writes `VERIFICATION_PASSED` and verifier B writes `VERIFICATION_FAILED`, the final state (last append) determines the authoritative state. The conflict is not automatically detected. A consumer querying by `execution_id` might see only one verification status if they only check the latest event. |
| **Severity** | MEDIUM — the conflict is detectable by inspecting all events for the execution_id (both verification events are present). But consumers that only check the latest event would see an incomplete picture. |
| **Status** | CANDIDATE for MC-TC-004 — conflict detection (raising an error or quarantining conflicting verifications) is a reasonable scope item for MC-TC-004. |

---

## Summary Table

| ID | Scenario | False Authoritative State? | Severity | Recommended Action |
|----|----------|---------------------------|----------|-------------------|
| A-001 | False Agent Claim | YES — unchecked consumers | MEDIUM | Document consumer guidance; no code change |
| A-002 | Fake Tool Success | YES — forged receipts | HIGH | Defer to future authenticated UTR |
| A-003 | Tool Invocation Without Execution | NO | MEDIUM | Detectable via orphan query; no action |
| A-004 | Partial Execution | NO | MEDIUM | No false state; no action |
| A-005 | Crash After External Mutation | NO (external inconsistency) | HIGH | Defer to transactional outbox pattern |
| A-006 | Event Forged | YES — any event | CRITICAL | Defer to authenticated EventStore |
| A-012 | Verification Without Evidence | YES — verification with no evidence | HIGH | **Candidate for MC-TC-004** |
| A-014 | External Reality Assumption | NO | MEDIUM | Opt-in policy; no action |
| A-017 | Out-of-Order Event | NO | LOW | No action |
| A-018 | Verification Race | YES — last-write-wins | MEDIUM | **Candidate for MC-TC-004** |

---

## Risk Severity Distribution

- **CRITICAL** (creates false authoritative state): 1 scenario (A-006)
- **HIGH** (creates false authoritative state): 2 scenarios (A-002, A-012)
- **HIGH** (external inconsistency only): 1 scenario (A-005)
- **MEDIUM**: 5 scenarios (A-001, A-003, A-004, A-014, A-018)
- **LOW**: 1 scenario (A-017)

---

## Blocking Assessment

### Would any scenario block MC-TC-004?

**NO.** The criteria for blocking MC-TC-004 would be:

1. **New P0/P1 finding discovered:** None of these scenarios are new findings. All were known and documented in MC-TC-003D. None were claimed to be resolved by MC-TC-003E remediation.
2. **Design shows fundamental flaw:** The remaining scenarios are architectural scope boundaries (A-001, A-002, A-005, A-006) or feature gaps (A-003, A-004, A-012, A-014, A-017, A-018). Neither constitutes a fundamental design flaw.
3. **Worse after remediation than before:** All scenarios are in the same or better state than at 003D. No regression has been introduced.

### Special note on A-006 (Event Forged)

A-006 is classified as **CRITICAL** severity for creating false authoritative state, but it is an **architectural scope boundary**, not a remediation defect. The current architecture is in-process single-tenant. True EventStore authentication requires a multi-process or service architecture. Blocking MC-TC-004 on A-006 would mean blocking all future development until MUSCAL transitions to authenticated IPC — which is circular, because such a transition would itself be a major implementation phase.

**Recommendation:** A-006 is accepted by design for the current architecture phase. It should be revisited when MUSCAL moves to multi-process/tenant architecture.

---

## MC-TC-004 Scope Candidates

Two scenarios are identified as reasonable scope items for MC-TC-004:

1. **A-012 (Verification Without Evidence):** Add evidence requirement to `store_verification()` or `set_verification()` — require a receipt_id or evidence payload before allowing `VERIFIED` state.
2. **A-018 (Verification Race):** Add conflict detection to EventStore — detect when two verifications exist for the same execution_id with conflicting status, and either raise an error or quarantine the second.

Neither is mandatory for MC-TC-004 to proceed, but both represent meaningful improvements to the trust model within the current architecture constraints.

---

## Conclusion

**No residual adversarial scenario blocks MC-TC-004.** All 10 STILL POSSIBLE scenarios are either:
- Architectural scope boundaries (deferred to future phase)
- Feature enhancements (not correctness defects)
- Detectable via existing mechanisms

The Trust Core is architecturally ready for MC-TC-004 implementation.
