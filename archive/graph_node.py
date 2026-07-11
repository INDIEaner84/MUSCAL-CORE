class GraphNode:
    def __init__(self, node_id, node_type, payload):
        self.id = node_id
        self.type = node_type
        self.payload = payload
        self.edges = []
