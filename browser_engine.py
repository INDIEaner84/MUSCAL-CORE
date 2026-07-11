class BrowserEngine:
    def __init__(self, headless=False):
        self.headless = headless
        self._play = None
        self._browser = None
        self._page = None
        self._available = False
        self._start()

    def _start(self):
        try:
            from playwright.sync_api import sync_playwright
            self._play = sync_playwright().start()
            self._browser = self._play.chromium.launch(headless=self.headless)
            self._page = self._browser.new_page()
            self._available = True
        except ImportError:
            self._available = False

    @property
    def available(self):
        return self._available

    def open(self, url):
        if not self._available:
            return {"status": "stub", "url": url}
        self._page.goto(url, timeout=15000)
        return {"status": "opened", "title": self._page.title(), "url": url}

    def click(self, selector):
        if not self._available:
            return {"status": "stub", "selector": selector}
        self._page.click(selector)
        return {"status": "clicked", "selector": selector}

    def type(self, selector, text):
        if not self._available:
            return {"status": "stub", "selector": selector, "text": text}
        self._page.fill(selector, text)
        return {"status": "typed", "selector": selector, "text": text}

    def extract(self, selector):
        if not self._available:
            return {"status": "stub", "selector": selector}
        content = self._page.inner_text(selector)
        return {"status": "extracted", "selector": selector, "content": content[:2000]}

    def close(self):
        if self._browser:
            self._browser.close()
        if self._play:
            self._play.stop()
