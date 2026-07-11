class UIState:
    def __init__(self, screenshot_path, description):
        self.screenshot = screenshot_path
        self.description = description
        self.elements = []

    def add_element(self, element):
        self.elements.append(element)
