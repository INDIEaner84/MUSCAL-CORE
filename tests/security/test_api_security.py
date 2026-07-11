import json
import os
import time

import pytest


@pytest.fixture
def app():
    from runtime.api import create_app, set_server_ready, _rate_limiter
    _rate_limiter._windows.clear()
    app = create_app()
    app.config["TESTING"] = True
    set_server_ready(True)
    return app.test_client()


class TestContentTypeValidation:
    def test_post_without_json_returns_415(self, app):
        resp = app.post("/api/task", data="not json", content_type="text/plain")
        assert resp.status_code == 415

    def test_post_with_json_succeeds(self, app):
        resp = app.post("/api/task", data=json.dumps({"task": "test"}),
                        content_type="application/json")
        assert resp.status_code in (200, 401)  # 401 = auth required is also valid

    def test_get_unaffected_by_content_type(self, app):
        resp = app.get("/api/health", content_type="text/plain")
        assert resp.status_code == 200


class TestRateLimiter:
    def test_rate_limit_blocks_excess(self, app):
        from runtime.api import _rate_limiter
        _rate_limiter._windows.clear()
        ip = "127.0.0.1"
        path = "/api/test_rate"
        key = f"{ip}:{path}"
        for _ in range(60):
            assert _rate_limiter.check(key, 60, 60)
        assert not _rate_limiter.check(key, 60, 60)

    def test_rate_limit_recovers_after_window(self, app):
        from runtime.api import _rate_limiter
        _rate_limiter._windows.clear()
        key = "test:recovery"
        _rate_limiter._windows[key] = [time.time() - 2.0]
        assert _rate_limiter.check(key, 1, 1)

    def test_cleanup_removes_stale_keys(self, app):
        from runtime.api import _rate_limiter
        _rate_limiter._windows.clear()
        _rate_limiter._windows["stale:key"] = [time.time() - 7200]
        _rate_limiter.cleanup()
        assert "stale:key" not in _rate_limiter._windows


class TestSecurityAuditLog:
    def test_auth_failure_logged(self, app):
        log_path = "storage/security.jsonl"
        if os.path.exists(log_path):
            os.remove(log_path)
        resp = app.post("/api/task", data=json.dumps({"x": 1}),
                        content_type="application/json",
                        headers={"X-API-Key": "wrong"})
        assert resp.status_code == 401
        assert os.path.exists(log_path)
        with open(log_path) as f:
            lines = [json.loads(l) for l in f if l.strip()]
        assert any(e["event"] == "auth_failure" for e in lines)

    def test_rate_limit_logged(self, app):
        from runtime.api import _rate_limiter, _log_security_event
        log_path = "storage/security.jsonl"
        if os.path.exists(log_path):
            os.remove(log_path)
        _rate_limiter._windows.clear()
        _log_security_event("rate_limit", "exceeded 60/min", "127.0.0.1", "/api/test")
        assert os.path.exists(log_path)
        with open(log_path) as f:
            lines = [json.loads(l) for l in f if l.strip()]
        assert any(e["event"] == "rate_limit" for e in lines)

    def test_security_log_file_permissions(self, app):
        log_path = "storage/security.jsonl"
        if os.path.exists(log_path):
            mode = os.stat(log_path).st_mode & 0o777
            assert mode <= 0o600


class TestSecurityHeaders:
    def test_hsts_header_present(self, app):
        resp = app.get("/api/health")
        assert resp.headers.get("Strict-Transport-Security") == "max-age=31536000; includeSubDomains"

    def test_xframe_options_deny(self, app):
        resp = app.get("/api/health")
        assert resp.headers.get("X-Frame-Options") == "DENY"

    def test_xcontent_type_options(self, app):
        resp = app.get("/api/health")
        assert resp.headers.get("X-Content-Type-Options") == "nosniff"

    def test_csp_header_present(self, app):
        resp = app.get("/api/health")
        csp = resp.headers.get("Content-Security-Policy", "")
        assert "default-src 'self'" in csp

    def test_referrer_policy(self, app):
        resp = app.get("/api/health")
        assert resp.headers.get("Referrer-Policy") == "strict-origin-when-cross-origin"
