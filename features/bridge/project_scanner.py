from __future__ import annotations

import subprocess
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional


@dataclass
class GitStatus:
    dirty: bool
    modified_count: int
    untracked_count: int


@dataclass
class ProjectContext:
    root: Path
    repository: str
    branch: str
    commit: str
    git: GitStatus
    scan_timestamp: str
    scan_status: str

    def to_dict(self) -> dict:
        return {
            "project": {
                "root": str(self.root.resolve()),
                "repository": self.repository,
                "branch": self.branch,
                "commit": self.commit,
            },
            "git": {
                "dirty": self.git.dirty,
                "modified_count": self.git.modified_count,
                "untracked_count": self.git.untracked_count,
            },
            "scan": {
                "timestamp": self.scan_timestamp,
                "status": self.scan_status,
            },
        }


class ProjectScanner:

    def __init__(self, path: Optional[Path] = None):
        self._path = path

    def scan(self, path: Optional[Path] = None) -> ProjectContext:
        target = path or self._path or Path.cwd()
        root = self._resolve_root(target)
        branch = self._get_branch(root)
        commit = self._get_commit(root)
        repo_type = self._detect_repo_type(root)
        status = self._get_status(root)
        return ProjectContext(
            root=root,
            repository=repo_type,
            branch=branch,
            commit=commit,
            git=status,
            scan_timestamp=datetime.now(timezone.utc).isoformat(),
            scan_status="ok",
        )

    def _resolve_root(self, path: Path) -> Path:
        result = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            capture_output=True, text=True, timeout=10,
            cwd=path,
        )
        if result.returncode != 0:
            raise NotARepositoryError(f"Not a git repository: {path}")
        return Path(result.stdout.strip())

    def _get_branch(self, root: Path) -> str:
        result = subprocess.run(
            ["git", "branch", "--show-current"],
            capture_output=True, text=True, timeout=10,
            cwd=root,
        )
        return result.stdout.strip() or "detached"

    def _get_commit(self, root: Path) -> str:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            capture_output=True, text=True, timeout=10,
            cwd=root,
        )
        return result.stdout.strip()

    def _detect_repo_type(self, root: Path) -> str:
        result = subprocess.run(
            ["git", "remote", "-v"],
            capture_output=True, text=True, timeout=10,
            cwd=root,
        )
        remotes = result.stdout.strip()
        if not remotes:
            return "local-only"
        return "remote"

    def _get_status(self, root: Path) -> GitStatus:
        result = subprocess.run(
            ["git", "status", "--porcelain"],
            capture_output=True, text=True, timeout=10,
            cwd=root,
        )
        lines = [l for l in result.stdout.splitlines() if l.strip()]
        modified = sum(1 for l in lines if l.startswith(" M") or l.startswith("M "))
        untracked = sum(1 for l in lines if l.startswith("??"))
        dirty = len(lines) > 0
        return GitStatus(dirty=dirty, modified_count=modified, untracked_count=untracked)


class NotARepositoryError(Exception):
    pass
