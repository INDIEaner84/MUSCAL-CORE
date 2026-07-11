class ScenarioEvaluator:
    def score(self, scenario):
        base = len(str(scenario["hypothetical_result"]))

        if "ALT_1" in scenario["hypothetical_result"]:
            base -= 1

        return max(0, base)
