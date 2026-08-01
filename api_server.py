import asyncio
import logging
import os
import time
from datetime import datetime, timezone
from typing import Any, Optional, Tuple

from fastapi import FastAPI, WebSocket, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from runtime.api.errors import api_error
from event_bus import EventBus
from runtime.event_store import EventStore

from features.runtime_canonical import (
    get_auth_token,
    get_security_headers,
    get_shared_state,
    is_auth_required,
    is_server_ready,
    RUNTIME_CANONICAL_VERSION,
)

from features.supl.initialize import initialize_supl_runtime, SuplRuntime

try:
    from graph_store import GraphStore
except ImportError:
    from graph_memory import GraphMemory as GraphStore

from decision_autopsy import DecisionAutopsy
try:
    from meta_reasoning_kernel import MetaReasoningKernel
except ImportError:
    class MetaReasoningKernel:
        def __init__(self, *a, **kw): pass
        def run(self, *a, **kw): return {}
from recursive_self_improver import RecursiveSelfImprover
from replay_engine import ReplayEngine

import config

logger = logging.getLogger(__name__)

MAX_BODY_SIZE = 10 * 1024 * 1024


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        response = await call_next(request)
        headers = get_security_headers()
        for header, value in headers.items():
            response.headers[header] = value
        return response


def _create_middleware(app: FastAPI) -> None:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost", "http://127.0.0.1"],
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=["Content-Type", "Authorization", "X-API-Key"],
    )
    app.add_middleware(SecurityHeadersMiddleware)

    @app.middleware("http")
    async def limit_content_size(request: Request, call_next):
        cl = request.headers.get("content-length")
        if cl and int(cl) > MAX_BODY_SIZE:
            return JSONResponse(api_error("Request too large", 413)[0], status_code=413)
        return await call_next(request)

    @app.middleware("http")
    async def check_server_ready(request: Request, call_next):
        if not is_server_ready() and request.url.path != "/health":
            return JSONResponse(api_error("Server initializing - please wait", 503)[0], status_code=503)
        return await call_next(request)

    @app.middleware("http")
    async def check_auth(request: Request, call_next):
        if not is_auth_required(request.url.path, request.method):
            return await call_next(request)
        token = request.headers.get("X-API-Key", "")
        if token != get_auth_token():
            return JSONResponse(api_error("Unauthorized", 401)[0], status_code=401)
        return await call_next(request)

    try:
        from slowapi import Limiter, _rate_limit_exceeded_handler
        from slowapi.util import get_remote_address
        limiter = Limiter(key_func=get_remote_address)
        app.state.limiter = limiter
        app.add_exception_handler(429, _rate_limit_exceeded_handler)
    except ImportError:
        pass


def create_app(
    event_bus: Optional[EventBus] = None,
    event_store: Optional[EventStore] = None,
    utr: Any = None,
) -> Tuple[FastAPI, SuplRuntime]:
    from features.runtime_canonical import init_canonical_runtime
    init_canonical_runtime()

    app = FastAPI(title="MUSCAL Control Plane", docs_url="/docs", redoc_url="/redoc")
    _create_middleware(app)

    bus = event_bus if event_bus is not None else EventBus()
    store_inst = event_store if event_store is not None else EventStore()

    graph_store = GraphStore()
    replay_engine = ReplayEngine(graph_store)
    autopsy = DecisionAutopsy(graph_store)
    meta_kernel = MetaReasoningKernel(autopsy)
    improver = RecursiveSelfImprover()

    supl_runtime = initialize_supl_runtime(
        event_bus=bus,
        event_store=store_inst,
        fastapi_app=app,
        utr=utr,
    )

    _register_routes(app, graph_store, replay_engine, autopsy, meta_kernel, improver)

    return app, supl_runtime


def _register_routes(app, graph_store, replay_engine, autopsy, meta_kernel, improver):
    @app.get("/health")
    def health():
        state = get_shared_state()
        return {
            "status": "ok",
            "uptime": round(time.monotonic() - state["start_time"], 2),
            "server_ready": is_server_ready(),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "runtime_version": RUNTIME_CANONICAL_VERSION,
        }

    @app.get("/ready")
    def ready():
        s = get_shared_state()
        if not is_server_ready():
            return JSONResponse({"status": "not_ready"}, status_code=503)
        return {"status": "ready", "uptime": round(time.monotonic() - s["start_time"], 2)}

    @app.get("/live")
    def live():
        return {"status": "alive"}

    @app.get("/version")
    def version():
        state = get_shared_state()
        return {
            "name": "muscal-core",
            "version": "0.7.0",
            "python": os.environ.get("PYTHON_VERSION", "3.12"),
            "session": config.SESSION_ID,
            "runtime_version": RUNTIME_CANONICAL_VERSION,
        }

    @app.get("/graph")
    def get_graph():
        return {
            "nodes": [{"id": n.id, "type": n.type, "payload": n.payload} for n in graph_store.nodes.values()],
            "edges": graph_store.edges
        }

    @app.get("/replay/{node_id}")
    def replay(node_id: str):
        return replay_engine.replay(node_id)

    @app.get("/explain/{node_id}")
    def explain(node_id: str):
        return autopsy.run(node_id)

    @app.get("/meta-explain/{node_id}")
    def meta_explain(node_id: str):
        return meta_kernel.run(node_id)

    @app.get("/self-improve/{node_id}")
    def self_improve(node_id: str):
        critique_result = meta_kernel.critique.analyze(
            meta_kernel.autopsy.graph.nodes[node_id],
            meta_kernel.autopsy.graph
        )
        return improver.step(critique_result)


_dev_app, _dev_supl = create_app()
app = _dev_app
supl_runtime = _dev_supl
# Route-function references for backward compat (test_r9_api_server_imports)
health = app.routes
ready = app.routes
live = app.routes
version = app.routes
