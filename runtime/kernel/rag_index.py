"""RAG-Index für MUSCAL-Wissen.
Liest kernel/docs/alita_wissen.md, embeddet Chunks via Ollama (nomic-embed-text),
cached auf Disk, sucht per Cosine Similarity.
"""

import json
import logging
import math
import re
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Optional

log = logging.getLogger(__name__)

OLLAMA_BASE = "http://localhost:11434"
EMBED_MODEL = "nomic-embed-text"
WISSEN_PATH = Path(__file__).parent / "docs" / "alita_wissen.md"
CACHE_PATH = Path(__file__).parent / "data" / "wissen_cache.json"

CHUNK_HEADER_PATTERN = re.compile(r"^##\s+\d+\.\s+(.+)", re.MULTILINE)


class RAGIndex:
    def __init__(self, wissen_path: Path = WISSEN_PATH, cache_path: Path = CACHE_PATH):
        self._wissen_path = wissen_path
        self._cache_path = cache_path
        self._chunks: list[str] = []
        self._embeddings: list[list[float]] = []
        self._loaded = False

    def load(self) -> int:
        if not self._wissen_path.exists():
            log.warning("Wissen-Datei nicht gefunden: %s", self._wissen_path)
            return 0
        text = self._wissen_path.read_text(encoding="utf-8")
        self._chunks = self._chunk_document(text)
        log.info("Wissen geladen: %d Chunks aus %s", len(self._chunks), self._wissen_path.name)
        if self._cache_path.exists():
            self._load_cache()
        if not self._embeddings or len(self._embeddings) != len(self._chunks):
            self._embed_all()
            self._save_cache()
        self._loaded = True
        return len(self._chunks)

    def search(self, query: str, k: int = 3) -> list[str]:
        if not self._loaded or not self._chunks:
            return []
        q_emb = self._embed_one(query)
        scores = []
        for i, emb in enumerate(self._embeddings):
            sim = self._cosine_similarity(q_emb, emb)
            scores.append((sim, i))
        scores.sort(key=lambda x: -x[0])
        results = [self._chunks[i] for _, i in scores[:k]]
        log.debug("RAG search '%s' → %d results", query[:50], len(results))
        return results

    def get_context(self, query: str, k: int = 3, max_chars: int = 2000) -> str:
        try:
            chunks = self.search(query, k=k)
        except Exception as e:
            log.warning("RAG search failed: %s", e)
            return ""
        if not chunks:
            return ""
        parts = []
        total = 0
        for c in chunks:
            if total + len(c) > max_chars:
                c = c[: max_chars - total] + "\n[… truncated]"
            parts.append(c)
            total += len(c)
        return "Relevanter Kontext aus Alita/MUSCAL:\n\n" + "\n\n---\n\n".join(parts)

    def _chunk_document(self, text: str) -> list[str]:
        lines = text.split("\n")
        chunks = []
        current = []
        for line in lines:
            if line.startswith("## ") and current:
                chunks.append("\n".join(current).strip())
                current = [line]
            else:
                current.append(line)
        if current:
            chunks.append("\n".join(current).strip())
        return [c for c in chunks if len(c) > 50]

    def _embed_one(self, text: str) -> list[float]:
        payload = json.dumps({"model": EMBED_MODEL, "prompt": text[:2048]}).encode()
        req = urllib.request.Request(
            f"{OLLAMA_BASE}/api/embeddings",
            data=payload,
            method="POST",
            headers={"Content-Type": "application/json"},
        )
        try:
            with urllib.request.urlopen(req, timeout=10) as resp:
                result = json.loads(resp.read())
                return result.get("embedding", [])
        except Exception as e:
            log.warning("Embedding failed: %s", e)
            return [0.0] * 768

    def _embed_all(self):
        log.info("Embedding %d Chunks mit %s ...", len(self._chunks), EMBED_MODEL)
        t0 = time.time()
        self._embeddings = [self._embed_one(c) for c in self._chunks]
        elapsed = time.time() - t0
        log.info("Embedding fertig: %.1fs (%.2fs/Chunk)", elapsed, elapsed / max(len(self._chunks), 1))

    def _cosine_similarity(self, a: list[float], b: list[float]) -> float:
        dot = sum(ai * bi for ai, bi in zip(a, b))
        na = math.sqrt(sum(ai * ai for ai in a))
        nb = math.sqrt(sum(bi * bi for bi in b))
        if na == 0 or nb == 0:
            return 0.0
        return dot / (na * nb)

    def _load_cache(self):
        try:
            data = json.loads(self._cache_path.read_text(encoding="utf-8"))
            if data.get("chunks") == self._chunks:
                self._embeddings = data["embeddings"]
                log.info("Cache geladen: %d Embeddings", len(self._embeddings))
        except (json.JSONDecodeError, KeyError, OSError):
            pass

    def _save_cache(self):
        self._cache_path.parent.mkdir(parents=True, exist_ok=True)
        data = {"chunks": self._chunks, "embeddings": self._embeddings}
        self._cache_path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
        log.info("Cache gespeichert: %s", self._cache_path)


_rag_index: Optional[RAGIndex] = None


def get_rag_index() -> RAGIndex:
    global _rag_index
    if _rag_index is None:
        _rag_index = RAGIndex()
        _rag_index.load()
    return _rag_index


def reload_rag_index() -> int:
    global _rag_index
    _rag_index = RAGIndex()
    return _rag_index.load()
