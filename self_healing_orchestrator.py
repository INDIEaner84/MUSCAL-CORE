from adaptive_router import AdaptiveRouter
from node_trust import NodeTrust
from reconfig_engine import ReconfigEngine
from weighted_consensus import WeightedConsensus


class SelfHealingOrchestrator:
    def __init__(self, nodes):
        self.nodes = nodes
        self.trust = NodeTrust()
        self.consensus = WeightedConsensus(self.trust)
        self.router = AdaptiveRouter(self.trust)
        self.healer = ReconfigEngine(self.trust)

        for n in nodes:
            self.trust.init_node(n.id)

    def run_task(self, task):
        wrapped = {
            "type": "TASK",
            "tool": task["tool"],
            "args": task.get("args", {})
        }

        self.nodes = self.healer.heal(self.nodes)

        active_nodes = self.router.route(self.nodes)

        results = []

        for node in active_nodes:
            try:
                result = node.receive(wrapped)
                score = self._score(result)

                self.trust.update(node.id, score)

                results.append({
                    "node": node.id,
                    "result": result
                })

            except Exception:
                self.trust.update(node.id, 0.0)

        decision = self.consensus.decide(results)

        return decision

    def _score(self, result):
        s = 5
        if result and "error" not in str(result):
            s += 2
        if len(str(result)) > 20:
            s += 1
        return min(s, 10) / 10
