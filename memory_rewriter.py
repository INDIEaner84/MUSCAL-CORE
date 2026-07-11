class MemoryRewriter:
    def __init__(self, graph):
        self.graph = graph

    def rewrite(self):
        merged = {}

        for a, r, b in self.graph.edges:
            key = (self.graph.nodes[a], r)

            if key not in merged:
                merged[key] = set()

            merged[key].add(self.graph.nodes[b])

        self.graph.compressed_view = {
            k: list(v) for k, v in merged.items()
        }

        return self.graph.compressed_view
