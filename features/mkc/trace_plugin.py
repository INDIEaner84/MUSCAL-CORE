import json
import os
import time


class Plugin:
    name = "execution_trace"

    def __init__(self):
        self._trace = []

    def register(self, hooks):
        for hook_name in hooks:
            if "after" in hook_name or hook_name == "kernel_before":
                hooks[hook_name].append(self._make_handler(hook_name))

    def _make_handler(self, hook_name):
        def handler(ctx):
            os.makedirs("storage", exist_ok=True)
            entry = {
                "timestamp": time.time(),
                "hook": hook_name,
                "input": str(ctx.get("input_text", ""))[:80],
            }
            if "mcxf" in ctx:
                entry["mcxf_tasks"] = len(ctx["mcxf"].tasks) if hasattr(ctx.get("mcxf"), "tasks") else 0
            if "execution_plan" in ctx:
                entry["plan_steps"] = len(ctx["execution_plan"].steps) if hasattr(ctx.get("execution_plan"), "steps") else 0
            if "mel_result" in ctx:
                entry["tool_count"] = len(ctx["mel_result"])
            if "feedback" in ctx:
                entry["confidence_adjustments"] = ctx["feedback"].confidence_adjustments if hasattr(ctx.get("feedback"), "confidence_adjustments") else None
            if "mem_id" in ctx:
                entry["memory_id"] = ctx["mem_id"]
            self._trace.append(entry)
            with open("storage/trace.jsonl", "a") as f:
                f.write(json.dumps(entry) + "\n")
        return handler

    def execute(self, context):
        pass
