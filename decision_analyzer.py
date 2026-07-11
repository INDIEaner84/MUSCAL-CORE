class DecisionAnalyzer:
    def analyze(self, node, causality):
        return {
            "decision": node.payload,
            "cause_count": len(causality["causes"]),
            "effect_count": len(causality["effects"]),
            "stability": "high" if len(causality["causes"]) > 1 else "low"
        }
