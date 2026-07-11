class BrowserExecutor:
    def __init__(self, agent):
        self.agent = agent

    def run_step(self, step):
        tool = step["tool"]
        args = step.get("args", {})
        return self.agent.execute({"tool": tool, "args": args})
