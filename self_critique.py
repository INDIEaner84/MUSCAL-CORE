from counterfactual_engine import CounterfactualEngine
from scenario_evaluator import ScenarioEvaluator


class SelfCritique:
    def __init__(self):
        self.evaluator = ScenarioEvaluator()
        self.counterfactual = CounterfactualEngine()

    def analyze(self, node, graph_store):
        scenarios = self.counterfactual.generate(node, graph_store)

        scores = [self.evaluator.score(s) for s in scenarios]

        best = max(scores)
        worst = min(scores)

        stability = "stable" if (best - worst) < 3 else "unstable"

        return {
            "scenarios": scenarios,
            "scores": scores,
            "stability": stability,
            "variance": best - worst
        }
