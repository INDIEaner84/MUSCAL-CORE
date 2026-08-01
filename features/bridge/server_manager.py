from __future__ import annotations

import re
import subprocess
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional


@dataclass
class ServerStatus:
    running: bool
    url: Optional[str]
    pid: Optional[int]
    started_at: Optional[str]
    error: Optional[str] = None


class OpenCodeServerManager:

    def __init__(
        self,
        opencode_path: str = "opencode",
        port: int = 0,
        hostname: str = "127.0.0.1",
        cors: Optional[str] = None,
    ):
        self._opencode_path = opencode_path
        self._port = port
        self._hostname = hostname
        self._cors = cors
        self._process: Optional[subprocess.Popen] = None
        self._url: Optional[str] = None
        self._started_at: Optional[str] = None

    def start(self, workdir: Optional[Path] = None) -> ServerStatus:
        if self._process is not None and self._process.poll() is None:
            return ServerStatus(
                running=True,
                url=self._url,
                pid=self._process.pid,
                started_at=self._started_at,
            )

        cmd = [self._opencode_path, "serve"]
        if self._port:
            cmd.extend(["--port", str(self._port)])
        if self._hostname:
            cmd.extend(["--hostname", self._hostname])
        if self._cors:
            cmd.extend(["--cors", self._cors])

        try:
            self._process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                cwd=workdir or Path.cwd(),
            )
        except FileNotFoundError:
            return ServerStatus(
                running=False, url=None, pid=None,
                started_at=None,
                error=f"OpenCode executable not found: {self._opencode_path}",
            )

        self._started_at = datetime.now(timezone.utc).isoformat()
        self._url = self._wait_for_url(timeout=10)

        return ServerStatus(
            running=self._url is not None,
            url=self._url,
            pid=self._process.pid,
            started_at=self._started_at,
        )

    def _wait_for_url(self, timeout: int = 10) -> Optional[str]:
        deadline = time.time() + timeout
        while time.time() < deadline:
            if self._process is None or self._process.poll() is not None:
                return None
            if self._process.stdout:
                line = self._process.stdout.readline()
                if line:
                    match = re.search(r'(https?://[^\s]+)', line)
                    if match:
                        return match.group(1)
            else:
                time.sleep(0.1)
        return None

    def stop(self) -> None:
        if self._process is not None and self._process.poll() is None:
            self._process.terminate()
            try:
                self._process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self._process.kill()
                self._process.wait(timeout=5)
        self._process = None
        self._url = None
        self._started_at = None

    def is_alive(self) -> bool:
        return self._process is not None and self._process.poll() is None

    def get_url(self) -> Optional[str]:
        return self._url

    def get_status(self) -> ServerStatus:
        return ServerStatus(
            running=self.is_alive(),
            url=self._url,
            pid=self._process.pid if self._process else None,
            started_at=self._started_at,
        )

    def build_attach_command(self, message: str) -> list[str]:
        if not self._url:
            raise RuntimeError("Server not running. Start server first.")
        return [
            self._opencode_path, "run",
            "--attach", self._url,
            "--format", "json",
            "--", message,
        ]
