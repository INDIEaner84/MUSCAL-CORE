from swarm_node import SwarmNode


class BrowserNode(SwarmNode):
    def browser_open(self, url):
        from playwright.sync_api import sync_playwright

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=False)
            page = browser.new_page()
            page.goto(url)

            return page.title()
