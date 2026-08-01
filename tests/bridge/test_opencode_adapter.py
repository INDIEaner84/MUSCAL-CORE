from __future__ import annotations

from pathlib import Path

import pytest

from features.bridge.opencode_adapter import OpenCodeAdapter, OpenCodeResult


class TestOpenCodeAdapter:

    def test_help_command_succeeds(self):
        adapter = OpenCodeAdapter()
        result = adapter.execute("--help")
        assert result.status == "completed"
        assert result.return_code == 0

    def test_nonexistent_opencode_returns_not_found(self):
        adapter = OpenCodeAdapter(opencode_path="/nonexistent/opencode")
        result = adapter.execute("test")
        assert result.status == "not-found"

    def test_timeout_returns_timeout_status(self):
        adapter = OpenCodeAdapter(timeout=0)
        result = adapter.execute("test")
        assert result.status == "timeout"

    def test_build_command_with_session(self):
        adapter = OpenCodeAdapter()
        cmd = adapter._build_command("hello", workdir=None, session="ses_123", model=None, agent=None)
        assert "-s" in cmd
        assert "ses_123" in cmd

    def test_build_command_with_model(self):
        adapter = OpenCodeAdapter()
        cmd = adapter._build_command("hello", workdir=None, session=None, model="gpt-4", agent=None)
        assert "-m" in cmd
        assert "gpt-4" in cmd

    def test_build_command_with_agent(self):
        adapter = OpenCodeAdapter()
        cmd = adapter._build_command("hello", workdir=None, session=None, model=None, agent="my-agent")
        assert "--agent" in cmd
        assert "my-agent" in cmd

    def test_build_command_with_attach_url(self):
        adapter = OpenCodeAdapter()
        cmd = adapter._build_command("hello", workdir=None, session=None, model=None, agent=None, attach_url="http://127.0.0.1:8080")
        assert "--attach" in cmd
        assert "http://127.0.0.1:8080" in cmd
        assert "--format" in cmd
        assert "json" in cmd

    def test_build_command_attach_and_session(self):
        adapter = OpenCodeAdapter()
        cmd = adapter._build_command("hello", workdir=None, session="ses_123", model=None, agent=None, attach_url="http://localhost:9000")
        assert "--attach" in cmd
        assert "http://localhost:9000" in cmd
        assert "-s" in cmd
        assert "ses_123" in cmd

    def test_execute_with_attach_url(self):
        adapter = OpenCodeAdapter(attach_url="http://127.0.0.1:8080")
        cmd = adapter._build_command("hello", workdir=None, session=None, model=None, agent=None, attach_url="http://127.0.0.1:8080")
        assert "--attach" in cmd
        assert "http://127.0.0.1:8080" in cmd

    def test_execute_with_per_call_attach(self):
        adapter = OpenCodeAdapter()
        cmd = adapter._build_command("hello", workdir=None, session=None, model=None, agent=None, attach_url="http://localhost:8080")
        assert "--attach" in cmd

    def test_extract_session_from_stdout(self):
        adapter = OpenCodeAdapter()
        result = adapter._extract_session(
            "session: ses_abc123def\nSome output",
            "",
        )
        assert result == "ses_abc123def"

    def test_extract_session_returns_none_when_missing(self):
        adapter = OpenCodeAdapter()
        result = adapter._extract_session("no session here", "no session here")
        assert result is None

    def test_opencode_result_dataclass(self):
        result = OpenCodeResult(
            status="completed",
            return_code=0,
            duration=1.5,
            stdout="ok",
            stderr="",
            session_reference="ses_123",
        )
        assert result.status == "completed"
        assert result.return_code == 0
        assert result.duration == 1.5
        assert result.stdout == "ok"
