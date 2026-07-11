import os
import time

import pytest


# ── RateLimiter ───────────────────────────────────────────────────────

class TestRateLimiter:
    def test_allow_within_limit(self):
        from runtime.api import _RateLimiter
        rl = _RateLimiter()
        assert rl.check("test", max_requests=3, window_seconds=10)
        assert rl.check("test", max_requests=3, window_seconds=10)
        assert rl.check("test", max_requests=3, window_seconds=10)

    def test_block_when_exceeded(self):
        from runtime.api import _RateLimiter
        rl = _RateLimiter()
        for _ in range(3):
            rl.check("test", max_requests=3, window_seconds=10)
        assert not rl.check("test", max_requests=3, window_seconds=10)

    def test_independent_keys(self):
        from runtime.api import _RateLimiter
        rl = _RateLimiter()
        for _ in range(5):
            rl.check("a", max_requests=5, window_seconds=10)
        assert rl.check("b", max_requests=5, window_seconds=10)

    def test_expired_window(self):
        from runtime.api import _RateLimiter
        rl = _RateLimiter()
        rl._windows["exp_test"] = [time.time() - 20]
        assert rl.check("exp_test", max_requests=1, window_seconds=10)

    def test_cleanup_removes_old(self):
        from runtime.api import _RateLimiter
        rl = _RateLimiter()
        rl._windows["stale"] = [time.time() - 4000]
        rl._windows["fresh"] = [time.time() - 100]
        rl.cleanup()
        assert "stale" not in rl._windows
        assert "fresh" in rl._windows


# ── Auth ──────────────────────────────────────────────────────────────

class TestApiAuth:
    def test_is_auth_required_public_paths(self):
        from runtime.api import _is_auth_required
        assert not _is_auth_required("/api/health", "GET")
        assert not _is_auth_required("/api/state", "GET")
        assert not _is_auth_required("/api/live", "GET")

    def test_is_auth_required_options(self):
        from runtime.api import _is_auth_required
        assert not _is_auth_required("/api/admin", "OPTIONS")

    def test_is_auth_required_get_without_prefix(self):
        from runtime.api import _is_auth_required
        assert not _is_auth_required("/api/chat", "GET")

    def test_is_auth_required_admin_get(self):
        from runtime.api import _is_auth_required
        assert _is_auth_required("/api/admin", "GET")

    def test_is_auth_required_admin_get_with_token(self):
        from runtime.api import _is_auth_required
        assert _is_auth_required("/api/admin", "GET")


# ── Auth Token ────────────────────────────────────────────────────────

class TestGetAuthToken:
    def test_from_env(self, monkeypatch):
        monkeypatch.setenv("MUSCAL_API_KEY", "test-key-123")
        from runtime.api import _get_auth_token
        assert _get_auth_token() == "test-key-123"

    def test_fallback_to_session_id(self, monkeypatch):
        monkeypatch.delenv("MUSCAL_API_KEY", raising=False)
        import importlib
        import runtime.api
        importlib.reload(runtime.api)
        from runtime.api import _get_auth_token
        import config
        assert _get_auth_token() == config.SESSION_ID


# ── Security Event Logging ────────────────────────────────────────────

class TestLogSecurityEvent:
    def test_writes_to_file(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        from runtime.api import _log_security_event
        _log_security_event("test_event", "test detail", "127.0.0.1", "/api/test")
        log_path = tmp_path / "storage" / "security.jsonl"
        assert log_path.exists()
        content = log_path.read_text()
        assert "test_event" in content
        assert "127.0.0.1" in content
        assert "/api/test" in content

    def test_multiple_entries(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        from runtime.api import _log_security_event
        _log_security_event("e1", "d1", "1.1.1.1", "/a")
        _log_security_event("e2", "d2", "2.2.2.2", "/b")
        log_path = tmp_path / "storage" / "security.jsonl"
        lines = log_path.read_text().strip().split("\n")
        assert len(lines) == 2
