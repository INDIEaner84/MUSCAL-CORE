from __future__ import annotations

import json
import logging
import os as _os
import time
from collections import defaultdict
from typing import Any, Optional

log = logging.getLogger("muscal.api")

_writer: Optional[Any] = None
_obs_loop: Optional[Any] = None
_policy: Optional[Any] = None
_governance: Optional[Any] = None
_server_ready = False

_AUTH_REQUIRED_GET_PREFIXES = ("/api/admin", "/api/governance", "/api/snapshot", "/api/handoff")
_PUBLIC_PATHS = {"/api/health", "/api/state", "/api/live"}


class _RateLimiter:
    def __init__(self):
        self._windows: dict[str, list[float]] = defaultdict(list)

    def check(self, key: str, max_requests: int, window_seconds: int) -> bool:
        now = time.time()
        cutoff = now - window_seconds
        self._windows[key] = [t for t in self._windows[key] if t > cutoff]
        if len(self._windows[key]) >= max_requests:
            return False
        self._windows[key].append(now)
        return True

    def cleanup(self):
        now = time.time()
        for key in list(self._windows):
            self._windows[key] = [t for t in self._windows[key] if t > now - 3600]
            if not self._windows[key]:
                del self._windows[key]


_rate_limiter = _RateLimiter()


def _log_security_event(event: str, detail: str, ip: str, path: str):
    try:
        entry = json.dumps({
            "timestamp": time.time(),
            "event": event,
            "detail": detail,
            "ip": ip,
            "path": path,
        })
        _os.makedirs("storage", exist_ok=True)
        with _os.fdopen(_os.open("storage/security.jsonl", _os.O_WRONLY | _os.O_CREAT | _os.O_APPEND, 0o600), "a") as f:
            f.write(entry + "\n")
    except Exception:
        pass


def _get_auth_token():
    env_key = _os.environ.get("MUSCAL_API_KEY", "")
    if env_key:
        return env_key
    import config as _cfg
    return getattr(_cfg, "SESSION_ID", "")


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


def set_globals(writer=None, obs_loop=None, policy=None, governance=None):
    global _writer, _obs_loop, _policy, _governance
    _writer = writer
    _obs_loop = obs_loop
    _policy = policy
    _governance = governance


def register_blueprints(app) -> None:
    from runtime.api.admin import bp as admin_bp
    from runtime.api.chat import bp as chat_bp
    from runtime.api.events import bp as events_bp
    from runtime.api.fs import bp as fs_bp
    from runtime.api.handoff import bp as handoff_bp
    from runtime.api.models import bp as models_bp
    from runtime.api.rag import bp as rag_bp
    from runtime.api.state import bp as state_bp
    from runtime.api.tasks import bp as tasks_bp
    from runtime.api.workers import bp as workers_bp
    app.register_blueprint(state_bp)
    app.register_blueprint(tasks_bp)
    app.register_blueprint(workers_bp)
    app.register_blueprint(events_bp)
    app.register_blueprint(chat_bp)
    app.register_blueprint(models_bp)
    app.register_blueprint(rag_bp)
    app.register_blueprint(fs_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(handoff_bp)


_CORS_ORIGINS = [
    "http://localhost",
    "http://127.0.0.1",
    "http://localhost:5000",
    "http://127.0.0.1:5000",
    "http://localhost:8501",
    "http://127.0.0.1:8501",
    "null",
]
_SECURITY_HEADERS = {
    "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
    "X-Frame-Options": "DENY",
    "X-Content-Type-Options": "nosniff",
    "X-XSS-Protection": "0",
    "Content-Security-Policy": "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'",
    "Referrer-Policy": "strict-origin-when-cross-origin",
}


def init_app(app) -> None:
    from flask import jsonify, request

    from runtime.api.errors import api_error
    from runtime.database import init_db
    init_db()

    app.config["MAX_CONTENT_LENGTH"] = 10 * 1024 * 1024

    try:
        from flask_cors import CORS as _CORS
        _CORS(app, origins=_CORS_ORIGINS)
    except ImportError:
        @app.after_request
        def _add_cors(resp):
            origin = request.headers.get("Origin", "")
            if origin in _CORS_ORIGINS or origin.startswith("http://localhost"):
                resp.headers["Access-Control-Allow-Origin"] = origin
            else:
                resp.headers["Access-Control-Allow-Origin"] = "http://localhost"
            resp.headers["Access-Control-Allow-Headers"] = "Content-Type"
            return resp

    @app.after_request
    def _add_security_headers(resp):
        for header, value in _SECURITY_HEADERS.items():
            resp.headers[header] = value
        return resp

    @app.before_request
    def _rewrite_api_version():
        if request.path.startswith("/api/v1/"):
            request.environ["PATH_INFO"] = "/api/" + request.path[len("/api/v1/"):]

    @app.before_request
    def _check_server_ready():
        if not _server_ready and request.path.rstrip("/") not in {"/api/health", "/api/live"}:    
            return jsonify(api_error("Server initializing - please wait", 503)[0]), 503

    @app.before_request
    def _check_content_type():
        if request.method == "POST" and request.path.startswith("/api/"):
            ct = (request.content_type or "").split(";")[0].strip()
            if ct and ct != "application/json":
                return jsonify(api_error("Content-Type must be application/json", 415)[0]), 415

    @app.before_request
    def _check_auth_request():
        if not _is_auth_required(request.path, request.method):
            return
        token = request.headers.get("X-API-Key", "")
        expected = _get_auth_token()
        if token != expected:
            _log_security_event("auth_failure", f"expected={expected!r}, got={token!r}",
                                request.remote_addr or "?", request.path)
            return jsonify(api_error("Unauthorized", 401)[0]), 401

    @app.before_request
    def _check_rate_limit():
        if request.method == "OPTIONS":
            return
        ip = request.remote_addr or "?"
        key = f"{ip}:{request.path}"
        if not _rate_limiter.check(key, 60, 60):
            _log_security_event("rate_limit", "exceeded 60/min", ip, request.path)
            return jsonify(api_error("Too many requests", 429)[0]), 429
        if not _rate_limiter.check(f"{ip}:global", 1000, 3600):
            return jsonify(api_error("Too many requests", 429)[0]), 429

    @app.errorhandler(400)
    @app.errorhandler(403)
    @app.errorhandler(404)
    @app.errorhandler(413)
    @app.errorhandler(429)
    @app.errorhandler(500)
    def _handle_http_error(exc):
        return jsonify(api_error(str(exc) if app.debug else "Internal error", exc.code)[0]), exc.code

    try:
        from flasgger import Swagger
        Swagger(app, template={
            "info": {"title": "MUSCAL CORE API", "version": "1.0"},
            "basePath": "/api",
        })
        log.info("Swagger docs enabled at /apidocs")
    except ImportError:
        log.info("flasgger not installed — Swagger disabled")


def set_server_ready(val: bool = True) -> None:
    global _server_ready
    _server_ready = val


def create_app():
    from flask import Flask, jsonify, request
    app = Flask(__name__)
    init_app(app)
    register_blueprints(app)
    return app
