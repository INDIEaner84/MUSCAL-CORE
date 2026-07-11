class CounterfactualEngine:
    def generate(self, node, graph_store):
        data = getattr(node, "payload", getattr(node, "data", ""))

        return [
            {
                "scenario": "A",
                "assumption": "node executed differently",
                "hypothetical_result": str(data) + "_ALT_1"
            },
            {
                "scenario": "B",
                "assumption": "missing causal input removed",
                "hypothetical_result": str(data) + "_ALT_2"
            }
        ]
