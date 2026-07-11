import json
import os


class MCXFMemoryStore:
    def __init__(self, path="mcxf_memory.json"):
        self.path = path
        self.data = self._load()

    def _load(self):
        if not os.path.exists(self.path):
            return []
        with open(self.path, "r", encoding="utf-8") as f:
            return json.load(f)

    def save(self):
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump(self.data, f, indent=2)

    def add(self, mcxf_doc):
        self.data.append(mcxf_doc)
        self.save()

    def all(self):
        return self.data

    @property
    def count(self):
        return len(self.data)
