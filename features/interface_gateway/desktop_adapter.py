from __future__ import annotations

from typing import Any, Optional


class DesktopAdapter:

    def mouse_move(self, x: int = 0, y: int = 0) -> dict[str, Any]:
        if x < 0 or y < 0:
            raise ValueError(f"Invalid coordinates: ({x}, {y})")
        return {"action": "mouse_move", "x": x, "y": y, "status": "ok"}

    def mouse_click(self, x: int = 0, y: int = 0, button: str = "left") -> dict[str, Any]:
        if x < 0 or y < 0:
            raise ValueError(f"Invalid coordinates: ({x}, {y})")
        if button not in ("left", "right", "middle"):
            raise ValueError(f"Invalid button: {button}")
        return {"action": "mouse_click", "x": x, "y": y, "button": button, "status": "ok"}

    def keyboard_type(self, text: str) -> dict[str, Any]:
        if not isinstance(text, str):
            raise ValueError("Text must be a string")
        return {"action": "keyboard_type", "length": len(text), "status": "ok"}

    def window_manage(self, action: str, window_title: str = "") -> dict[str, Any]:
        if action not in ("focus", "minimize", "maximize", "close", "resize", "move"):
            raise ValueError(f"Invalid window action: {action}")
        return {"action": "window_manage", "window_action": action, "window_title": window_title, "status": "ok"}

    def filesystem_read(self, path: str) -> dict[str, Any]:
        import os
        if not os.path.exists(path):
            raise FileNotFoundError(f"Path not found: {path}")
        return {"action": "filesystem_read", "path": path, "status": "ok"}

    def filesystem_write(self, path: str, content: str) -> dict[str, Any]:
        if not isinstance(content, str):
            raise ValueError("Content must be a string")
        return {"action": "filesystem_write", "path": path, "length": len(content), "status": "ok"}
