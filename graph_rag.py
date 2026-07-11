class GraphRAG:
    def __init__(self, graph):
        self.graph = graph

    def retrieve(self, query):
        results = self.graph.query(query)
        related = []
        for node_id in results["nodes"]:
            related.append({
                "node": node_id,
                "content": results["nodes"][node_id],
                "relations": self.graph.get_related(node_id),
            })
        return related


def query_graph_memory(q):
    from mcxf_fusion import get_fusion_layer
    fusion = get_fusion_layer()
    if fusion is None or fusion.graph_rag is None:
        return []
    return fusion.graph_rag.retrieve(q)
