class LoopController:
    def __init__(self, max_iterations=5):
        self.max_iterations = max_iterations
        self.iteration = 0
        self.history = []

    def should_continue(self, feedback):
        if self.iteration >= self.max_iterations:
            return False, "MAX_ITERATIONS_REACHED"
        if feedback.get("status") == "SUCCESS":
            return False, "GOAL_REACHED"
        return True, "CONTINUE"

    def step(self):
        self.iteration += 1
