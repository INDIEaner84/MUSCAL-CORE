from __future__ import annotations

from typing import Any, Optional


class BrowserAdapter:

    def navigate(self, url: str, timeout: int = 30) -> dict[str, Any]:
        if not url.startswith(("http://", "https://")):
            raise ValueError(f"Invalid URL scheme: {url}")
        return {"url": url, "status": "navigated", "title": "mocked"}

    def read_page(self, url: str, selector: str = "") -> dict[str, Any]:
        if not url.startswith(("http://", "https://")):
            raise ValueError(f"Invalid URL scheme: {url}")
        return {"url": url, "content": "<html><body>mocked content</body></html>", "length": 42}

    def extract_content(self, url: str, selector: str = "") -> dict[str, Any]:
        if not url.startswith(("http://", "https://")):
            raise ValueError(f"Invalid URL scheme: {url}")
        return {"url": url, "extracted": "mocked extracted text", "selector": selector}

    def screenshot(self, url: str, full_page: bool = False) -> dict[str, Any]:
        if not url.startswith(("http://", "https://")):
            raise ValueError(f"Invalid URL scheme: {url}")
        return {"url": url, "screenshot_path": "/tmp/mocked_screenshot.png", "full_page": full_page}
