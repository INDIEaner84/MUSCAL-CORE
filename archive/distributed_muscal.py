from distributed_orchestrator import DistributedOrchestrator
from global_memory import GlobalMemory


class DistributedMUSCAL:
    def __init__(self, nodes):
        self.orchestrator = DistributedOrchestrator(nodes)
        self.memory = GlobalMemory()

    def run(self, task):
        wrapped = {
            "type": "TASK",
            "tool": task["tool"],
            "args": task.get("args", {})
        }
        decision = self.orchestrator.run_task(wrapped)

        self.memory.commit(decision)

        return decision
