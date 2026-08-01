from __future__ import annotations

import json
import shlex
import subprocess
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional


@dataclass
class OpenCodeResult:
    status: str  # completed | failed | timeout | not-found
    return_code: Optional[int]
    duration: float
    stdout: str
    stderr: str
    session_reference: Optional[str]
    raw_artifacts: dict = field(default_factory=dict)


class OpenCodeAdapter:

    def __init__(self, opencode_path: str = "opencode", timeout: int = 120,
                 attach_url: Optional[str] = None):
        self._opencode_path = opencode_path
        self._timeout = timeout
        self._attach_url = attach_url

    def execute(self, message: str, workdir: Optional[Path] = None,
                session: Optional[str] = None,
                model: Optional[str] = None,
                agent: Optional[str] = None,
                attach_url: Optional[str] = None) -> OpenCodeResult:
        url = attach_url or self._attach_url
        cmd = self._build_command(message, workdir, session, model, agent, url)
        start = datetime.now(timezone.utc)

        try:
            proc = subprocess.run(
                cmd,
                capture_output=True, text=True,
                timeout=self._timeout,
                cwd=workdir or Path.cwd(),
            )
        except subprocess.TimeoutExpired:
            duration = (datetime.now(timezone.utc) - start).total_seconds()
            return OpenCodeResult(
                status="timeout",
                return_code=None,
                duration=duration,
                stdout="",
                stderr=f"Process timed out after {self._timeout}s",
                session_reference=None,
            )
        except FileNotFoundError:
            duration = (datetime.now(timezone.utc) - start).total_seconds()
            return OpenCodeResult(
                status="not-found",
                return_code=None,
                duration=duration,
                stdout="",
                stderr=f"OpenCode executable not found: {self._opencode_path}",
                session_reference=None,
            )

        duration = (datetime.now(timezone.utc) - start).total_seconds()
        session_ref = self._extract_session(proc.stdout, proc.stderr)
        raw = {}

        if proc.stdout.strip():
            try:
                raw = json.loads(proc.stdout)
            except (json.JSONDecodeError, ValueError):
                raw = {"raw_stdout": proc.stdout[:10000]}

        return OpenCodeResult(
            status="completed" if proc.returncode == 0 else "failed",
            return_code=proc.returncode,
            duration=duration,
            stdout=proc.stdout,
            stderr=proc.stderr,
            session_reference=session_ref,
            raw_artifacts=raw,
        )

    def _build_command(self, message: str, workdir: Optional[Path],
                       session: Optional[str],
                       model: Optional[str],
                       agent: Optional[str],
                       attach_url: Optional[str] = None) -> list[str]:
        cmd = [self._opencode_path, "run", "--format", "json"]
        if attach_url:
            cmd.extend(["--attach", attach_url])
        if session:
            cmd.extend(["-s", session])
        if model:
            cmd.extend(["-m", model])
        if agent:
            cmd.extend(["--agent", agent])
        cmd.append("--")
        cmd.append(message)
        return cmd

    def _extract_session(self, stdout: str, stderr: str) -> Optional[str]:
        for line in (stdout + stderr).splitlines():
            for prefix in ("session:", "Session:", "session_id:", "sessionId:"):
                if prefix in line:
                    parts = line.split()
                    for p in parts:
                        if p.startswith("ses_"):
                            return p
        return None
