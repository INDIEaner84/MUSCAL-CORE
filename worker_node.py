class WorkerNode:
    def __init__(self, worker_id, executor):
        self.worker_id = worker_id
        self.executor = executor
        self.busy = False

    def execute(self, task):
        self.busy = True
        try:
            result = self.executor(task)
            return {"worker": self.worker_id, "task": task, "result": result}
        finally:
            self.busy = False
