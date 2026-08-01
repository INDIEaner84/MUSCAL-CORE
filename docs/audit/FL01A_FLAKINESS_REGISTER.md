# FL-01a FLAKINESS REGISTER — Order-Dependent Test Failures (documented, NOT fixed)

**Date:** 2026-08-01 · **Source:** G2_ADJUDICATION_REPORT.md FL-01a · **Decision:** D-040
**Status:** DOCUMENTED — no fix applied (per Mission-Control directive; fix deferred to Phase B)

---

## 1. Symptom

Full pytest suite (`pytest -q`, 2.367 collected): **23 failed / 2.343 passed / 1 skipped**.
Reproduced identically twice (2026-08-01, before and after wave commits).

## 2. Failure split

| Group | Count | Determinism | Cause |
|-------|------:|-------------|-------|
| **Order-dependent (FL-01a)** | 19 | pass in isolation & in subset runs (verified: 177/177, 176+1) | Global singleton state pollution |
| **Baseline drift (FL-01b)** | 4 | deterministic | Stale EXPECTED_TOTAL → FIXED 2026-08-01 (commit 5d728c7) |

## 3. Order-dependent failures (19) — full register

| # | Test | Module | Isolated | Subset |
|---|------|--------|----------|--------|
| 1 | TestWorkerContract::test_worker_executes_tool | tests/test_worker.py | ✅ pass | ✅ |
| 2 | TestCognitiveUnitWorkerIntegration::test_cu_delegates_to_worker | tests/test_worker.py | ✅ | ✅ |
| 3 | TestCognitiveUnitWorkerIntegration::test_cu_without_worker_falls_back_to_direct_execution | tests/test_worker.py | ✅ | ✅ |
| 4 | TestWorkerE32Enrichment::test_w1_single_step_execution | tests/test_worker.py | ✅ | ✅ |
| 5 | TestWorkerE32Enrichment::test_w2_multi_step_ordered_execution | tests/test_worker.py | ✅ | ✅ |
| 6 | TestWorkerE32Enrichment::test_w4_continue_independent_continues | tests/test_worker.py | ✅ | ✅ |
| 7 | test_console_executor | tests/test_tool_runtime_phase3.py | ✅ | ✅ |
| 8 | test_filesystem_executor | tests/test_tool_runtime_phase3.py | ✅ | ✅ |
| 9 | test_file_write_alias | tests/test_tool_runtime_phase3.py | ✅ | ✅ |
| 10 | test_math_executor | tests/test_tool_runtime_phase3.py | ✅ | ✅ |
| 11 | test_browser_executor_stub | tests/test_tool_runtime_phase3.py | ✅ | ✅ |
| 12 | test_browser_unavailable_capabilities | tests/test_tool_runtime_phase3.py | ✅ | ✅ |
| 13 | test_verification_cu_with_runtime | tests/test_specialized_cu_phase5.py | ✅ | ✅ |
| 14 | test_verification_cu_single_receipt | tests/test_specialized_cu_phase5.py | ✅ | ✅ |
| 15 | test_verification_cu_tool_name | tests/test_specialized_cu_phase5.py | ✅ | ✅ |
| 16 | TestCanonicalRuntimeInit::test_r2_server_ready_state | tests/test_runtime_convergence.py | ✅ | ✅ |
| 17 | TestCanonicalRuntimeInit::test_r6_kernel_tool_check_with_runtime | tests/test_runtime_convergence.py | ✅ | ✅ |
| 18 | test_cognitive_unit_tool_delegation | tests/test_pipeline_phase4.py | ✅ | ✅ |
| 19 | TestP63GovernanceSafetyUTR::test_utr_enforces_safetygate | tests/test_phase6_production_readiness.py | ✅ | ✅ |

## 4. Root cause hypothesis [C1]

Module-level global singletons mutated across tests without reset:

| Global | Location |
|--------|----------|
| `_UTR = None` / `set_global_utr()` / `_get_global_utr()` | `tools.py:9-24` |
| `set_global_event_store()` / `get_global_event_store()` | `features/tool_runtime/tool_runtime.py:28-33` |
| `set_global_default_timeout()` / `get_global_default_timeout()` | `features/tool_runtime/tool_runtime.py:37-42` |
| `_GLOBAL_EVENT_STORE` registry | `features/tool_runtime/tool_runtime.py` (MC-TC-005.1) |

Tests in `test_tool_runtime_phase3.py` / `test_worker.py` / `test_specialized_cu_phase5.py`
mutate these globals (e.g. per-test UTR creation with global registration); when a
previous test leaves a configured global, subsequent tests observe stale wiring.
Failure mode observed: `AttributeError` (executor registry state), missing capabilities.

## 5. Decision (D-040)

**NOT fixed** per Mission-Control directive ("Flaky Tests NICHT reparieren, sondern nur
dokumentieren"). Deferred fix (Phase B): test-scoped autouse fixtures resetting
`_UTR`/global event store per test. Follow-up ADR for global-state ownership (D-042).

## 6. Mitigation status

- Full-suite runs until Phase B: expected `19 failed / 2348+ passed`.
- Isolation workaround documented: run failing files as subsets.
- CI implication: full-suite gates will be flaky-red; use subset strategy or `-p no:randomly`-style order pinning (NOT configured).

---

*Register maintained at docs/audit/FL01A_FLAKINESS_REGISTER.md · evidence: pytest runs 2026-08-01 (full ×2, isolated, subsets).*
