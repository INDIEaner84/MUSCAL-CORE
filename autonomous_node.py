class AutonomousNode:
    def __init__(self, node_id, executor):
        self.id = node_id
        self.executor = executor
        self.memory = []
        self.peers = []

    def connect(self, peers):
        self.peers = peers

    def receive(self, task):
        result = self.executor.run(task["tool"], task["args"])

        self.memory.append({
            "task": task,
            "result": result
        })

        self.share(task, result)

        return result

    def share(self, task, result):
        for p in self.peers:
            p.sync({
                "from": self.id,
                "task": task,
                "result": result
            })

    def sync(self, data):
        self.memory.append(data)
