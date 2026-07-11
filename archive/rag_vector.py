from embedder import Embedder
from vector_memory import VectorMemory


class RAG:
    def __init__(self, embedder=None, store=None):
        self.embedder = embedder or Embedder()
        self.store = store or VectorMemory()

    def add(self, text):
        vec = self.embedder.encode(text)
        self.store.add(vec, text)

    def search(self, query):
        vec = self.embedder.encode(query)
        return self.store.search(vec)
