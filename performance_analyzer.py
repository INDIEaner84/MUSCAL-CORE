class PerformanceAnalyzer:
    def score(self, critique_result):
        stability = 1.0 if critique_result["stability"] == "stable" else 0.5
        variance = critique_result["variance"]

        return stability - (variance * 0.1)
