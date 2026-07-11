from evolving_critique import EvolvingCritique
from metric_evolution_engine import MetricEvolutionEngine
from metric_registry import MetricRegistry
from performance_analyzer import PerformanceAnalyzer


class RecursiveSelfImprover:
    def __init__(self):
        self.metrics = MetricRegistry()
        self.evolver = MetricEvolutionEngine()
        self.critique = EvolvingCritique(self.metrics)
        self.analyzer = PerformanceAnalyzer()

    def step(self, critique_result):
        evaluated = self.critique.evaluate(critique_result)

        performance = self.analyzer.score(critique_result)

        self.metrics = self.evolver.evolve(self.metrics, performance)

        self.critique.version += 1

        return {
            "evaluation": evaluated,
            "metrics": self.metrics.metrics,
            "performance": performance
        }
