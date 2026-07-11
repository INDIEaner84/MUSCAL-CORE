class BrowserRouter:
    def __init__(self, agent):
        self.agent = agent

    def run(self, task):
        if task["tool"].startswith("browser."):
            return self.agent.execute(task)
        return {"status": "NOT_BROWSER_TASK", "tool": task.get("tool", "")}
