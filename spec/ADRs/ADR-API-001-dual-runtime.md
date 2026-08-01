# ADR-API-001 — Dual API Runtime During Reality Closure

**Status:** PROPOSED → APPROVED
**Date:** 2026-07-27
**Authority:** RC-02 Gate 1

## Context

The production deployment currently runs one API server:
- **Flask :5001** — started by `supervisor.py` Phase 2-3, serves runtime/backend API

A second server exists:
- **FastAPI** (`api_server.py`) — implements the control plane with SUPL routes, WebSocket, Graph inspection, Decision Autopsy
- This server is NOT started by the production boot path
- It creates independent `EventBus()` and `EventStore()` instances

SUPL API routes (`features/supl/api.py`) are implemented using FastAPI decorators. They cannot be directly mounted on Flask.

## Decision

**Keep Flask :5001 unchanged. Start FastAPI :8000 as the SUPL/API integration layer.**

Rationale:
1. SUPL API code already targets FastAPI — rewriting as Flask would be unnecessary work
2. SUPL WebSocket (`features/supl/ws_stream.py`) already targets FastAPI
3. Frontend JSX already targets port 8000 (`API_BASE = "http://localhost:8000"`)
4. Flask remains the runtime/observation/LLM backend — no disruption to existing functionality
5. FastAPI provides native async WebSocket support needed by SUPL

## Architecture

```
supervisor.py
  ├── Phase 1: MuscalOS.start()
  │     └── canonical EventBus, EventStore, UTR
  ├── SUPL Runtime Initialization
  │     ├── initialize_supl_runtime(
  │     │     event_bus=MuscalOS.events,
  │     │     event_store=MuscalOS.event_store,
  │     │     utr=production_utr,
  │     │     fastapi_app=app,
  │     │   )
  │     └── uvicorn.run(app, port=8000, ...)
  ├── Phase 2: Flask Runtime API (:5001)
  └── Phase 4: Shutdown both servers
```

## Ownership

| Component | Owner | Lifecycle |
|-----------|-------|-----------|
| MuscalOS | supervisor.py | Phase 1 → Phase 4 |
| FastAPI SUPL | supervisor.py | After Phase 1 → Phase 4 |
| Flask API | supervisor.py | Phase 2-3 → Phase 4 |
| EventBus | MuscalOS | Owned by MuscalOS |
| EventStore | MuscalOS | Owned by MuscalOS |
| SUPL Runtime | supervisor.py | Created after Phase 1, shutdown in Phase 4 |

## Ports

| Server | Port | Purpose |
|--------|------|---------|
| Flask | 5001 | Runtime API (existing) |
| FastAPI | 8000 | SUPL API + WebSocket + Control Plane |

## Limitations

1. Two API servers add operational complexity
2. No HTTP-level sharing between Flask and FastAPI
3. Both servers share the same SQLite database (thread-safe via WAL mode)
4. This is a transitional architecture — consolidation may be possible in a future gate
5. No process-level isolation — both servers in the same Python process

## Future Options

- Mount Flask as ASGI app under FastAPI (merging into one server)
- Replace Flask entirely with FastAPI
- Extract FastAPI to a separate container
