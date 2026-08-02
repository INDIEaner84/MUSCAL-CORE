# ADR-008: Deployment Runtime — Supervisor Container Model

**Status:** ACCEPTED  
**Date:** 2026-07-08  
**Author:** MASTER ORCHESTRATOR  

---

## Context

MUSCAL v0.7 has three runtime entry points with unclear deployment boundaries:

| Entry Point | File | Function | Current Container Target |
|-------------|------|----------|--------------------------|
| **CLI REPL** | `main.py` | Interactive kernel loop, no network | Yes (`CMD ["python", "main.py"]`) |
| **OS Runtime** | `muscal_os.py` | Full OS lifecycle: boot phases, EventBus, kernel, plugins, health checks | No |
| **API Runtime** | `runtime/main.py` | Flask API on :5001, DB writer, observation loop, governance | No |

### Runtime: Podman (rootless)

Deployment targets **Podman 4.9.3 rootless** on Linux. Docker-compatible — `Containerfile` and `compose.yml` work with both `podman` and `docker` runtimes.

### Problems with the previous Containerfile (Dockerfile)

1. **Wrong target**: `CMD ["python", "main.py"]` starts the CLI REPL, which blocks on `input()` — the container hangs forever waiting for stdin
2. **Port mismatch**: `docker-compose.yml` exposed port 8000, but `runtime/main.py` serves on port 5001, and `main.py` serves nothing
3. **Single process**: No supervisor — if the kernel crashes, the container dies
4. **No lifecycle**: `muscal_os.py` manages boot readiness, health checks, and shutdown — but the Containerfile ignored it entirely

### Existing building blocks

The codebase already has most of what a supervisor needs:

```
muscal_os.MuscalOS
  ├── BootManager (5 phases: INIT → LOAD_CONFIG → INIT_MODULES → START_SERVICES → HEALTH_CHECK)
  ├── EventBus (publish/subscribe, history, priorities)
  ├── MuscalKernel (RAG→MKC→Bridge→Optimizer→MEL→Feedback→Memory)
  ├── Plugin loader (auto-discovery in features/)
  ├── Health checks (memory, graph, sphere, tools)
  └── Shutdown lifecycle (snapshot, flush, cleanup)

runtime.main
  ├── init_db / check_consistency_on_start
  ├── WriterThread (async DB writes)
  ├── ObservationLoop (governance monitoring)
  ├── GovernanceSync (iteration limits)
  ├── LLM router (Qwen, SMOL)
  ├── Flask API (blueprints: state, tasks, workers, events, chat, models, rag, fs, admin, handoff)
  └── CORS + before_request hooks
```

---

## Decision

**Option C: Supervisor Container that starts both MUSCAL OS and the API Runtime.**

```
┌──────────────────────────────────────────────────────┐
│                   Container                           │
│                                                        │
│   ┌──────────────────────────────────────────────┐    │
│   │           supervisor.py (PID 1)               │    │
│   │                                                │    │
│   │   1. Start EventBus                            │    │
│   │   2. Start MUSCAL OS (muscal_os.MuscalOS)      │    │
│   │      ├── BootManager phases                    │    │
│   │      ├── Kernel init                           │    │
│   │      ├── Plugin loading                        │    │
│   │      ├── Health checks                         │    │
│   │      └── EventBus subscription                │    │
│   │   3. Start API Runtime (runtime.main)          │    │
│   │      ├── DB init + writer                      │    │
│   │      ├── Observation loop                     │    │
│   │      └── Flask on :5001                       │    │
│   │   4. Health endpoint :5001/api/health         │    │
│   │   5. Graceful shutdown on SIGTERM             │    │
│   └──────────────────────────────────────────────┘    │
└──────────────────────────────────────────────────────┘
```

### Why not multi-container?

| Approach | Pros | Cons |
|----------|------|------|
| **Single container (Option C)** | Simple networking, shared storage, single lifecycle | All processes share host |
| **Multi-container** | Independent scaling, failure isolation | Docker networking, volume sync, startup ordering |
| **Sidecar** | API can scale independently | EventBus must cross container boundary |

Single container is correct for v0.8:

- Plugin system is in-process (no IPC)
- EventBus is in-memory (no serialization)
- Single user / single tenant
- No horizontal scaling requirement
- Simpler to monitor (one health check, one log stream)

### Supervisor Process Model

```
PID 1: supervisor.py
  ├── Thread: EventBus (in-process)
  ├── Thread: MuscalOS (boot phases, kernel, plugins)
  ├── Thread: API Runtime (Flask, DB writer, observation)
  ├── Signal handler: SIGTERM → graceful shutdown
  │   ├── 1. Stop accepting requests
  │   ├── 2. Flush EventBus
  │   ├── 3. Save kernel snapshot
  │   ├── 4. Stop observation loop
  │   ├── 5. Stop writer thread
  │   └── 6. Exit(0)
  └── Health: /api/health returns OS + API status
```

### Startup Sequence

```
supervisor.py start()
  │
  ├── 1. Create storage directories
  │
  ├── 2. Init EventBus (in-memory, shared between OS and API)
  │
  ├── 3. Boot MUSCAL OS
  │     ├── Phase INIT: storage, EventBus
  │     ├── Phase LOAD_CONFIG: validate, resolve paths
  │     ├── Phase INIT_MODULES: kernel, plugins, system runtime
  │     ├── Phase START_SERVICES: wire EventBus, load snapshot
  │     └── Phase HEALTH_CHECK: memory, graph, sphere, tools → READY
  │
  ├── 4. Boot API Runtime
  │     ├── init_db
  │     ├── WriterThread start
  │     ├── ObservationLoop start
  │     ├── GovernanceSync
  │     ├── LLM router init
  │     ├── Flask create_app + register_blueprints
  │     └── set_server_ready(True)
  │
  └── 5. Block on Flask (app.run)
```

### Shutdown Sequence

```
SIGTERM → supervisor.py
  │
  ├── 1. set_server_ready(False) → API returns 503
  ├── 2. Flush EventBus history
  ├── 3. MuscalOS.shutdown() → save snapshot, close storage
  ├── 4. ObservationLoop.stop()
  ├── 5. WriterThread.stop()
  └── 6. Exit(0)
```

---

## Migration Plan

### Phase 1: Create supervisor.py

A single module in the project root that replaces `main.py` as the container entry point.

### Phase 2: Create Containerfile + compose.yml

`Containerfile` (Podman-native, gleiches Format wie Dockerfile):

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
RUN mkdir -p /app/storage
CMD ["python", "supervisor.py"]
```

`compose.yml` (ersetzt docker-compose.yml, Podman + Docker kompatibel):

```yaml
services:
  muscal:
    build:
      context: .
      dockerfile: Containerfile
    ports:
      - "${RUNTIME_FLASK_PORT:-5001}:5001"
    volumes:
      - ./storage:/app/storage:Z
    environment:
      - MUSCAL_ENV=${MUSCAL_ENV:-production}
      - MUSCAL_MODE=${MUSCAL_MODE:-standard}
      - OLLAMA_BASE=${OLLAMA_BASE:-http://host.containers.internal:11434}
      - RUNTIME_FLASK_PORT=${RUNTIME_FLASK_PORT:-5001}
    user: "1000:1000"
    init: true
    read_only: true
    tmpfs:
      - /tmp
    cap_drop:
      - ALL
    security_opt:
      - no-new-privileges:true
    restart: unless-stopped
    stop_grace_period: 30s
    healthcheck:
      test: ["CMD", "python", "-c", "import urllib.request; urllib.request.urlopen('http://localhost:5001/api/health')"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 15s
```

### Phase 4: Security regression tests (23.18)

Once the supervisor model is defined:

- `tests/security/test_path_policy.py`
- `tests/security/test_input_limits.py`
- `tests/security/test_database_validation.py`
- `tests/security/test_tool_return_contract.py`

### Phase 5: Supervisor lifecycle contract test

```python
# tests/contract/test_supervisor_lifecycle.py
def test_supervisor_startup():
    sup = Supervisor(config=test_config)
    report = sup.start()
    assert report.os_ready == True
    assert report.api_ready == True
    assert report.eventbus_active == True
    assert sup.health()["status"] == "ready"
    sup.stop()
```

---

## Consequences

### Positive
- Single deployment artifact (one Docker image, one compose service)
- Existing `muscal_os.py` boot phases are reused (not rewritten)
- Existing `runtime/main.py` API is reused (not rewritten)
- CLI REPL (`main.py`) remains available for development
- Clean shutdown with state persistence
- Health check covers both OS and API

### Negative
- Single container means no independent scaling of OS vs API
- Plugin crash affects the entire container (mitigated by auto-heal in plugin_registry)
- EventBus in-memory: restart loses queued events (acceptable for v0.8)

### Neutral
- `supervisor.py` adds ~80 LOC but replaces no existing files
- `main.py` still works for CLI development
- Port changes from 8000 to 5001 (aligns with `config.RUNTIME_FLASK_PORT`)

---

## Compliance Check

- [ ] Phase 1: supervisor.py created with OS + API boot sequence
- [ ] Phase 2: Containerfile created with `CMD ["python", "supervisor.py"]`
- [ ] Phase 3: compose.yml created (port 5001, env, healthcheck, :Z volumes)
- [ ] Phase 4: Security regression tests pass
- [ ] Phase 5: Supervisor lifecycle contract test passes
- [ ] `.containerignore` + `.env.example` created
- [ ] Old `Dockerfile` + `docker-compose.yml` removed
- [ ] `main.py` remains functional for CLI development
- [ ] `podman build -t muscal-core -f Containerfile .` succeeds
- [ ] `podman run -p 5001:5001 muscal-core` serves /api/health
- [ ] `podman stop` triggers graceful shutdown (SIGTERM → snapshot → exit 0)
