class ExecutionGovernor:
    def __init__(self, mel_executor, loop_controller):
        self.mel = mel_executor
        self.loop = loop_controller

    def run(self, mcxf_task_plan):
        feedback = {"status": "INIT"}

        while True:
            self.loop.step()

            results = []
            for task in mcxf_task_plan:
                result = self.mel(task)
                results.append(result)

            feedback = self._evaluate(results)

            self.loop.history.append({
                "iteration": self.loop.iteration,
                "results": results,
                "feedback": feedback,
            })

            cont, reason = self.loop.should_continue(feedback)

            if not cont:
                return {
                    "status": "STOPPED",
                    "reason": reason,
                    "history": self.loop.history,
                }

    def _evaluate(self, results):
        success = all(r.get("status") == "executed" for r in results)
        if success:
            return {"status": "SUCCESS"}
        return {"status": "IN_PROGRESS"}
