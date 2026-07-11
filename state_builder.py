from ui_state import UIState


class StateBuilder:
    def __init__(self, vision):
        self.vision = vision

    def build(self, screenshot_path):
        analysis = self.vision.analyze(screenshot_path)
        state = UIState(screenshot_path, analysis["summary"])
        for el in analysis["elements"]:
            state.add_element(el)
        return state
