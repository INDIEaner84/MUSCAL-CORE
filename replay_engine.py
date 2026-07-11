class ReplayEngine:
    def __init__(self, store):
        self.store = store

    def replay(self, node_id):
        path = []
        current = self.store.nodes.get(node_id)

        while current:
            path.append(current)
            parents = [
                e[0] for e in self.store.edges if e[1] == current.id
            ]
            current = self.store.nodes.get(parents[0]) if parents else None

        return list(reversed(path))
