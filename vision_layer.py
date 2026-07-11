class VisionLayer:
    def __init__(self, llm=None):
        self.llm = llm

    def analyze(self, screenshot_path):
        return {
            "elements": [
                {"type": "button", "text": "Login", "bbox": [100, 200, 150, 240]},
                {"type": "input", "text": "Search", "bbox": [50, 100, 300, 140]},
            ],
            "summary": "Login page with search input",
        }
