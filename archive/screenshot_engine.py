class ScreenshotEngine:
    def __init__(self, page):
        self.page = page

    def capture(self):
        path = "screen.png"
        self.page.screenshot(path=path)
        return path
