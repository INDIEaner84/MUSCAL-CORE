# D-E3.0.2-002 — ROUTING RECONCILIATION

**Status:** CORRECTED
**Supersedes:** D-E3.0-005, D-E3.0-006
**Date:** 2026-07-22

---

## 1. Previous Claim (E3.0)

The Router domain is "partially implemented" and needs generalization. `scheduler.py:RoutingPolicy` was described as a component that needs further development.

## 2. Corrected Claim

**Two independent routing systems exist** with different production reachability:

| Component | Location | Status | Classification |
|-----------|----------|--------|----------------|
| `RoutingPolicy` | `runtime/kernel/scheduler.py` | Fully functional with DB-backed rules | **WARM_PATH** |
| `TaskRouter` | `task_router.py` (root) | Stub: `route()` + `send()` only | **ORPHANED** |
| `AdaptiveRouter` | `adaptive_router.py` | Stub: trust-based filtering only | **ORPHANED** |

`RoutingPolicy` is called by `gate.py:start_task_atomic()` which is called by `runtime/api/tasks.py`. It is NOT called by `MuscalKernel.run()`. The Router domain is complete in the Flask API path but entirely absent from the kernel hot path.

## 3. Repository Evidence

| Evidence | Source |
|----------|--------|
| RoutingPolicy has 34 lines with full DB implementation | `scheduler.py` |
| RoutingPolicy.route() returns DB value or `"qwen_router"` default | `scheduler.py:29` |
| RoutingPolicy called by gate.py | `gate.py:6`: `from runtime.kernel.scheduler import RoutingPolicy` |
| RoutingPolicy called by runtime/main.py | `runtime/main.py:33`: `policy = RoutingPolicy(config.DB_PATH)` |
| RoutingPolicy called by supervisor.py | `supervisor.py:67`: `policy = RoutingPolicy()` |
| gate.py called by tasks API | `runtime/api/tasks.py:10`: `from runtime.kernel.gate import start_task_atomic` |
| RoutingPolicy NOT called by kernel.py | `grep` confirms zero references in kernel.py |
| TaskRouter has 12 lines, zero callers | `task_router.py` |
| AdaptiveRouter has 11 lines, zero callers | `adaptive_router.py` |

## 4. Call Graph

```
Flask API (runtime/main.py, supervisor.py)
  └── runtime/api/tasks.py:api_submit_task()
        └── gate.py:start_task_atomic()
              ├── scheduler.py:RoutingPolicy.route()  ← WARM_PATH
              └── runtime/kernel/writer.py:WriterThread  ← WARM_PATH

MuscalKernel.run() (main.py, main_boot.py)
  └── [NO ROUTING CALLED]  ← HOT_PATH GAP
```

## 5. Classification

**WARM_PATH** for `runtime/kernel/scheduler.py:RoutingPolicy`.
**ORPHANED** for `task_router.py` and `adaptive_router.py`.

## 6. Architectural Impact

- E3.1 must **add routing to the kernel hot path** — this is a gap, not a partial implementation
- The existing `RoutingPolicy` in `runtime/kernel/scheduler.py` is a valid implementation that can be reused or adapted
- E3.1 must decide: bridge the API route to the kernel, or implement a separate Router in the kernel
- The `"qwen_router"` hardcoded default is a model-binding violation in WARM_PATH

## 7. E3.1 Consequence

**REQUIRES NEW CONTRACT.** E3.1 must specify a Router contract for the kernel hot path. The existing `RoutingPolicy` can serve as the WARM_PATH reference implementation but must be adapted for the kernel pipeline.

## 8. Routing Infrastructure Comparison

| Aspect | WARM_PATH (Flask API) | HOT_PATH (kernel) | TARGET (canonical) |
|--------|----------------------|-------------------|--------------------|
| Routing | RoutingPolicy (DB-backed) | None | Router → CU dispatch |
| Entry point | POST /api/task | MuscalKernel.run() | — |
| Task type | Explicit (task_type) | Task plan from MKC/MCXF | Implicit from task analysis |
| Backend | WriterThread + SQLite | Inline execution | Unified tool runtime |
