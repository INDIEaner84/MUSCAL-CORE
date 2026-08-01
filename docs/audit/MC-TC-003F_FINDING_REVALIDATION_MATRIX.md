# MC-TC-003F — Finding Revalidation Matrix

---

## P0-C01 — Double Identity

| Field | Detail |
|-------|--------|
| **Original vulnerability** | `EnrichedMuscalOS.run()` generated execution_id=A, delegated to `MuscalOS.run()` which generated execution_id=B. Two identity chains for one logical execution. |
| **Remediation** | `MuscalOS.run()` now accepts `execution_context` parameter (line 129). When supplied, uses that context rather than generating a new one. `EnrichedMuscalOS.run()` passes `execution_context=ctx` to `self._os.run()` (line 135). Additional: `get_context_manager().set_context(ctx)` ensures thread-local context is available to graph→EventBus enrichment (line 145). |
| **Independent verification** | Source inspection confirms `muscal_os.py:136-144` — only generates new ExecutionContext when `execution_context is None`. `enriched_bootstrap.py:134-135` — passes existing ctx. `test_phase3e_remediation.py:60-82` — verifies single identity across EventBus. All 6 identity tests pass. |
| **Residual risk** | If a caller constructs an `EnrichedMuscalOS` and calls `self._os.run()` directly (bypassing `EnrichedMuscalOS.run()`), the `EnrichedMuscalOS.run()` safeguard is bypassed. Direct `MuscalOS.run()` now has the same guard (accepts context), so risk is LOW. |
| **Status** | **RESOLVED** |

---

## P0-C02 — Default Persistence Dropped Identity

| Field | Detail |
|-------|--------|
| **Original vulnerability** | `_persist_to_store()` in `muscal_os.py` did not propagate `execution_id`, `correlation_id`, `causation_id` or any identity fields to EventStore persistence columns. |
| **Remediation** | `_persist_to_store()` now calls `_extract_identity(msg.payload)` which extracts identity from both flat payloads and nested graph event payloads. The extracted identity dict is unpacked into the EventStore.append() call via `**identity`. Additionally, `enrich_with_context()` is called in the graph→EventBus bridge handler to enrich events with the thread-local context's identity fields. |
| **Independent verification** | Source inspection confirms `muscal_os.py:_extract_identity` checks both `payload.get("execution_id")` and `payload.get("payload", {}).get("execution_id")` for nested graph format. `_persist_to_store` unpacks identity with `**identity`. Tests verify `execution_id`, `correlation_id`, `causation_id`, `execution_mode` all survive persistence. |
| **Residual risk** | `_extract_identity` silently defaults missing fields to empty strings or `"real"` — no alerting. Identity depends on `enrich_with_context` finding a thread-local context (which now is always set by `MuscalOS.run()` after fix). |
| **Status** | **RESOLVED** |

---

## P0-C03 — Direct State Mutation

| Field | Detail |
|-------|--------|
| **Original vulnerability** | `execution_state` and `verification_state` were plain `@dataclass` fields. Any code could set `ctx.verification_state = "verified"` bypassing all verification logic. |
| **Remediation** | ExecutionContext converted from `@dataclass` to manually-defined class with `__slots__`. `execution_state` and `verification_state` are `@property` with setters that raise `ValidationError` on direct assignment. Mutation only via `transition_state()` and `set_verification()` which use `object.__setattr__` for internal write access. |
| **Independent verification** | Adversarial test `test_execution_state_direct_mutation_rejected` confirms direct assignment raises `ValidationError`. Adversarial test `test_state_only_changes_through_authorized_methods` confirms `transition_state()` works. Remediation tests confirm valid/invalid transitions, verification via `set_verification()`, and terminal state protection. Source inspection confirms `orchestrator.py:167,169` uses `set_verification()`. |
| **Residual risk** | `object.__setattr__` can still bypass protection if used intentionally. `extract_from_payload` (static factory) uses `object.__setattr__` directly — this is intended for deserialization only. Any code with reference to the private attribute name (`_execution_state`) and `object.__setattr__` can bypass. This is a Python-level limitation — no runtime access control exists. |
| **Status** | **RESOLVED** |

---

## P1-F01 — EventBus UUID Identity

| Field | Detail |
|-------|--------|
| **Original vulnerability** | EventBus event IDs used format strings like `{topic}_{counter}_{timestamp}` which cannot provide distributed uniqueness and are predictable. |
| **Remediation** | `EventBus.publish()` now imports `uuid7()` lazily and generates `id=uuid7()` for every published event message. |
| **Independent verification** | Source inspection confirms `event_bus.py:46,52` — `from features.identity.uuid7 import uuid7` inside `publish()`, `id=uuid7()`. Remediation tests verify 100 unique IDs generated and `is_uuid7()` passes. Event ID is distinct from execution ID (separate fields). |
| **Residual risk** | uuid7 provides probabilistic uniqueness (not cryptographic like uuid4). UUID v7 is time-ordered and predictable in principle (millisecond precision + random suffix). Acceptable for non-security event identity. |
| **Status** | **RESOLVED** |

---

## P1-F02 / P1-F03 — Execution Mode Hardcoded in Receipt/Verification

| Field | Detail |
|-------|--------|
| **Original vulnerability** | `store_receipt()` and `store_verification()` hardcoded `execution_mode='real'` regardless of the actual execution mode. |
| **Remediation** | `store_receipt()` now derives `execution_mode` from `getattr(receipt, "execution_mode", "")`. `store_verification()` derives from `getattr(vr, "execution_mode", "")`. Both log a warning when missing and default to `"real"`. |
| **Independent verification** | Source inspection confirms `runtime/event_store.py:128-133` — `receipt_mode = getattr(receipt, "execution_mode", "")` → warning → `"real"` fallback. Same pattern at lines 153-158 for verification. Remediation tests verify simulated and proposed modes preserved. |
| **Residual risk** | Warning + fallback to `"real"` when mode is missing — silently treats untyped receipts as real. Could mask incomplete identity wiring. |
| **Status** | **RESOLVED** |

---

## P1-F04 — Causation Direction Reversed

| Field | Detail |
|-------|--------|
| **Original vulnerability** | `store_receipt()` set `causation_id` to the receipt's OWN receipt_id (backwards causation). The child pointed to itself. |
| **Remediation** | `store_receipt()` now: `receipt_causation = getattr(receipt, "causation_id", "") or receipt_eid`. Falls back to `execution_id` when receipt has no own causation. `store_verification()`: `vr_causation = getattr(vr, "causation_id", "") or getattr(vr, "receipt_id", "")`. Verification causation defaults to the receipt_id (the evidence that caused the verification). |
| **Independent verification** | Source inspection confirms `runtime/event_store.py:127` — `causation_id` derived from receipt's own `causation_id` or execution_id. `store_verification.py:159` — `causation_id` from verification's own or receipt_id. Remediation tests confirm `causation_id != receipt_id` and verification causation defaults to receipt_id. |
| **Residual risk** | Heuristic fallback may be incorrect when both `causation_id` and `execution_id`/`receipt_id` are empty or incorrect. No cross-validation exists. |
| **Status** | **RESOLVED** |

---

## P1-F05 — Orphan Event Protection

| Field | Detail |
|-------|--------|
| **Original vulnerability** | EventStore accepted execution-required events (EXECUTION_STARTED, TOOL_EXECUTED, execution.receipt, etc.) without any `execution_id`. |
| **Remediation** | `EventStore.append()` checks `topic in _EXECUTION_REQUIRED_TOPICS` and raises `ValueError` when `execution_id` is empty. Non-execution topics (boot.init, health.*, os.started) are still allowed without execution_id. |
| **Independent verification** | Source inspection confirms `runtime/event_store.py:11-22` — `_EXECUTION_REQUIRED_TOPICS` frozenset contains 9 topics. Line 82-86 — validation before insert. Remediation tests verify: rejection for EXECUTION_STARTED without execution_id, rejection for execution.receipt without execution_id, rejection for VERIFICATION_PASSED without execution_id, acceptance when execution_id present, and acceptance for boot.init without execution_id. |
| **Residual risk** | Validation checks for empty string only. Malformed execution_ids (non-empty but invalid) are accepted — no cross-reference to ExecutionContext Manager. "Orphan" execution_ids (valid format but no corresponding execution context) are accepted. The enforcement is syntactic (field present), not semantic (execution exists). |
| **Status** | **RESOLVED** |

---

## Summary

| Finding | Status | Residual Risk Level |
|---------|--------|-------------------|
| P0-C01 | RESOLVED | LOW |
| P0-C02 | RESOLVED | LOW |
| P0-C03 | RESOLVED | MEDIUM |
| P1-F01 | RESOLVED | LOW |
| P1-F02/F03 | RESOLVED | LOW |
| P1-F04 | RESOLVED | LOW |
| P1-F05 | RESOLVED | MEDIUM |

All 7 P0/P1 findings independently verified as resolved.
No finding requires reversal or re-classification.
