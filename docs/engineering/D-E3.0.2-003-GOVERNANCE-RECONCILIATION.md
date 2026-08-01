# D-E3.0.2-003 — GOVERNANCE RECONCILIATION

**Status:** CORRECTED
**Supersedes:** D-E3.0-005 (§Governance), D-E3.0-012 (§5)
**Date:** 2026-07-22

---

## 1. Previous Claim (E3.0)

Governance is "partially wired" and needs integration into the kernel pipeline.

## 2. Corrected Claim

**Two Governance implementations exist** with different locking models and reachability:

| Implementation | Locking | Reachability | Status |
|---------------|---------|-------------|--------|
| `Governance` (async) | `asyncio.Lock()` | Called by `gate.py` without `await` — **BUG** | COLD_PATH |
| `GovernanceSync` (sync) | `threading.Lock()` | Created and used by `runtime/main.py`, `supervisor.py`, `gate.py` | **WARM_PATH** |

Neither implementation is called by `MuscalKernel.run()` (HOT_PATH).

## 3. Repository Evidence

| Evidence | Source |
|----------|--------|
| Governance.consume_iteration() is async | `governance.py:57`: `async def consume_iteration` |
| Gate calls consume_iteration without await | `gate.py:15`: `if governance is not None and not governance.consume_iteration(task_type):` → returns coroutine (always truthy) |
| GovernanceSync.consume_iteration() is sync | `governance.py:174`: `def consume_iteration` (no async) |
| GovernanceSync created in runtime/main.py | `runtime/main.py:35`: `governance = GovernanceSync()` |
| GovernanceSync created in supervisor.py | `supervisor.py:68`: `governance = GovernanceSync()` |
| Gate receives governance as `Any` | `gate.py:14`: `governance: Any = None` |
| Governance NOT imported by kernel.py | `grep` confirms zero references |
| ExecutionGovernor stub (38 lines) | `execution_governor.py` — only imported by orphaned `permission_engine.run_muscal()` |
| ObservationLoop monitors governance violations | `runtime/observation/loop.py:81` |

## 4. Call Graph

```
Flask API (runtime/main.py, supervisor.py)
  ├── GovernanceSync (created)
  ├── set_governance(governance) → ObservationLoop monitors
  └── runtime/api/tasks.py:api_submit_task()
        └── gate.py:start_task_atomic(governance=GovernanceSync)
              └── governance.consume_iteration()  ← sync, works correctly

MuscalKernel.run() (main.py, main_boot.py)
  └── [NO GOVERNANCE CALLED]  ← HOT_PATH GAP
```

## 5. Classification

**WARM_PATH** for `GovernanceSync` (used by Flask API path).
**COLD_PATH** for `Governance` (async — has a bug if instantiated).
**ORPHANED** for `ExecutionGovernor`.

## 6. Latent Bug

If `async Governance` is passed to `gate.py:start_task_atomic()`, the call `governance.consume_iteration(task_type)` returns a coroutine object. Coroutine objects are truthy, so the check `not governance.consume_iteration(...)` evaluates to `False`, and governance **never blocks**. The guard is silently bypassed.

This is currently harmless because only `GovernanceSync` is instantiated in production, but it represents a type-safety violation that could cause governance failures if the code is refactored.

## 7. Architectural Impact

- E3.1 must **wire governance into the kernel hot path** — this is a genuine gap
- The `GovernanceSync` implementation is production-ready and can be referenced as the target pattern
- E3.1 must resolve the async/sync duality (prefer sync for the kernel pipeline)
- The latent `gate.py` bug must be fixed when governance is formalized

## 8. E3.1 Consequence

**REQUIRES NEW CONTRACT.** E3.1 must specify a Governance contract for the kernel hot path. The existing `GovernanceSync` is the reference implementation. The gate.py async bug must be fixed as part of the governance formalization.

## 9. Governance Interface Comparison

| Feature | WARM_PATH (Flask API) | HOT_PATH (kernel) | TARGET |
|---------|----------------------|-------------------|--------|
| Implementation | GovernanceSync | None | Unified governance |
| Check | Per-task via gate.py | None | Per-iteration + per-tool |
| Limits | Iterations, tokens, cost | None | Iterations, tokens, cost, human-in-loop |
| Persistence | None | None | Event-sourced |
| Locking | threading.Lock | None | threading.Lock (preferred) |
