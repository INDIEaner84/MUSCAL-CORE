from permission_engine import mel_execute
from task_model import Task
from task_queue import TaskQueue


class ResourceManager:
    def __init__(self):
        self.limits = {"cpu": 100, "tool_calls": 50}
        self.usage = {"cpu": 0, "tool_calls": 0}

    def check(self, task):
        if self.usage["tool_calls"] >= self.limits["tool_calls"]:
            return False, "TOOL_LIMIT_REACHED"
        return True, "OK"

    def consume(self, task):
        self.usage["tool_calls"] += 1


class Scheduler:
    def __init__(self, task_queue, resource_manager, executor):
        self.queue = task_queue
        self.rm = resource_manager
        self.executor = executor

    def run(self):
        results = []
        while not self.queue.empty():
            task = self.queue.get_next()
            allowed, reason = self.rm.check(task)
            if not allowed:
                results.append({"task": task.tool, "status": "BLOCKED", "reason": reason})
                continue
            self.rm.consume(task)
            result = self.executor({"tool": task.tool, "args": task.args})
            results.append(result)
        return results


def muscal_runtime(mcxf_tasks):
    queue = TaskQueue()
    rm = ResourceManager()
    for t in mcxf_tasks:
        queue.add(Task(t["tool"], t["args"], t.get("priority", 1)))
    scheduler = Scheduler(queue, rm, mel_execute)
    return scheduler.run()
