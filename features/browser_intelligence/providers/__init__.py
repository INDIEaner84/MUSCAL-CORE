"""Browser Intelligence - provider registry.

Kept import-light: browser_use is imported lazily inside get_provider so the
MUSCAL plugin loader can import this package without the heavy dependency.
"""

from __future__ import annotations


def get_provider(name: str = "browser_use"):
    if name == "browser_use":
        from .browser_use import BrowserUseProvider

        return BrowserUseProvider()
    raise ValueError(f"Unknown research provider: {name}")


def available_providers() -> list:
    return ["browser_use"]
