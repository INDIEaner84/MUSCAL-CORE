import time


class CognitiveUnit:
    def __init__(self, unit_id, agent_type, worker=None, memory=None,
                 tool_runtime=None, safety_gate=None, governance=None):
        self.id = unit_id
        self.agent_type = agent_type
        self.worker = worker
        self.memory = memory
        self.tool_runtime = tool_runtime
        self.safety_gate = safety_gate
        self.governance = governance

    def execute(self, context):
        if not context:
            context = {}
        task_type = context.get("task_type", "general")
        tool_name = context.get("tool", "")
        args = context.get("args", {})

        if self.governance is not None:
            gov_result = self.governance.check(context)
            if not getattr(gov_result, "allowed", True):
                return {
                    "status": "blocked_by_governance",
                    "unit_id": self.id,
                    "agent_type": self.agent_type,
                    "task_type": task_type,
                }

        if self.worker is not None:
            worker_result = self.worker.execute(context)
            worker_result["unit_id"] = self.id
            worker_result["agent_type"] = self.agent_type
            return worker_result

        if self.safety_gate is not None:
            safety_result = self.safety_gate.check(tool_name, args)
            if not safety_result.allowed:
                return {
                    "status": "blocked_by_safety",
                    "unit_id": self.id,
                    "agent_type": self.agent_type,
                    "reason": safety_result.reason,
                    "task_type": task_type,
                }

        if self.tool_runtime is not None and tool_name:
            result = self.tool_runtime.execute(tool_name, args)
            return {
                "status": "success" if result.success else "error",
                "unit_id": self.id,
                "agent_type": self.agent_type,
                "tool": tool_name,
                "output": result.output,
                "error": result.error,
                "task_type": task_type,
            }

        return {
            "status": "noop",
            "unit_id": self.id,
            "agent_type": self.agent_type,
            "task_type": task_type,
        }

    def to_dict(self):
        return {
            "id": self.id,
            "agent_type": self.agent_type,
            "worker": self.worker.id if self.worker and hasattr(self.worker, "id") else str(self.worker) if self.worker else None,
        }
