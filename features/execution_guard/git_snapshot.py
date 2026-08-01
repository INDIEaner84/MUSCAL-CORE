from __future__ import annotations

import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from .models import GitSnapshot


class GitSnapshotter:

    def __init__(self, path: Optional[Path] = None):
        self._path = path

    def snapshot(self, path: Optional[Path] = None) -> GitSnapshot:
        target = path or self._path or Path.cwd()
        root = self._resolve_root(target)
        branch = self._get_branch(root)
        commit = self._get_commit(root)
        modified, untracked = self._get_changed_files(root)
        dirty = len(modified) > 0 or len(untracked) > 0

        return GitSnapshot(
            repository_root=root,
            branch=branch,
            commit=commit,
            dirty=dirty,
            modified_files=modified,
            untracked_files=untracked,
            timestamp=datetime.now(timezone.utc).isoformat(),
        )

    def detect_changes(self, pre: GitSnapshot, post: GitSnapshot) -> list[str]:
        changed: list[str] = []
        pre_set = set(pre.modified_files + pre.untracked_files)
        post_set = set(post.modified_files + post.untracked_files)

        added = post_set - pre_set
        removed = pre_set - post_set
        still_modified = pre_set & post_set

        for f in sorted(added):
            changed.append(f"+{f}")
        for f in sorted(removed):
            changed.append(f"-{f}")
        for f in sorted(still_modified):
            changed.append(f"~{f}")

        if pre.commit != post.commit:
            changed.insert(0, f"commit: {pre.commit} -> {post.commit}")

        return changed

    def _resolve_root(self, path: Path) -> Path:
        result = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            capture_output=True, text=True, timeout=10, cwd=path,
        )
        if result.returncode != 0:
            raise NotGitRepositoryError(f"Not a git repository: {path}")
        return Path(result.stdout.strip())

    def _get_branch(self, root: Path) -> str:
        result = subprocess.run(
            ["git", "branch", "--show-current"],
            capture_output=True, text=True, timeout=10, cwd=root,
        )
        return result.stdout.strip() or "detached"

    def _get_commit(self, root: Path) -> str:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            capture_output=True, text=True, timeout=10, cwd=root,
        )
        return result.stdout.strip()

    def _get_changed_files(self, root: Path) -> tuple[list[str], list[str]]:
        result = subprocess.run(
            ["git", "status", "--porcelain"],
            capture_output=True, text=True, timeout=10, cwd=root,
        )
        lines = [l for l in result.stdout.splitlines() if l.strip()]
        modified: list[str] = []
        untracked: list[str] = []
        for line in lines:
            if line.startswith("??"):
                untracked.append(line[3:])
            else:
                modified.append(line[3:])
        return modified, untracked


class NotGitRepositoryError(Exception):
    pass
