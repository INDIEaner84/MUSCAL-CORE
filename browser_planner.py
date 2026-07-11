class UIPlan:
    def __init__(self, steps):
        self.steps = steps
        self.current = 0

    def next(self):
        if self.current < len(self.steps):
            step = self.steps[self.current]
            self.current += 1
            return step
        return None


class BrowserPlanner:
    def __init__(self, llm=None):
        self.llm = llm

    def create_plan(self, task):
        prompt = task.get("instruction", "")
        return UIPlan([
            {"tool": "browser.open", "args": {"url": "https://example.com"}},
            {"tool": "browser.type", "args": {"selector": "input", "text": prompt}},
            {"tool": "browser.click", "args": {"selector": "button"}},
            {"tool": "browser.extract", "args": {"selector": "body"}},
        ])
