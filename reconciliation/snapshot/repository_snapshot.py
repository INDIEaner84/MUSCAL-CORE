from __future__ import annotations

import fnmatch
import os
from typing import TYPE_CHECKING

from reconciliation.snapshot.file_node import FileNode
from reconciliation.snapshot.hash_cache import HashCache
from reconciliation.snapshot.tree import DirectoryTree

if TYPE_CHECKING:
    from reconciliation.core.scope import ScanScope


class RepositorySnapshot:
    def __init__(
        self,
        repo_root: str = ".",
        ignore_patterns: list[str] | None = None,
    ) -> None:
        self.repo_root = os.path.abspath(repo_root)
        self._hash_cache = HashCache()
        self._file_nodes: list[FileNode] = []
        self._tree = DirectoryTree()
        self._ignore = ignore_patterns or self._default_ignores()
        self._built = False

    def build(self) -> None:
        if self._built:
            return
        self._walk()
        self._built = True

    @property
    def files(self) -> list[FileNode]:
        self.build()
        return list(self._file_nodes)

    @property
    def tree(self) -> DirectoryTree:
        self.build()
        return self._tree

    def file_node_for(self, path: str) -> FileNode | None:
        self.build()
        node = self._tree.lookup(path)
        return node.file_node if node else None

    def hash_for(self, path: str) -> str | None:
        self.build()
        node = self._tree.lookup(path)
        if node is None or node.file_node is None:
            return None
        fn = node.file_node
        sha256 = self._hash_cache.get(fn.abs_path, fn.modified)
        fn._hash = sha256
        return sha256

    def filter(
        self,
        extension: str | None = None,
        directory: str | None = None,
    ) -> list[FileNode]:
        self.build()

        def pred(f: FileNode) -> bool:
            if extension is not None and f.extension != extension:
                return False
            if directory is not None and f.directory != directory:
                return False
            return True

        return self._tree.filter(pred)

    def glob(self, pattern: str) -> list[FileNode]:
        self.build()
        return self._tree.glob(pattern)

    def to_scan_scope(self) -> ScanScope:
        from reconciliation.core.scope import ScanScope

        return ScanScope(
            repo_root=self.repo_root,
            exclude_patterns=list(self._ignore),
        )

    def invalidate_hash(self, path: str) -> None:
        node = self._tree.lookup(path)
        if node and node.file_node:
            self._hash_cache.invalidate(node.file_node.abs_path)

    def _walk(self) -> None:
        for root, dirs, files in os.walk(self.repo_root):
            rel_root = os.path.relpath(root, self.repo_root)
            if rel_root == ".":
                rel_root = ""

            dirs[:] = [
                d
                for d in dirs
                if not self._is_ignored(
                    os.path.join(rel_root, d) if rel_root else d
                )
            ]

            for fname in files:
                rel_path = os.path.join(rel_root, fname) if rel_root else fname
                if self._is_ignored(rel_path):
                    continue
                abs_path = os.path.join(root, fname)
                file_node = FileNode.from_abs_path(abs_path, self.repo_root)
                sha256 = self._hash_cache.get(
                    file_node.abs_path, file_node.modified
                )
                file_node._hash = sha256
                self._file_nodes.append(file_node)
                self._tree.add(file_node)

    def _is_ignored(self, rel_path: str) -> bool:
        return any(fnmatch.fnmatch(rel_path, pat) for pat in self._ignore)

    @staticmethod
    def _default_ignores() -> list[str]:
        return [
            ".git/**",
            "__pycache__/**",
            "*.pyc",
            "*.pyo",
            ".venv/**",
            "venv/**",
            "*.db",
            "*.sqlite",
            "*.sqlite3",
            ".env",
            ".env.*",
            "*.egg-info/**",
            "build/**",
            "dist/**",
            ".pytest_cache/**",
            ".mypy_cache/**",
            ".ruff_cache/**",
            ".coverage",
            "htmlcov/**",
            "node_modules/**",
            ".DS_Store",
            "Thumbs.db",
            "*.log",
            "*.swp",
            "*.swo",
        ]
