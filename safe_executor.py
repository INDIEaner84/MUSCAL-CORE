class SafeExecutor:
    def run_node(self, node, task):
        try:
            return node.receive(task)
        except Exception:
            return "NODE_FAILED"
