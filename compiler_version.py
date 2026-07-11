class CompilerVersion:
    def __init__(self):
        self.version = 1
        self.rules = {
            "task_keywords": ["build", "create", "implement"],
            "decision_keywords": ["we decide", "we choose"],
            "ignore_keywords": ["should", "maybe"]
        }

    def evolve(self, feedback_score):
        if feedback_score < 5:
            self.version += 1
            self.rules["task_keywords"].append("improve")
            self.rules["decision_keywords"].append("final")

        return self.rules
