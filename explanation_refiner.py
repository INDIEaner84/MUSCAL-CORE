class ExplanationRefiner:
    def refine(self, explanation, critique):
        if critique["stability"] == "unstable":
            explanation += "\n⚠ Alternative causal paths detected. Explanation confidence reduced."

        if critique["variance"] > 5:
            explanation += "\n⚠ High divergence between possible outcomes."

        return explanation
