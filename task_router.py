class TaskRouter:
    def route(self, nodes, task):
        target = nodes[0]

        self.send(target, task)

    def send(self, node, task):
        node.receive({
            "type": "TASK",
            "tool": task["tool"],
            "args": task["args"]
        })
