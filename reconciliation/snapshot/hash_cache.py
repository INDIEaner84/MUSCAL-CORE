from __future__ import annotations

import hashlib


class HashCache:
    def __init__(self) -> None:
        self._cache: dict[str, tuple[float, str]] = {}

    def get(self, abs_path: str, mtime: float) -> str:
        cached_mtime, cached_hash = self._cache.get(abs_path, (None, None))  # type: ignore
        if cached_mtime == mtime:
            return cached_hash
        sha256 = self._compute(abs_path)
        self._cache[abs_path] = (mtime, sha256)
        return sha256

    def invalidate(self, abs_path: str) -> None:
        self._cache.pop(abs_path, None)

    def clear(self) -> None:
        self._cache.clear()

    @staticmethod
    def _compute(abs_path: str) -> str:
        h = hashlib.sha256()
        with open(abs_path, "rb") as f:
            while True:
                block = f.read(65536)
                if not block:
                    break
                h.update(block)
        return h.hexdigest()
