class CausalityEngine:
    def infer(self, graph, node_id):
        node = graph.get_node(node_id)
        if node is None:
            return {"node": node_id, "causes": [], "effects": []}

        related = graph.get_related(node_id)
        causes = [e["from"] for e in related if e["to"] == node_id]
        effects = [e["to"] for e in related if e["from"] == node_id]

        return {
            "node": node_id,
            "causes": causes,
            "effects": effects
        }
