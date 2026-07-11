class ResultCollector:
    def __init__(self):
        self.results = []

    def add(self, node_id, result):
        self.results.append({
            "node": node_id,
            "result": result
        })

    def clear(self):
        self.results = []
