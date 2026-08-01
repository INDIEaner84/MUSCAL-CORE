from __future__ import annotations

from typing import Optional

from ..runtime.models import ApprovalPolicy
from .models import ToolDefinition


class ToolPolicy:

    def __init__(self, approval_policy=ApprovalPolicy):
        self._approval = approval_policy

    def is_tool_allowed(self, tool: ToolDefinition, autonomy_level: str) -> bool:
        level_num = int(autonomy_level[1]) if autonomy_level.startswith("A") and len(autonomy_level) == 2 else 0
        required_num = int(tool.required_autonomy[1]) if tool.required_autonomy.startswith("A") and len(tool.required_autonomy) == 2 else 5
        return level_num >= required_num

    def requires_approval(self, tool: ToolDefinition, autonomy_level: str) -> bool:
        if tool.requires_confirmation:
            return True
        level = self._approval.for_level(autonomy_level)
        action_map = {
            "filesystem": "modify_files",
            "opencode": "modify_files",
            "desktop": "modify_files",
            "browser": "inspect_system",
        }
        action = action_map.get(tool.category, "read_only")
        return level.needs_confirmation(action)

    def check(self, tool: ToolDefinition, autonomy_level: str) -> tuple[bool, str]:
        if not self.is_tool_allowed(tool, autonomy_level):
            return False, (
                f"Tool '{tool.tool_id}' requires autonomy {tool.required_autonomy}, "
                f"but current level is {autonomy_level}"
            )
        if self.requires_approval(tool, autonomy_level):
            return False, f"Tool '{tool.tool_id}' requires approval at {autonomy_level}"
        return True, ""
