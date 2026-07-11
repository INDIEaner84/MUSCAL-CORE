class MemoryCompressor:
    def __init__(self, graph):
        self.graph = graph

    def compress(self):
        compressed = {}

        for a, r, b in self.graph.edges:
            key = (self.graph.nodes[a], r)

            if key not in compressed:
                compressed[key] = set()

            compressed[key].add(self.graph.nodes[b])

        return {k: list(v) for k, v in compressed.items()}
