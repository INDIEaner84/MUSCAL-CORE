import numpy as np


class VectorMemory:
    def __init__(self, dim=384):
        import faiss
        self.index = faiss.IndexFlatL2(dim)
        self.texts = []

    def add(self, vector, text):
        self.index.add(np.array([vector]))
        self.texts.append(text)

    def search(self, vector, k=5):
        D, I = self.index.search(np.array([vector]), k)
        results = []
        for i in I[0]:
            if i < len(self.texts):
                results.append(self.texts[i])
        return results
