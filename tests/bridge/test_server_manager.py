from __future__ import annotations

from pathlib import Path

from features.bridge.server_manager import OpenCodeServerManager, ServerStatus


class TestOpenCodeServerManager:

    def test_init_defaults(self):
        mgr = OpenCodeServerManager()
        assert mgr._opencode_path == "opencode"
        assert mgr._port == 0
        assert mgr._hostname == "127.0.0.1"
        assert mgr._cors is None

    def test_not_running_initially(self):
        mgr = OpenCodeServerManager()
        assert not mgr.is_alive()
        assert mgr.get_url() is None

    def test_get_status_not_running(self):
        mgr = OpenCodeServerManager()
        status = mgr.get_status()
        assert not status.running
        assert status.url is None
        assert status.pid is None

    def test_start_nonexistent_opencode(self):
        mgr = OpenCodeServerManager(opencode_path="/nonexistent/opencode")
        status = mgr.start()
        assert not status.running
        assert status.error is not None
        assert "not found" in status.error.lower()

    def test_server_status_dataclass(self):
        status = ServerStatus(
            running=True,
            url="http://127.0.0.1:8080",
            pid=12345,
            started_at="2026-07-28T12:00:00",
        )
        assert status.running
        assert status.url == "http://127.0.0.1:8080"
        assert status.pid == 12345

    def test_server_status_with_error(self):
        status = ServerStatus(
            running=False,
            url=None,
            pid=None,
            started_at=None,
            error="Something went wrong",
        )
        assert not status.running
        assert status.error == "Something went wrong"

    def test_is_alive_after_stop(self):
        mgr = OpenCodeServerManager()
        mgr.stop()
        assert not mgr.is_alive()

    def test_build_attach_command_raises_when_not_running(self):
        mgr = OpenCodeServerManager()
        try:
            mgr.build_attach_command("test message")
            assert False, "Should have raised RuntimeError"
        except RuntimeError as e:
            assert "Server not running" in str(e)

    def test_stop_idempotent(self):
        mgr = OpenCodeServerManager()
        mgr.stop()
        mgr.stop()
        assert not mgr.is_alive()
