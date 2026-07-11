class ReasoningEngine:
    def infer(self, multi_hop_data):
        conclusions = []

        for a, relation, b in multi_hop_data:
            if relation == "is":
                conclusions.append(f"{a} defines {b}")

            if relation == "has":
                conclusions.append(f"{a} contains {b}")

        return conclusions
