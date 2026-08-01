from __future__ import annotations

from features.tools.opencode_tool import OpenCodeTool
from features.tools.browser_tool import BrowserTool
from features.tools.desktop_tool import DesktopTool


class TestToolIntegrations:

    def test_opencode_tool_definition(self):
        tool = OpenCodeTool()
        definition = tool.definition
        assert definition.tool_id == "opencode.execute"
        assert definition.provider == "opencode"

    def test_browser_tool_definition(self):
        tool = BrowserTool()
        definition = tool.definition
        assert definition.tool_id == "browser.navigate"
        assert definition.provider == "browser"

    def test_browser_navigate_not_implemented(self):
        tool = BrowserTool()
        result = tool.navigate("https://example.com")
        assert result.success is False
        assert "not yet implemented" in result.error

    def test_browser_screenshot_not_implemented(self):
        tool = BrowserTool()
        result = tool.screenshot("https://example.com")
        assert result.success is False

    def test_desktop_tool_definition(self):
        tool = DesktopTool()
        definition = tool.definition
        assert definition.tool_id == "desktop.click"
        assert definition.requires_confirmation is True

    def test_desktop_click_not_implemented(self):
        tool = DesktopTool()
        result = tool.click(x=100, y=200)
        assert result.success is False
        assert "not yet implemented" in result.error

    def test_desktop_type_not_implemented(self):
        tool = DesktopTool()
        result = tool.type_text("hello")
        assert result.success is False
