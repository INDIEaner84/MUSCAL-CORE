from __future__ import annotations

from pathlib import Path

import pytest

from features.bridge.project_scanner import ProjectScanner, NotARepositoryError


class TestProjectScanner:

    def test_scanner_detects_repository_root(self):
        scanner = ProjectScanner()
        ctx = scanner.scan(Path("."))
        assert ctx.root is not None
        assert ctx.root.exists()

    def test_scanner_detects_branch(self):
        scanner = ProjectScanner()
        ctx = scanner.scan(Path("."))
        assert ctx.branch == "main" or ctx.branch == "detached"

    def test_scanner_detects_commit(self):
        scanner = ProjectScanner()
        ctx = scanner.scan(Path("."))
        assert len(ctx.commit) >= 7

    def test_scanner_detects_dirty_state(self):
        scanner = ProjectScanner()
        ctx = scanner.scan(Path("."))
        assert isinstance(ctx.git.dirty, bool)

    def test_scanner_counts_modified_files(self):
        scanner = ProjectScanner()
        ctx = scanner.scan(Path("."))
        assert isinstance(ctx.git.modified_count, int)
        assert ctx.git.modified_count >= 0

    def test_scanner_counts_untracked_files(self):
        scanner = ProjectScanner()
        ctx = scanner.scan(Path("."))
        assert isinstance(ctx.git.untracked_count, int)
        assert ctx.git.untracked_count >= 0

    def test_scanner_raises_on_non_repo(self, tmp_path: Path):
        scanner = ProjectScanner()
        with pytest.raises(NotARepositoryError):
            scanner.scan(tmp_path)

    def test_project_context_to_dict(self):
        scanner = ProjectScanner()
        ctx = scanner.scan(Path("."))
        d = ctx.to_dict()
        assert "project" in d
        assert "git" in d
        assert "scan" in d
        assert d["project"]["root"] == str(ctx.root.resolve())
        assert d["project"]["branch"] == ctx.branch
        assert d["project"]["commit"] == ctx.commit
        assert d["git"]["dirty"] == ctx.git.dirty
        assert d["git"]["modified_count"] == ctx.git.modified_count
        assert d["git"]["untracked_count"] == ctx.git.untracked_count
