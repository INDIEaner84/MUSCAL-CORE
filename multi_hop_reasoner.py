class MultiHopReasoner:
    def __init__(self, graph):
        self.graph = graph

    def expand(self, start_text, depth=2):
        visited = set()
        frontier = []

        seeds = [
            n for n, t in self.graph.nodes.items()
            if start_text.lower() in t.lower()
        ]

        frontier.extend(seeds)

        result = []

        for _ in range(depth):
            next_frontier = []

            for node in frontier:
                if node in visited:
                    continue

                visited.add(node)

                edges = self.graph.query_related(node)

                for e in edges:
                    result.append(e)
                    next_frontier.append(e[2])

            frontier = next_frontier

        return result
