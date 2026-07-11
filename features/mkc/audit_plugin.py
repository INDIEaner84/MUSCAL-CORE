import json
import os
import time


class Plugin:
    name = "audit_logger"

    def register(self, hooks):
        for hook_name, hook_list in hooks.items():
            if isinstance(hook_list, list):
                hook_list.append(self._make_handler(hook_name))

    def _make_handler(self, hook_name):
        start = {"time": None}

        def on_before(ctx):
            start["time"] = time.time()

        def on_after(ctx):
            t0 = start.get("time") or time.time()
            duration_ms = round((time.time() - t0) * 1000, 2)
            os.makedirs("storage", exist_ok=True)
            entry = {
                "timestamp": time.time(),
                "hook": hook_name,
                "duration_ms": duration_ms,
                "input": str(ctx.get("input_text", ""))[:120],
            }
            with open("storage/audit.jsonl", "a") as f:
                f.write(json.dumps(entry) + "\n")

        if hook_name.endswith("_after"):
            return on_after
        if hook_name.endswith("_before"):
            return on_before
        return lambda ctx: None

    def execute(self, context):
        pass
