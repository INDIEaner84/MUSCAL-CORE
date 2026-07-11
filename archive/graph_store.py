import warnings

warnings.warn(
    "graph_store.py is deprecated. Use graph_memory.GraphMemory instead.",
    DeprecationWarning, stacklevel=2
)


class GraphStore:
    def __init__(self):
        self.nodes = {}
        self.edges = []

    def add_node(self, node):
        self.nodes[node.id] = node

    def add_edge(self, from_id, to_id):
        self.edges.append((from_id, to_id))
