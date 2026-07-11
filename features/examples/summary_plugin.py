import json
import os
import time


class Plugin:
    name = "pipeline_summary"
    version = "1.0.0"

    def register(self, hooks):
        hooks.setdefault("kernel_before", []).append(self._on_start)
        hooks.setdefault("kernel_after", []).append(self._on_end)

    def _on_start(self, ctx):
        ctx["_pipeline_start"] = time.time()
        ctx["_pipeline_stages"] = []

    def _on_end(self, ctx):
        start = ctx.get("_pipeline_start", time.time())
        duration_ms = round((time.time() - start) * 1000, 2)
        stages = ctx.get("_pipeline_stages", [])
        mem_id = ctx.get("mem_id", None)
        success = ctx.get("feedback", None) is not None

        os.makedirs("storage", exist_ok=True)
        with open("storage/pipeline_summary.jsonl", "a") as f:
            f.write(json.dumps({
                "timestamp": time.time(),
                "duration_ms": duration_ms,
                "stages": stages,
                "memory_id": mem_id,
                "success": success,
                "input_preview": ctx.get("input_text", "")[:100],
            }) + "\n")

    def execute(self, context):
        return {
            "last_summary": context.get("_pipeline_start", None),
        }
