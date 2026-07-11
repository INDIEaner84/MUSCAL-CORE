class ConsensusEngine:
    def decide(self, results):
        votes = {}

        for r in results:
            value = str(r["result"])

            if value not in votes:
                votes[value] = 0

            votes[value] += 1

        winner = max(votes, key=votes.get)

        return {
            "decision": winner,
            "votes": votes
        }
