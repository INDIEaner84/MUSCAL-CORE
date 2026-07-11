"""
ChromaDB persistenter Vektor-Index für MUSCAL.
Ersetzt den JSON-Cache in rag_index.py langfristig.
"""

import logging
from pathlib import Path
from typing import Optional

import chromadb
from chromadb.config import Settings

log = logging.getLogger(__name__)

CHROMA_PATH = Path(__file__).parent / "data" / "chroma"
COLLECTION_NAME = "muscal_wissen"
EMBED_MODEL = "nomic-embed-text"
OLLAMA_EMBED_URL = "http://localhost:11434/api/embeddings"


class ChromaIndex:
    def __init__(self, persist_path: Path = CHROMA_PATH):
        self._client = chromadb.PersistentClient(
            path=str(persist_path),
            settings=Settings(anonymized_telemetry=False),
        )
        self._collection: Optional[chromadb.Collection] = None
        self._loaded = False

    def _get_or_create_collection(self) -> chromadb.Collection:
        try:
            return self._client.get_collection(COLLECTION_NAME)
        except Exception:
            return self._client.create_collection(COLLECTION_NAME)

    def _ollama_embed(self, text: str) -> list[float]:
        """Single embedding via Ollama (nomic-embed-text)."""
        import json
        import urllib.request
        req = urllib.request.Request(
            OLLAMA_EMBED_URL,
            data=json.dumps({"model": EMBED_MODEL, "prompt": text}).encode(),
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read())["embedding"]

    def load(self) -> int:
        self._collection = self._get_or_create_collection()
        count = self._collection.count()
        self._loaded = True
        log.info("ChromaDB geladen: %d Dokumente in '%s'", count, COLLECTION_NAME)
        return count

    def add_document(self, doc_id: str, text: str, metadata: Optional[dict] = None) -> None:
        if self._collection is None:
            self._collection = self._get_or_create_collection()
        embedding = self._ollama_embed(text)
        self._collection.add(
            ids=[doc_id],
            embeddings=[embedding],
            documents=[text],
            metadatas=[metadata or {}],
        )
        log.debug("ChromaDB add: %s (%d chars)", doc_id, len(text))

    def add_chunks_from_wissen(self, wissen_path: Path) -> int:
        """Lies kernel/docs/alita_wissen.md, Chunk it, embed + store."""
        if not wissen_path.exists():
            log.warning("Wissen-Datei nicht gefunden: %s", wissen_path)
            return 0

        text = wissen_path.read_text(encoding="utf-8")
        chunks = self._chunk_document(text)
        existing = self._collection.count() if self._collection else 0

        # Nur hinzufügen, wenn Collection leer ist
        if existing > 0:
            log.info("ChromaDB hat bereits %d Einträge – überspringe Bootstrap", existing)
            return existing

        for i, chunk in enumerate(chunks):
            title = f"wissen_chunk_{i:03d}"
            self.add_document(
                doc_id=title,
                text=chunk,
                metadata={"source": str(wissen_path.name), "chunk": i, "total": len(chunks)},
            )

        log.info("ChromaDB Bootstrap: %d Chunks aus %s", len(chunks), wissen_path.name)
        return len(chunks)

    def search(self, query: str, k: int = 5) -> list[dict]:
        if self._collection is None or self._collection.count() == 0:
            return []
        q_emb = self._ollama_embed(query)
        results = self._collection.query(query_embeddings=[q_emb], n_results=k)
        out = []
        for i in range(len(results["ids"][0])):
            out.append({
                "id": results["ids"][0][i],
                "text": results["documents"][0][i][:500],
                "score": float(results["distances"][0][i]) if results.get("distances") else 0.0,
            })
        return out

    @staticmethod
    def _chunk_document(text: str, max_chars: int = 1500) -> list[str]:
        """Simple chunking by header (##)."""
        import re
        header_pat = re.compile(r"^(##\s+.+)$", re.MULTILINE)
        parts = header_pat.split(text)
        chunks = []
        current = ""
        for part in parts:
            if part.startswith("## "):
                if current:
                    chunks.append(current.strip())
                current = part + "\n"
            else:
                current += part
                if len(current) >= max_chars:
                    chunks.append(current.strip())
                    current = ""
        if current.strip():
            chunks.append(current.strip())
        return [c for c in chunks if c]


# Singleton
_chroma_index: Optional[ChromaIndex] = None


def get_chroma_index() -> ChromaIndex:
    global _chroma_index
    if _chroma_index is None:
        _chroma_index = ChromaIndex()
        _chroma_index.load()
    return _chroma_index


def bootstrap_chroma(wissen_path: Optional[Path] = None) -> int:
    """Einmalig: Wissen-Dokumente in ChromaDB laden."""
    idx = get_chroma_index()
    wp = wissen_path or (Path(__file__).parent / "docs" / "alita_wissen.md")
    return idx.add_chunks_from_wissen(wp)


def search_chroma(query: str, k: int = 5) -> list[dict]:
    return get_chroma_index().search(query, k=k)
