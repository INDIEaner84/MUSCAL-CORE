# ADR-009: Observability Foundation

**Status:** PROPOSED  
**Date:** 2026-07-10  
**Author:** MASTER ORCHESTRATOR  

---

## Context

MUSCAL v0.7 lacks structured observability:

- No health/liveness/readiness endpoints in the FastAPI control plane
- No centralized metrics collection
- No structured logging setup
- No tracing foundation for debugging multi-step kernel executions

Without these, the system is invisible in production — crashes, slowdowns, and data corruption go undetected until a user reports them.

### Existing building blocks

The codebase has some ad-hoc observability scattered across modules:

| Module | Pattern | Problem |
|--------|---------|---------|
| `config.py` | Module-level constants, `get_session_id()` | No structured metadata |
| `event_bus.py` | `get_history()`, `get_stats()` | In-memory only, no export |
| `trace_engine.py` | `print_trace()` | CLI-only, not accessible via API |

### Requirements

- Monitoring systems (Prometheus, Grafana) need HTTP endpoints
- Container orchestration needs `/health`, `/ready`, `/live`
- Developers need structured logs (JSON format planned)
- Debugging needs span-based tracing for kernel execution

---

## Decision

**Option A: Thin foundation layer with explicit interfaces.**

Create `runtime/monitoring/` as a standalone package with four modules.
No external dependencies — use only the Python standard library and what is already in `pyproject.toml`.

### Module boundaries

```
runtime/monitoring/
  ├── __init__.py     # Public exports
  ├── health.py       # get_health(), get_ready(), get_live()
  ├── logging.py      # setup_logging()
  ├── metrics.py      # MetricsCollector (counters + gauges)
  └── trace.py        # Tracer (span-based, in-memory)
```

### Health endpoints (FastAPI control plane)

All four endpoints are added to `api_server.py`:

| Endpoint | Purpose | Response |
|----------|---------|----------|
| `GET /health` | General health | `{"status":"ok","uptime":...,"server_ready":true}` |
| `GET /ready` | Readiness (accepts traffic) | `{"status":"ready"}` or 503 |
| `GET /live` | Liveness (process alive) | `{"status":"alive"}` |
| `GET /version` | Version info | `{"name":"muscal-core","version":"0.7.0",...}` |

### MetricsCollector

```python
class MetricsCollector:
    def increment(self, name: str, value: int = 1): ...
    def gauge(self, name: str, value: float): ...
    def snapshot(self) -> dict: ...
```

In-memory counters and gauges. No Prometheus dependency at this stage.
`snapshot()` returns a plain dict for export via API or logging.

### Tracer

```python
class Tracer:
    def start_span(self, name: str): ...
    def add_event(self, name: str, attributes: dict = None): ...
    def end_span(self) -> dict: ...
    def snapshot(self) -> list: ...
```

In-memory span tree. Designed to wrap kernel `run()` steps.
No OpenTelemetry dependency at this stage.

### What is NOT in scope for v0.9

- Prometheus / OpenMetrics exposition format
- OpenTelemetry export
- Distributed tracing
- Log aggregation (Loki, ELK)
- Alerting rules
- Dashboard (Grafana)

---

## Consequences

### Positive
- Container healthchecks can target `/health` instead of raw port checks
- Monitoring systems have structured endpoints to poll
- Debugging gains span context without external dependencies
- Metrics and tracing can be retrofitted with real backends later (same interface)

### Negative
- No Prometheus exposition — monitoring must poll JSON endpoints or wait for v0.95
- In-memory only — metrics and traces are lost on restart

### Neutral
- `runtime/monitoring/` is a new package — no existing code is modified or broken
- The four modules total &lt;100 LOC with zero external dependencies

---

## Compliance Check

- [ ] `GET /health` returns status, uptime, server_ready
- [ ] `GET /ready` returns 200 when ready, 503 otherwise
- [ ] `GET /live` returns 200
- [ ] `GET /version` returns name, version, python, session
- [ ] `MetricsCollector.increment()` / `gauge()` / `snapshot()` works
- [ ] `Tracer.start_span()` / `add_event()` / `end_span()` / `snapshot()` works
- [ ] `setup_logging()` configures root logger with structured format
- [ ] No new external dependencies
- [ ] All 116+ unit tests still pass
