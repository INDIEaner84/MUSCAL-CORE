class GraphContextBuilder:
    def build(self, graph, query):
        related = []

        for node_id, text in graph.nodes.items():
            if query.lower() in text.lower():
                edges = graph.query_related(node_id)

                related.append({
                    "node": text,
                    "edges": edges
                })

        return related
