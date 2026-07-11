class VisionPlanner:
    def create_action(self, state, task):
        for el in state.elements:
            if el["type"] == "button" and "login" in el["text"].lower():
                return {
                    "tool": "browser.click",
                    "args": {"selector": "button:has-text('Login')"},
                }
        return {
            "tool": "browser.type",
            "args": {"selector": "input", "text": task.get("instruction", "")},
        }
