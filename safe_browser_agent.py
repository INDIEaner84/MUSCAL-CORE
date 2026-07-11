class SafeBrowserAgent:
    def __init__(self, browser_engine, allowlist=None):
        self.browser = browser_engine
        self.allowlist = allowlist or ["http", "https"]

    def execute(self, task):
        tool = task["tool"]
        args = task.get("args", {})

        if tool == "browser.open":
            url = args.get("url", "")
            if self._check_url(url):
                return self.browser.open(url)
            return {"status": "BLOCKED", "reason": "url_not_allowed", "url": url}

        if tool == "browser.click":
            return self.browser.click(args.get("selector", ""))

        if tool == "browser.type":
            return self.browser.type(args.get("selector", ""), args.get("text", ""))

        if tool == "browser.extract":
            return self.browser.extract(args.get("selector", ""))

        return {"status": "BLOCKED", "tool": tool, "reason": "unknown_browser_tool"}

    def _check_url(self, url):
        return any(url.startswith(p) for p in self.allowlist)
