import numpy as np


class Embedder:
    def __init__(self):
        from sentence_transformers import SentenceTransformer
        self.model = SentenceTransformer("all-MiniLM-L6-v2")

    def encode(self, text):
        return np.array(self.model.encode(text)).astype("float32")
