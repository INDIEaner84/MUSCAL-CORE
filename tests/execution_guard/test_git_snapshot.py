from __future__ import annotations

from pathlib import Path

import pytest

from features.execution_guard.git_snapshot import GitSnapshotter, NotGitRepositoryError


class TestGitSnapshotter:

    def test_snapshot_clean_repo(self, tmp_path: Path):
        repo = tmp_path / "clean_repo"
        repo.mkdir()
        import subprocess
        subprocess.run(["git", "init"], cwd=repo, capture_output=True)
        subprocess.run(["git", "config", "user.email", "test@test"], cwd=repo, capture_output=True)
        subprocess.run(["git", "config", "user.name", "test"], cwd=repo, capture_output=True)
        (repo / "test.txt").write_text("hello")
        subprocess.run(["git", "add", "."], cwd=repo, capture_output=True)
        subprocess.run(["git", "commit", "-m", "init"], cwd=repo, capture_output=True)

        snapper = GitSnapshotter()
        snap = snapper.snapshot(repo)
        assert snap.dirty is False
        assert snap.branch == "master" or snap.branch == "main"
        assert len(snap.commit) >= 7
        assert snap.modified_files == []
        assert snap.untracked_files == []

    def test_snapshot_dirty_repo(self, tmp_path: Path):
        repo = tmp_path / "dirty_repo"
        repo.mkdir()
        import subprocess
        subprocess.run(["git", "init"], cwd=repo, capture_output=True)
        subprocess.run(["git", "config", "user.email", "test@test"], cwd=repo, capture_output=True)
        subprocess.run(["git", "config", "user.name", "test"], cwd=repo, capture_output=True)
        (repo / "existing.txt").write_text("hello")
        subprocess.run(["git", "add", "."], cwd=repo, capture_output=True)
        subprocess.run(["git", "commit", "-m", "init"], cwd=repo, capture_output=True)
        (repo / "modified.txt").write_text("changed")
        (repo / "new.txt").write_text("new file")

        snapper = GitSnapshotter()
        snap = snapper.snapshot(repo)
        assert snap.dirty is True

    def test_snapshot_detects_branch(self):
        snapper = GitSnapshotter()
        snap = snapper.snapshot(Path("."))
        assert snap.branch is not None
        assert len(snap.branch) > 0

    def test_snapshot_detects_commit(self):
        snapper = GitSnapshotter()
        snap = snapper.snapshot(Path("."))
        assert len(snap.commit) >= 7

    def test_snapshot_raises_on_non_repo(self, tmp_path: Path):
        snapper = GitSnapshotter()
        with pytest.raises(NotGitRepositoryError):
            snapper.snapshot(tmp_path)

    def test_detect_no_changes(self, tmp_path: Path):
        repo = tmp_path / "no_change_repo"
        repo.mkdir()
        import subprocess
        subprocess.run(["git", "init"], cwd=repo, capture_output=True)
        subprocess.run(["git", "config", "user.email", "test@test"], cwd=repo, capture_output=True)
        subprocess.run(["git", "config", "user.name", "test"], cwd=repo, capture_output=True)
        (repo / "a.txt").write_text("hello")
        subprocess.run(["git", "add", "."], cwd=repo, capture_output=True)
        subprocess.run(["git", "commit", "-m", "init"], cwd=repo, capture_output=True)

        snapper = GitSnapshotter()
        pre = snapper.snapshot(repo)
        post = snapper.snapshot(repo)
        changes = snapper.detect_changes(pre, post)
        assert len(changes) == 0

    def test_detect_added_file(self, tmp_path: Path):
        repo = tmp_path / "added_repo"
        repo.mkdir()
        import subprocess
        subprocess.run(["git", "init"], cwd=repo, capture_output=True)
        subprocess.run(["git", "config", "user.email", "test@test"], cwd=repo, capture_output=True)
        subprocess.run(["git", "config", "user.name", "test"], cwd=repo, capture_output=True)
        (repo / "a.txt").write_text("hello")
        subprocess.run(["git", "add", "."], cwd=repo, capture_output=True)
        subprocess.run(["git", "commit", "-m", "init"], cwd=repo, capture_output=True)

        snapper = GitSnapshotter()
        pre = snapper.snapshot(repo)
        (repo / "new.txt").write_text("new")
        post = snapper.snapshot(repo)
        changes = snapper.detect_changes(pre, post)
        assert any("+new.txt" in c for c in changes) or any("+ new.txt" in c for c in changes)
