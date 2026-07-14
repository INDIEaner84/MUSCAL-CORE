from __future__ import annotations

import fnmatch
import os
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from reconciliation.snapshot.repository_snapshot import RepositorySnapshot


@dataclass
class ScanScope:
    include_patterns: list[str] = field(default_factory=lambda: ["**/*"])
    exclude_patterns: list[str] = field(default_factory=list)
    repo_root: str = "."

    @classmethod
    def from_snapshot(cls, snapshot: RepositorySnapshot) -> ScanScope:
        return cls(
            repo_root=snapshot.repo_root,
            exclude_patterns=list(snapshot._ignore),
        )

    def match(self, filepath: str) -> bool:
        included = any(
            fnmatch.fnmatch(filepath, pat) for pat in self.include_patterns
        )
        if not included:
            return False
        excluded = any(
            fnmatch.fnmatch(filepath, pat) for pat in self.exclude_patterns
        )
        return not excluded

    def files(self) -> list[str]:
        result: list[str] = []
        for root, dirs, files in os.walk(self.repo_root):
            rel_root = os.path.relpath(root, self.repo_root)
            if rel_root == ".":
                rel_root = ""
            # Skip excluded directories early
            dirs[:] = [
                d
                for d in dirs
                if not any(
                    fnmatch.fnmatch(
                        os.path.join(rel_root, d), pat
                    )
                    for pat in self.exclude_patterns
                )
            ]
            for fname in files:
                rel_path = os.path.join(rel_root, fname) if rel_root else fname
                if self.match(rel_path):
                    result.append(rel_path)
        return sorted(result)
