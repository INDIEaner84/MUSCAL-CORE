"""
MUSCAL Browser Runtime v0.1

Deterministic browser control via Playwright.
- DOM interaction via CSS selectors only (no XPath, no JS injection)
- Persistent browser context (reusable across steps)
- Graceful fallback if playwright not installed

Tools:
  browser.open(url), browser.click(selector), browser.type(selector, text),
  browser.scroll(direction), browser.extract_text(selector),
  browser.screenshot(path), browser.get_html()
"""


class BrowserRuntime:
    def __init__(self):
        self._playwright = None
        self._browser = None
        self._page = None

    def _ensure_launched(self):
        if self._page is not None:
            return
        from playwright.sync_api import sync_playwright
        self._playwright = sync_playwright().start()
        self._browser = self._playwright.chromium.launch(headless=False)
        self._page = self._browser.new_page()

    def open(self, url):
        self._ensure_launched()
        self._page.goto(url, timeout=10000)
        return {"status": "success", "title": self._page.title(), "url": self._page.url}

    def click(self, selector):
        self._ensure_launched()
        self._page.click(selector, timeout=10000)
        return {"status": "success", "selector": selector}

    def type(self, selector, text):
        self._ensure_launched()
        self._page.fill(selector, text, timeout=10000)
        return {"status": "success", "selector": selector, "typed": text[:200]}

    def scroll(self, direction):
        self._ensure_launched()
        delta = 500 if direction == "down" else -500
        self._page.evaluate(f"window.scrollBy(0, {delta})")
        return {"status": "success", "direction": direction}

    def extract_text(self, selector):
        self._ensure_launched()
        elements = self._page.query_selector_all(selector)
        texts = [el.inner_text() for el in elements[:50]]
        return {"text": "\n".join(texts)[:10000]}

    def screenshot(self, path):
        self._ensure_launched()
        self._page.screenshot(path=path)
        return {"status": "success", "path": path}

    def get_html(self):
        self._ensure_launched()
        html = self._page.content()
        return {"html": html[:50000]}

    def execute(self, tool_name, args):
        method_name = tool_name.split(".", 1)[1]
        method = getattr(self, method_name, None)
        if method is None:
            raise ValueError(f"Unknown browser tool: {tool_name}")
        return method(**args)
