import asyncio
import os
import time
from datetime import datetime, timezone

from fastapi import FastAPI, WebSocket, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from runtime.api.errors import api_error

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

_start_time = time.monotonic()

app = FastAPI(title="MUSCAL Control Plane", docs_url="/docs", redoc_url="/redoc")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost", "http://127.0.0.1"],
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization", "X-API-Key"],
)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        response = await call_next(request)
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-XSS-Protection"] = "0"
        response.headers["Content-Security-Policy"] = "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        return response


app.add_middleware(SecurityHeadersMiddleware)

MAX_BODY_SIZE = 10 * 1024 * 1024

_server_ready = False

_AUTH_REQUIRED_GET_PREFIXES = ("/admin", "/governance", "/snapshot", "/handoff")
_PUBLIC_PATHS = {"/health", "/state"}


def _get_auth_token():
    env_key = os.environ.get("MUSCAL_API_KEY", "")
    if env_key:
        return env_key
    return getattr(config, "SESSION_ID", "")


def _is_auth_required(path: str, method: str) -> bool:
    if method == "OPTIONS":
        return False
    if path.rstrip("/") in _PUBLIC_PATHS:
        return False
    if method == "GET" and not path.startswith(_AUTH_REQUIRED_GET_PREFIXES):
        return False
    expected = _get_auth_token()
    if not expected:
        return False
    return True


@app.middleware("http")
async def limit_content_size(request: Request, call_next):
    cl = request.headers.get("content-length")
    if cl and int(cl) > MAX_BODY_SIZE:
        return JSONResponse(api_error("Request too large", 413)[0], status_code=413)
    return await call_next(request)


@app.middleware("http")
async def check_server_ready(request: Request, call_next):
    if not _server_ready and request.url.path != "/health":
        return JSONResponse(api_error("Server initializing - please wait", 503)[0], status_code=503)
    return await call_next(request)


@app.middleware("http")
async def check_auth(request: Request, call_next):
    if not _is_auth_required(request.url.path, request.method):
        return await call_next(request)
    token = request.headers.get("X-API-Key", "")
    if token != _get_auth_token():
        return JSONResponse(api_error("Unauthorized", 401)[0], status_code=401)
    return await call_next(request)


try:
    from slowapi import Limiter, _rate_limit_exceeded_handler
    from slowapi.util import get_remote_address
    limiter = Limiter(key_func=get_remote_address)
    app.state.limiter = limiter
    app.add_exception_handler(429, _rate_limit_exceeded_handler)
except ImportError:
    limiter = None


def set_server_ready(val: bool = True):
    global _server_ready
    _server_ready = val


@app.get("/health")
def health():
    return {
        "status": "ok",
        "uptime": round(time.monotonic() - _start_time, 2),
        "server_ready": _server_ready,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@app.get("/ready")
def ready():
    if not _server_ready:
        return JSONResponse({"status": "not_ready"}, status_code=503)
    return {"status": "ready", "uptime": round(time.monotonic() - _start_time, 2)}


@app.get("/live")
def live():
    return {"status": "alive"}


@app.get("/version")
def version():
    return {
        "name": "muscal-core",
        "version": "0.7.0",
        "python": os.environ.get("PYTHON_VERSION", "3.12"),
        "session": config.SESSION_ID,
    }


control = None

store = GraphStore()
replay_engine = ReplayEngine(store)
autopsy = DecisionAutopsy(store)
meta_kernel = MetaReasoningKernel(autopsy)
improver = RecursiveSelfImprover()


@app.post("/task")
def submit_task(task: dict):
    return control.run_task(task["input"])


@app.get("/nodes")
def get_nodes():
    return [{"id": n.id} for n in control.swarm.nodes]


def _ws_check_token(ws: WebSocket) -> bool:
    token = ws.query_params.get("token", ws.headers.get("X-API-Key", ""))
    return token == _get_auth_token()


@app.websocket("/stream")
async def stream(ws: WebSocket):
    if not _ws_check_token(ws):
        await ws.close(code=4001)
        return
    await ws.accept()

    while True:
        for event in control.events:
            await ws.send_json(event)

        await asyncio.sleep(1)


@app.get("/graph")
def get_graph():
    return {
        "nodes": [{"id": n.id, "type": n.type, "payload": n.payload} for n in store.nodes.values()],
        "edges": store.edges
    }


@app.get("/replay/{node_id}")
def replay(node_id: str):
    return replay_engine.replay(node_id)


@app.websocket("/graph/stream")
async def graph_stream(ws: WebSocket):
    if not _ws_check_token(ws):
        await ws.close(code=4001)
        return
    await ws.accept()

    while True:
        data = {
            "type": "graph_update",
            "nodes": len(store.nodes),
            "edges": len(store.edges)
        }
        await ws.send_json(data)
        await asyncio.sleep(1)


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
