class WeightedConsensus:
    def __init__(self, trust):
        self.trust = trust

    def decide(self, results):
        scores = {}

        for r in results:
            value = str(r["result"])
            weight = self.trust.get(r["node"])

            if value not in scores:
                scores[value] = 0

            scores[value] += weight

        winner = max(scores, key=scores.get)

        return {
            "decision": winner,
            "weighted_votes": scores
        }
