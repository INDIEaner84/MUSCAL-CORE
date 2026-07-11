from browser_engine import BrowserEngine
from safe_browser_agent import SafeBrowserAgent
from state_builder import StateBuilder
from vision_layer import VisionLayer
from vision_planner import VisionPlanner


class VisionLoop:
    def __init__(self, browser, vision, planner):
        self.browser = browser
        self.vision = vision
        self.planner = planner

    def run(self, task):
        self.browser.execute({"tool": "browser.open", "args": {"url": "about:blank"}})
        screenshot = self.browser.execute({"tool": "browser.extract", "args": {"selector": "body"}})
        state = StateBuilder(self.vision).build("screen.png")
        action = self.planner.create_action(state, task)
        result = self.browser.execute(action)
        return {
            "state": state.description,
            "action": action,
            "result": result,
        }


_browser = None
_loop = None


def init_vision_agent(headless=False):
    global _browser, _loop
    if _loop is not None:
        return
    _browser = SafeBrowserAgent(BrowserEngine(headless=headless))
    vision = VisionLayer()
    planner = VisionPlanner()
    _loop = VisionLoop(_browser, vision, planner)


def run_vision_agent(task):
    if _loop is None:
        init_vision_agent()
    return _loop.run(task)
