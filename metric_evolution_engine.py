class MetricEvolutionEngine:
    def evolve(self, metrics, performance_score):
        if performance_score < 0.3:
            metrics.update("variance_penalty", metrics.get("variance_penalty") * 1.1)

        if performance_score > 0.7:
            metrics.update("stability_weight", metrics.get("stability_weight") * 0.95)

        return metrics
