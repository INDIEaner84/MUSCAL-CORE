from __future__ import annotations

from typing import Optional

from ..runtime.models import ApprovalPolicy


INTERFACE_RISK_MAP: dict[str, str] = {
    "browser.navigate": "inspect_system",
    "browser.read_page": "inspect_system",
    "browser.extract_content": "inspect_system",
    "browser.screenshot": "inspect_system",
    "desktop.mouse_move": "modify_files",
    "desktop.mouse_click": "modify_files",
    "desktop.keyboard_type": "modify_files",
    "desktop.window_manage": "modify_files",
    "desktop.filesystem_read": "read_only",
    "desktop.filesystem_write": "modify_files",
    "mcp.discover": "inspect_system",
    "mcp.register": "modify_files",
    "mcp.execute": "modify_files",
}

CONFIRMATION_REQUIRED: set[str] = {
    "desktop.mouse_click",
    "desktop.keyboard_type",
    "desktop.window_manage",
    "desktop.filesystem_write",
    "mcp.execute",
}


class InterfacePolicyAdapter:

    def __init__(self, approval_policy=ApprovalPolicy):
        self._approval = approval_policy

    def is_action_allowed(self, interface_action: str, autonomy_level: str) -> bool:
        action_category = INTERFACE_RISK_MAP.get(interface_action, "read_only")
        level_num = int(autonomy_level[1]) if (autonomy_level.startswith("A") and len(autonomy_level) == 2) else 0
        high_risk = {"desktop.mouse_click", "desktop.keyboard_type", "desktop.window_manage",
                     "desktop.filesystem_write", "mcp.execute"}
        if interface_action in high_risk and level_num < 3:
            return False
        policy = self._approval.for_level(autonomy_level)
        return policy.is_allowed(action_category)

    def requires_confirmation(self, interface_action: str, autonomy_level: str) -> bool:
        if interface_action in CONFIRMATION_REQUIRED:
            return True
        action_category = INTERFACE_RISK_MAP.get(interface_action, "read_only")
        policy = self._approval.for_level(autonomy_level)
        return policy.needs_confirmation(action_category)

    def check(self, interface_action: str, autonomy_level: str) -> tuple[bool, str]:
        if not self.is_action_allowed(interface_action, autonomy_level):
            return False, (
                f"Interface action '{interface_action}' not allowed at autonomy level {autonomy_level}"
            )
        if self.requires_confirmation(interface_action, autonomy_level):
            return False, f"Interface action '{interface_action}' requires confirmation at {autonomy_level}"
        return True, ""
