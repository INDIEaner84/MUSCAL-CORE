class NodeTrust:
    def __init__(self):
        self.scores = {}

    def init_node(self, node_id):
        self.scores[node_id] = 1.0

    def update(self, node_id, score):
        if node_id not in self.scores:
            self.init_node(node_id)

        self.scores[node_id] = (
            self.scores[node_id] * 0.8 + score * 0.2
        )

    def get(self, node_id):
        return self.scores.get(node_id, 1.0)

    def best_nodes(self, nodes):
        return sorted(
            nodes,
            key=lambda n: self.get(n.id),
            reverse=True
        )
