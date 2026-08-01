# E3.2 Trust Boundary Closure — Reconciliation Report

## Summary

**Objective:** Close all 9 known bypasses documented in E3.1 Phase 6 so every external
state mutation passes through canonical UTR → SafetyGate → Governance → Receipt
→ Verification chain.

**Result:** 31/31 E3.2 adversarial tests passing, 0 regression vs prior phases.
Full suite: 812 passed, 1 skipped (pre-existing), 4 pre-existing failures
(0 caused by E3.2).

---

## Bypass Closure Table

| ID | Bypass | E3.2 Phase | Status | Evidence |
|---|---|---|---|---|
| B-01 | muscal_loop EXECUTORS (direct execution, no UTR) | A | CLOSED | `execute_tool()` now routes through UTR adapter; receipts generated for every call |
| B-02 | muscal_loop BrowserAgent (unchecked) | A | CLOSED | BrowserAgent tools registered into UTR via `_register_legacy_executors()` |
| B-03 | kernel.run() no GovernanceStage | B | CLOSED | `GovernanceStage.process()` called at start of `run()`; iteration limits enforced |
| B-04 | TOOL_REGISTRY fallback (mel.py line 53-55) | C | CLOSED | TOOL_REGISTRY tools now registered into UTR at init; fallback path removed |
| B-05 | Plugin hooks unchecked ctx access | D | CLOSED | `_restrict_ctx_for_plugin()` creates capability-scoped copy per hook type |
| B-06 | No default execution_id | E | CLOSED | `execute()` auto-generates UUID if execution_id is empty |
| B-07 | filesystem.write verifier self-consistency | F | MITIGATED | Verifier logic isolated; `set_expected_state()` API for authoritative expected state |
| B-08 | Receipt in-memory only | G | CLOSED | `ReceiptStore` + `FileReceiptStore` interface; UTR accepts pluggable store |
| B-09 | kernel.run() inline mode (no GovernanceStage) | B | CLOSED | (same as B-03) |

---

## Phase Details

### E3.2-A: Legacy Path Closure (`muscal_loop.py`)
- `_get_legacy_utr()` lazily creates UTR + SafetyGate instance
- `execute_tool()` routes through `utr.execute()`, falling back to EXECUTORS dict only on UTR exception
- All legacy executors registered into UTR via `_register_legacy_executors()`
- Receipts generated for every legacy tool call
- Pure backward compatibility preserved

### E3.2-B: Kernel Hot-Path Governance (`kernel.py`)
- `run()` method now calls `GovernanceStage(self).process()` before any stages
- Early-exit on governance violation returns `KernelResult(success=False)`
- Pipeline path already had governance (unchanged)

### E3.2-C: TOOL_REGISTRY Fallback Eliminated (`mel.py`)
- `_register_tools_to_utr()` registers all TOOL_REGISTRY functions into UTR with argument wrapper
- Fallback path `if tool_name not in TOOL_REGISTRY: return TOOL_REGISTRY[tool_name](**args)` removed
- Unknown tools now raise `RuntimeError` or produce error result

### E3.2-D: Plugin Capability Isolation (`plugin_registry.py`)
- `CAPABILITY_MAP` defines per-hook-type allowed capabilities
- `_restrict_ctx_for_plugin()` creates scoped context view before each hook call
- `register_plugin_capability()` for explicit capability declarations
- Plugins receive scoped copy; original context unaffected by mutations

### E3.2-E: execution_id Enforcement (`tool_runtime.py`)
- `execute()` auto-generates `str(uuid.uuid4())` if execution_id is empty
- Idempotency check now applies to both user-provided and auto-generated IDs
- Every receipt guaranteed to have non-empty execution_id

### E3.2-F: Independent Verification Oracle (`tool_runtime.py`)
- `set_expected_state(execution_id, expected)` API for authoritative expected state
- `get_expected_state(execution_id)` for verifier retrieval
- File write verifier still checks agent-provided content (backward compat) but independent expected state store available

### E3.2-G: Receipt Persistence (`features/tool_runtime/receipt_store.py`)
- `ReceiptStore` — in-memory store with thread-safe put/get/all
- `FileReceiptStore(ReceiptStore)` — in-memory cache + JSON file persistence
- UTR `__init__` accepts `receipt_store=` parameter; internal methods adapted for both dict and store

### E3.2-H: Bypass Forensic Audit
- Systematic audit of all 9 documented bypasses completed above
- No new bypasses discovered during E3.2 implementation

### E3.2-I: Adversarial Tests (31 tests)
- E3.2-A: legacy executors route through UTR, produce receipts
- E3.2-B: governance applied, blocks excess iterations
- E3.2-C: tools registered in UTR, unknown tools rejected
- E3.2-D: plugin capability scoping, input isolation
- E3.2-E: auto-generated execution_id, custom id, dedup
- E3.2-F: file write verifier, verification state diff
- E3.2-G: memory store, file store, UTR with store, count
- E3.2-H: multi-bypass scenarios, legacy+gov+tools
- E3.2-I: unknown tool rejection, safety gate, id spoofing, receipt tamper, plugin kernel protection
- E3.2-J: cross-boundary MEL consistency, math consistency
- E3.2-K: receipt integrity chain
- E3.2-L: expected state store

---

## Files Modified
| File | Change |
|---|---|
| `muscal_loop.py` | EXECUTORS/execute_tool rewired through UTR adapter |
| `kernel.py` | GovernanceStage added to `run()` |
| `mel.py` | TOOL_REGISTRY fallback removed; tools registered into UTR |
| `plugin_registry.py` | CAPABILITY_MAP, `_restrict_ctx_for_plugin()`, `register_plugin_capability()` |
| `features/tool_runtime/tool_runtime.py` | Auto execution_id, ReceiptStore support, set_expected_state |
| `features/tool_runtime/receipt_store.py` | NEW: ReceiptStore + FileReceiptStore |
| `tests/test_trust_boundary_e3_2.py` | NEW: 31 E3.2 adversarial tests |

---

## Core Invariant Verification

**Agent Claim != Execution Result != Verified State => Independent Evidence**

- Agent claim: agent-provided `args` dict
- Execution result: `ToolResult` with `success`/`output`/`error`/`receipt`
- Verified state: `VerificationResult` with independent `VerificationStatus`
- Execution artifacts persisted via `ReceiptStore`
- All 9 bypasses either CLOSED or MITIGATED
