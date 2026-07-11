class EmergentConsensus:
    def decide(self, swarm_results):
        freq = {}

        for r in swarm_results:
            val = str(r["result"])

            if val not in freq:
                freq[val] = 0

            freq[val] += 1

        return {
            "emergent_state": max(freq, key=freq.get),
            "distribution": freq
        }
