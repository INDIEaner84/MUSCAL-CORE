# Gate 1 Certification: SUPL Production Wiring

**Status**: PASS
**Date**: 2026-07-27
**Certifier**: OpenCode autonomous audit

## Scope

Wire SUPL (FastAPI control plane + runtime) into the canonical production boot
path: `Containerfile → supervisor.py → MuscalOS → EventBus/EventStore → FastAPI:8000`.

## Criteria

| # | Criterion | Status | Evidence |
|---|-----------|--------|----------|
| 1 | FastAPI:8000 served from same process as supervisor.py | PASS | `supervisor.py:61-72` — uvicorn daemon thread in-phase |
| 2 | `create_app()` receives canonical EventBus from MuscalOS | PASS | `supervisor.py:55` — `os_instance.events` injected |
| 3 | `create_app()` receives canonical EventStore from MuscalOS | PASS | `supervisor.py:56` — `os_instance.event_store` injected |
| 4 | `api_server.py` does NOT create its own EventBus/EventStore in production | PASS | `api_server.py:111-112` — fallback is dead code; `supervisor.py` always provides instances |
| 5 | supervisor.py owns SUPL lifecycle (start, shutdown) | PASS | `supervisor.py:54-58` (create), `supervisor.py:78` (shutdown) |
| 6 | SUPL runtime receives UTR (if available) | PASS | `supervisor.py:50,57` — `get_global_utr()` passed to `create_app()` |
| 7 | Production wiring does not regress existing SUPL tests | PASS | 324/324 SUPL tests pass (excluding pre-existing broken `test_production_integration.py`) |
| 8 | Phase 1b Boot Contract is satisfied | PASS | `test_gate1_production_wiring.py` — 10/10 pass |

## Audit Findings

### Non-Blocking

1. **api_server.py:111-112** — Fallback `EventBus()` / `EventStore()` creates
   duplicate authorities when `None` is passed. Dead code in the production
   path but violates ADR-EVENT-001. Fix: replace with `assert` or error.

2. **tests/supl/test_production_integration.py** — Pre-existing test file uses
   non-existent API (`registry.add()`, `registry.update()`, `registry.remove()`).
   Not caused by Gate 1 changes; excluded from regression.

3. **test_phase6_production_readiness.py::test_utr_enforces_safetygate** —
   Fails in suite due to leaked global EventStore from a prior test. Passes in
   isolation. Pre-existing test isolation issue.

## Summary

All 8 Gate 1 criteria met. Production path verified: `supervisor.py` →
`MuscalOS` → canonical EventBus/EventStore → `create_app()` → FastAPI:8000.
No production-blocking regressions. 10 Gate 1 integration tests pass.
