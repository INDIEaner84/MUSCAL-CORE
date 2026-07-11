"""
MUSCAL Desktop Runtime v0.1

Coordinate-based and application-level desktop control via PyAutoGUI.
- pyautogui.FAILSAFE = True (mouse to corner = emergency stop)
- All actions must be explicitly declared in ExecutionPlan
- App whitelist (default: empty = no apps allowed)

Tools:
  desktop.open_app(name), desktop.type(text), desktop.click(x, y),
  desktop.screenshot(path), desktop.move(x, y), desktop.keypress(key)
"""

import time


class DesktopRuntime:
    def __init__(self):
        self._pyautogui = None
        self._init_pyautogui()

    def _init_pyautogui(self):
        import pyautogui
        pyautogui.FAILSAFE = True
        pyautogui.PAUSE = 0.3
        self._pyautogui = pyautogui

    def open_app(self, name):
        import subprocess
        allowed = []
        if name not in allowed:
            return {"status": "failed", "error": f"App '{name}' not in allowed_apps list"}
        subprocess.Popen([name], shell=False)
        time.sleep(1)
        return {"status": "success", "app": name}

    def type(self, text):
        self._pyautogui.typewrite(text, interval=0.05)
        return {"status": "success", "typed": text[:200]}

    def click(self, x, y):
        self._pyautogui.click(x, y)
        return {"status": "success", "x": x, "y": y}

    def screenshot(self, path):
        self._pyautogui.screenshot(path)
        return {"status": "success", "path": path}

    def move(self, x, y):
        self._pyautogui.moveTo(x, y, duration=0.3)
        return {"status": "success", "x": x, "y": y}

    def keypress(self, key):
        blocked = ["ctrl+alt+del", "alt+f4", "ctrl+shift+esc", "win", "super"]
        if key.lower() in blocked:
            return {"status": "failed", "error": f"Blocked key: {key}"}
        self._pyautogui.press(key)
        return {"status": "success", "key": key}

    def execute(self, tool_name, args):
        method_name = tool_name.split(".", 1)[1]
        method = getattr(self, method_name, None)
        if method is None:
            raise ValueError(f"Unknown desktop tool: {tool_name}")
        return method(**args)
