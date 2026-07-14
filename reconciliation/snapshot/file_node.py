from __future__ import annotations

import os
from dataclasses import dataclass, field


@dataclass
class FileNode:
    rel_path: str
    abs_path: str
    size: int
    extension: str
    directory: str
    filename: str
    modified: float
    _hash: str | None = field(default=None, repr=False)

    @property
    def hash(self) -> str:
        if self._hash is None:
            msg = f"Hash not set for {self.rel_path}; use HashCache to populate"
            raise ValueError(msg)
        return self._hash

    @classmethod
    def from_abs_path(cls, abs_path: str, repo_root: str) -> FileNode:
        rel_path = os.path.relpath(abs_path, repo_root)
        stat = os.stat(abs_path)
        ext = os.path.splitext(abs_path)[1]
        directory = os.path.dirname(rel_path)
        if directory == ".":
            directory = ""
        return cls(
            rel_path=rel_path,
            abs_path=abs_path,
            size=stat.st_size,
            extension=ext,
            directory=directory,
            filename=os.path.basename(abs_path),
            modified=stat.st_mtime,
        )
