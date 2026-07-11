from mcxf_fusion import _module_fusion


class MCXFCompressionEngine:
    def __init__(self, memory_store, rag):
        self.memory = memory_store
        self.rag = rag

    def compress(self, query=None, top_k=5):
        docs = self.memory.all()
        if query:
            relevant = self.rag.search(query, top_k=top_k)
            relevant = [r["text"] for r in relevant]
        else:
            relevant = [str(d) for d in docs[-top_k:]]

        compressed = self._merge(relevant)
        self.memory.add({
            "type": "COMPRESSED_NODE",
            "content": compressed,
            "sources": relevant,
        })
        return compressed

    def _merge(self, docs):
        merged = {"summary": [], "decisions": [], "tasks": [], "glossary": []}
        for d in docs:
            text = str(d)
            if "DECISION" in text or "decisions" in text.lower():
                merged["decisions"].append(text)
            elif "TASK" in text or "tasks" in text.lower():
                merged["tasks"].append(text)
            elif "means" in text or "defined" in text:
                merged["glossary"].append(text)
            else:
                merged["summary"].append(text)
        return merged


_compression = None


def init_compression(fusion=None):
    global _compression
    f = fusion or _module_fusion
    if f is None:
        raise RuntimeError("init_fusion() must be called before init_compression()")
    _compression = MCXFCompressionEngine(f.memory, f.rag)


def compress(query=None, top_k=5):
    if _compression is None:
        init_compression()
    return _compression.compress(query, top_k)


def periodic_compress(memory_size, threshold=20, query=None, top_k=5):
    if memory_size >= threshold:
        return compress(query=query, top_k=top_k)
    return None


def run_compression_cycle():
    return compress()
