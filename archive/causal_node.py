class CausalNode:
    def __init__(self, node_id, data):
        self.id = node_id
        self.data = data
        self.causes = []
        self.effects = []
