"""
MUSCAL System Agent Runtime v0.1

Routes browser/desktop tool calls to their respective runtimes.
Performs safety validation before any action.
Emits events to Graph + Sphere layers.

Safety Rules:
  - No shell.exec / subprocess.run / os.system
  - No page.evaluate (JavaScript injection)
  - URL whitelist (default: empty = block all)
  - Desktop allowed_apps whitelist (default: empty)
  - pyautogui.FAILSAFE = True
  - Max timeout: 10s per action
"""

from schema import (
    EVENT_SYSTEM_ACTION_COMPLETED,
    EVENT_SYSTEM_ACTION_FAILED,
    EVENT_SYSTEM_ACTION_STARTED,
)

BLOCKED_TOOLS = {"shell.exec", "subprocess.run", "os.system", "exec", "eval", "__import__"}
BLOCKED_KEYWORDS = ["import os", "import subprocess", "os.system", "subprocess.run", "eval(", "exec("]


class SafetyViolation(Exception):
    pass


class SystemAgentRuntime:
    def __init__(self, graph=None, sphere=None):
        self.graph = graph
        self.sphere = sphere
        self.browser = None
        self.desktop = None
        self._browser_available = False
        self._desktop_available = False
        self._init_browser()
        self._init_desktop()

    def _init_browser(self):
        try:
            from browser_tools import BrowserRuntime
            self.browser = BrowserRuntime()
            self._browser_available = True
        except ImportError:
            self._browser_available = False
        except Exception:
            self._browser_available = False

    def _init_desktop(self):
        try:
            from desktop_tools import DesktopRuntime
            self.desktop = DesktopRuntime()
            self._desktop_available = True
        except ImportError:
            self._desktop_available = False
        except Exception:
            self._desktop_available = False

    def validate_step(self, step: dict):
        tool = step.get("tool", "")
        args = step.get("args", {})

        if tool in BLOCKED_TOOLS:
            raise SafetyViolation(f"Blocked tool: {tool}")

        for kw in BLOCKED_KEYWORDS:
            text = str(args)
            if kw in text:
                raise SafetyViolation(f"Hidden command detected in args: {kw}")

    def execute(self, step: dict) -> dict:
        self.validate_step(step)
        tool = step["tool"]
        args = step["args"]

        if self.graph:
            self.graph.emit(EVENT_SYSTEM_ACTION_STARTED, {
                "tool": tool, "args": str(args)[:200]
            })

        try:
            if tool.startswith("browser."):
                if not self._browser_available:
                    raise RuntimeError("browser_tools not available (playwright missing)")
                result = self.browser.execute(tool, args)
            elif tool.startswith("desktop."):
                if not self._desktop_available:
                    raise RuntimeError("desktop_tools not available (pyautogui missing)")
                result = self.desktop.execute(tool, args)
            else:
                raise SafetyViolation(f"Unknown system tool: {tool}")

            if self.graph:
                self.graph.emit(EVENT_SYSTEM_ACTION_COMPLETED, {
                    "tool": tool, "result": str(result)[:200]
                })
            return {"status": "success", "tool": tool, "result": result}

        except Exception as e:
            if self.graph:
                self.graph.emit(EVENT_SYSTEM_ACTION_FAILED, {
                    "tool": tool, "error": str(e)
                })
            return {"status": "failed", "tool": tool, "error": str(e)}
