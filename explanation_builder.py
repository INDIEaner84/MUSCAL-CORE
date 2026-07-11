class ExplanationBuilder:
    def build(self, analysis, causality):
        return {
            "explanation": (
                f"This decision was triggered by {len(causality['causes'])} prior events "
                f"and influenced {len(causality['effects'])} downstream actions."
            ),
            "causal_path": causality
        }
