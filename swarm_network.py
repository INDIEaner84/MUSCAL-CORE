class SwarmNetwork:
    def __init__(self, nodes):
        self.nodes = nodes

    def broadcast(self, task):
        results = []

        for node in self.nodes:
            try:
                r = node.receive(task)
                results.append({
                    "node": node.id,
                    "result": r
                })
            except:
                results.append({
                    "node": node.id,
                    "result": "FAILED"
                })

        return results
