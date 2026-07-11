from consensus_engine import ConsensusEngine
from result_collector import ResultCollector
from safe_executor import SafeExecutor


class DistributedOrchestrator:
    def __init__(self, nodes):
        self.nodes = nodes
        self.collector = ResultCollector()
        self.consensus = ConsensusEngine()
        self.executor = SafeExecutor()

    def run_task(self, task):
        for node in self.nodes:
            result = self.executor.run_node(node, task)
            self.collector.add(node.id, result)

        decision = self.consensus.decide(self.collector.results)

        self.collector.clear()

        return decision
