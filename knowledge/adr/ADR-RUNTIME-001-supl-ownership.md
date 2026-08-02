# ADR-RUNTIME-001 — MuscalOS Ownership of SUPL Runtime

**Status:** PROPOSED → APPROVED
**Date:** 2026-07-27
**Authority:** RC-02 Gate 1

## Context

SUPL components (EventBusBridge, AdapterRegistry, GraphProjectionEngine, ProvenanceLinker, SUPLAPI, WebSocket) need to be initialized with production dependencies and managed through the production lifecycle.

Currently:
- `features/supl/initialize.py` has a clean `initialize_supl_runtime()` function that accepts dependencies
- `api_server.py` calls it but uses independent EventBus/EventStore instances
- No production bootstrap path calls it

## Decision

`supervisor.py` — the canonical production entry point — creates and owns the SUPL runtime.

The ownership chain:

```
supervisor.py
  └── MuscalOS (creates canonical authorities)
  └── SUPL Runtime (created after MuscalOS.start())
        ├── EventBusBridge (wraps MuscalOS.events)
        ├── AdapterRegistry (with EventBusBridge)
        ├── GraphProjectionEngine (with AdapterRegistry + store)
        ├── GraphProjectionEventBridge (subscribes to MuscalOS.events)
        ├── ProvenanceLinker (with EventBusBridge)
        ├── SUPLAPI (with all of the above + production UTR)
        ├── SUPLWebSocketManager (with MuscalOS.events + MuscalOS.event_store)
        └── FastAPI (:8000)
```

## Initialization Order

1. `MuscalOS.__init__()` — creates EventBus, EventStore (not yet started)
2. `MuscalOS.start()` — boots all phases, wires EventBus, starts health checks
3. `os_instance.events` — READY
4. `os_instance.event_store` — READY
5. Plugin UTR wiring — COMPLETE (via boot)
6. **SUPL Runtime** — initialized with canonical authorities
7. FastAPI — starts on port 8000
8. Flask — starts on port 5001 (existing Phase 2)

## Shutdown Order

1. Signal received (SIGTERM/SIGINT)
2. FastAPI uvicorn server stops
3. Flask app.run() returns
4. SUPL Runtime.shutdown() — unsubscribes EventBus subscriptions
5. MuscalOS.shutdown() — flushes EventStore, saves snapshot
6. WriterThread stops
7. Process exits

## Duplicate Prevention

- `api_server.py`'s module-level initialization is ONLY active when running `python api_server.py` directly
- The production path (`supervisor.py`) does NOT import `api_server.py` as a module
- SUPL initialization in `supervisor.py` creates a FRESH FastAPI app, not importing the module-level one
- No risk of duplicate EventBus/EventStore instances in the production path

## Development Mode

`api_server.py` can still be run directly for development:
```
uvicorn api_server:app --host 0.0.0.0 --port 8000
```
In this mode, it creates independent EventBus/EventStore instances (acceptable for development).
