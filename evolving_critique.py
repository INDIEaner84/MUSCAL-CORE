class EvolvingCritique:
    def __init__(self, metrics):
        self.metrics = metrics
        self.version = 1

    def evaluate(self, critique_result):
        stability_score = (
            1.0 if critique_result["stability"] == "stable" else 0.5
        ) * self.metrics.get("stability_weight")

        variance_score = critique_result["variance"] * self.metrics.get("variance_penalty")

        score = stability_score - variance_score

        return {
            "score": score,
            "version": self.version
        }
