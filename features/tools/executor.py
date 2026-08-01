from __future__ import annotations

import time
import uuid
from typing import Any, Optional

from .models import ToolDefinition, ToolResult
from .registry import ToolRegistry
from .policy import ToolPolicy
from .approval import ApprovalManager
from .audit import ToolAudit


class ToolExecutor:

    def __init__(self, registry: Optional[ToolRegistry] = None,
                 policy: Optional[ToolPolicy] = None,
                 approval: Optional[ApprovalManager] = None,
                 audit: Optional[ToolAudit] = None,
                 autonomy_level: str = "A3"):
        self._registry = registry or ToolRegistry()
        self._policy = policy or ToolPolicy()
        self._approval = approval or ApprovalManager()
        self._audit = audit or ToolAudit()
        self._autonomy_level = autonomy_level

    def execute(self, tool_id: str, action: str, params: Optional[dict] = None,
                requested_by: str = "system") -> ToolResult:
        tool = self._registry.get_tool(tool_id)
        if tool is None:
            return ToolResult(tool_id=tool_id, action=action, success=False,
                              error=f"Tool '{tool_id}' not found")

        self._audit.record_request(tool_id, action)

        allowed, reason = self._policy.check(tool, self._autonomy_level)
        if not allowed:
            if self._policy.requires_approval(tool, self._autonomy_level):
                req = self._approval.create_request(tool_id, action, tool.risk_level,
                                                     reason, requested_by)
                self._audit.record_approval_created(req)
                req = self._approval.approve(req.request_id)
                if req is None or req.state.name != "APPROVED":
                    self._audit.record_denied(tool_id, action, reason)
                    return ToolResult(tool_id=tool_id, action=action, success=False,
                                      error=f"Approval denied: {reason}")
                self._audit.record_approved(tool_id, action)
            else:
                self._audit.record_denied(tool_id, action, reason)
                return ToolResult(tool_id=tool_id, action=action, success=False,
                                  error=reason)

        start = time.time()
        try:
            result = self._dispatch(tool, action, params or {})
            duration = time.time() - start
            self._audit.record_execution(tool_id, action, result, duration)
            return result
        except Exception as e:
            duration = time.time() - start
            err = str(e)
            self._audit.record_failure(tool_id, action, err, duration)
            return ToolResult(tool_id=tool_id, action=action, success=False,
                              error=err, duration=duration)

    def _dispatch(self, tool: ToolDefinition, action: str, params: dict) -> ToolResult:
        if tool.provider == "builtin":
            return self._execute_builtin(tool, action, params)
        if tool.provider == "opencode":
            return self._execute_opencode(tool, action, params)
        return ToolResult(tool_id=tool.tool_id, action=action, success=False,
                          error=f"Provider '{tool.provider}' not implemented")

    def _execute_builtin(self, tool: ToolDefinition, action: str, params: dict) -> ToolResult:
        import json
        if tool.tool_id == "filesystem.read":
            path = params.get("path", "")
            try:
                with open(path) as f:
                    content = f.read()
                return ToolResult(tool_id=tool.tool_id, action=action, success=True, output=content)
            except Exception as e:
                return ToolResult(tool_id=tool.tool_id, action=action, success=False, error=str(e))
        if tool.tool_id == "filesystem.list":
            import os
            path = params.get("path", ".")
            try:
                entries = os.listdir(path)
                return ToolResult(tool_id=tool.tool_id, action=action, success=True, output=entries)
            except Exception as e:
                return ToolResult(tool_id=tool.tool_id, action=action, success=False, error=str(e))
        return ToolResult(tool_id=tool.tool_id, action=action, success=False,
                          error=f"Builtin action '{action}' not implemented")

    def _execute_opencode(self, tool: ToolDefinition, action: str, params: dict) -> ToolResult:
        return ToolResult(tool_id=tool.tool_id, action=action, success=False,
                          error="OpenCode execution delegated to OpenCodeTool")
