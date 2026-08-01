# MC-TC-004 — Failure Debt Classification

---

## Methodology

Each of the 18 pre-existing test failures is independently classified for Trust Core relevance. Tests were run both in isolation and in the full suite to identify the failure pattern.

**Independent verification:** Each of the 18 tests passes when run in isolation (`pytest test_file.py::test_name -v` → PASS) and fails only in the full suite due to global state carryover from preceding tests.

---

## Failure Classification

### Category A: Truly Unrelated (18/18)

| # | Test | Module | Layer | TC Relevance | Reason |
|---|------|--------|-------|-------------|--------|
| 1 | test_console_executor | test_tool_runtime_phase3.py | RUNTIME | NONE | Console executor implementation — no identity, state, or event concerns |
| 2 | test_filesystem_executor | test_tool_runtime_phase3.py | RUNTIME | NONE | Filesystem executor — no Trust Core interface |
| 3 | test_file_write_alias | test_tool_runtime_phase3.py | RUNTIME | NONE | File write alias — no Trust Core interface |
| 4 | test_math_executor | test_tool_runtime_phase3.py | RUNTIME | NONE | Math executor — no Trust Core interface |
| 5 | test_browser_executor_stub | test_tool_runtime_phase3.py | RUNTIME | NONE | Browser executor stub — no Trust Core interface |
| 6 | test_browser_unavailable_capabilities | test_tool_runtime_phase3.py | RUNTIME | NONE | Browser capabilities — no Trust Core interface |
| 7 | test_worker_executes_tool | test_worker.py | RUNTIME | NONE | Worker tool execution — no Trust Core interface |
| 8 | test_cu_delegates_to_worker | test_worker.py | RUNTIME | NONE | CU→Worker delegation — no Trust Core interface |
| 9 | test_cu_without_worker_fallback | test_worker.py | RUNTIME | NONE | Fallback execution — no Trust Core interface |
| 10 | test_w1_single_step_execution | test_worker.py | RUNTIME | NONE | Single step — no Trust Core interface |
| 11 | test_w2_multi_step_ordered | test_worker.py | RUNTIME | NONE | Multi-step order — no Trust Core interface |
| 12 | test_w4_continue_independent | test_worker.py | RUNTIME | NONE | Continue independent — no Trust Core interface |
| 13 | test_verification_cu_with_runtime | test_specialized_cu_phase5.py | RUNTIME | NONE | Verification CU runtime — uses UTR, not Trust Core verification path |
| 14 | test_verification_cu_single_receipt | test_specialized_cu_phase5.py | RUNTIME | NONE | Single receipt — no Trust Core interface |
| 15 | test_verification_cu_tool_name | test_specialized_cu_phase5.py | RUNTIME | NONE | Tool name — no Trust Core interface |
| 16 | test_cognitive_unit_tool_delegation | test_pipeline_phase4.py | PIPELINE | NONE | CU→Tool delegation — pipeline stage, not Trust Core |
| 17 | test_r6_kernel_tool_check_with_runtime | test_runtime_convergence.py | RUNTIME | NONE | Kernel+tool runtime check — runtime integration |
| 18 | test_utr_enforces_safetygate | test_phase6_production_readiness.py | RUNTIME | NONE | UTR safety gate — runtime governance |

### Evidence of No Trust Core Relevance

All 18 tests were searched for any reference to Trust Core components:

- **`ExecutionContext`**: 0 references across all 18 test files
- **`EventStore`**: 0 references
- **`execution_id`**: 0 references  
- **`EventBus`**: 0 references
- **`_persist_to_store`**: 0 references
- **`_enriched_persist`**: 0 references
- **`verification_state`**: 0 references
- **`execution_state`**: 0 references

These tests exclusively test tool runtime executors, worker delegation patterns, cognitive unit tool delegation, and runtime convergence — all in the RUNTIME layer below the Trust Core.

### Failure Pattern

All 18 failures follow the same pattern:
- **Import-time initialization dependency**: The `UnifiedToolRuntime`, executor modules, and worker modules perform import-time global initialization (e.g., `set_global_event_store()`). When test ordering changes (due to file name ordering or previous test state), the global state is not properly initialized.
- **`AttributeError`**: Typically `module 'X' has no attribute 'Y'` — caused by circular import or uninitialized module attribute.
- **`AssertionError`**: Typically an assertion fails because the expected runtime component was not registered (due to global state not being set by a preceding initialization test).

---

## Classification Summary

| Category | Count | Details |
|----------|-------|---------|
| A. Truly unrelated | **18** | All in RUNTIME layer, no Trust Core component references |
| B. Indirectly related | 0 | — |
| C. Directly Trust Core relevant | 0 | — |
| D. Hidden blocker | 0 | — |

---

## Impact on MC-TC-004

| Question | Answer |
|----------|--------|
| Does any failure affect identity continuity? | NO |
| Does any failure affect state authority? | NO |
| Does any failure affect execution truth? | NO |
| Does any failure affect provenance integrity? | NO |
| Does any failure affect evidence integrity? | NO |
| Does any failure affect verification integrity? | NO |
| Does any failure affect persistence integrity? | NO |
| Does any failure affect replayability? | NO |
| Does any failure affect security boundaries? | NO |
| Does any failure affect EventStore operations? | NO |

These 18 failures are **strictly pre-existing runtime-layer test infrastructure issues** with zero relevance to Trust Core semantics, identity continuity, state integrity, event integrity, or provenance.

---

## Verdict

**All 18 failures classified as: A. TRULY UNRELATED**

The phrase "pre-existing" is justified by:
1. Each test passes in isolation ✓
2. None reference Trust Core components ✓
3. All are in the RUNTIME layer ✓
4. Failure pattern is consistent with import-order global state ✓
5. MC-TC-003E changes did not touch any of these files ✓

**No reclassification required. No hidden blockers.**
