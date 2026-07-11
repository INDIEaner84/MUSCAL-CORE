import json
import os
import time


class Plugin:
    name = "confidence_metrics"

    def register(self, hooks):
        hooks.setdefault("mkc_after", []).append(self._on_mkc)
        hooks.setdefault("feedback_after", []).append(self._on_feedback)

    def _on_mkc(self, ctx):
        mcxf = ctx.get("mcxf_dict") or {}
        tasks = mcxf.get("tasks", [])
        confidences = [t.get("confidence", 1.0) for t in tasks if isinstance(t, dict)]
        if not confidences:
            return
        os.makedirs("storage", exist_ok=True)
        entry = {
            "timestamp": time.time(),
            "source": "mkc",
            "input": str(ctx.get("input_text", ""))[:80],
            "avg_confidence": round(sum(confidences) / len(confidences), 4),
            "min_confidence": min(confidences),
            "max_confidence": max(confidences),
            "task_count": len(tasks),
        }
        with open("storage/confidence.jsonl", "a") as f:
            f.write(json.dumps(entry) + "\n")

    def _on_feedback(self, ctx):
        feedback = ctx.get("feedback")
        if not feedback or not hasattr(feedback, "confidence_adjustments"):
            return
        adjustments = feedback.confidence_adjustments
        if not adjustments:
            return
        os.makedirs("storage", exist_ok=True)
        entry = {
            "timestamp": time.time(),
            "source": "feedback",
            "input": str(ctx.get("input_text", ""))[:80],
            "adjustments": dict(adjustments),
            "summary": feedback.summary if hasattr(feedback, "summary") else "",
        }
        with open("storage/confidence.jsonl", "a") as f:
            f.write(json.dumps(entry) + "\n")

    def execute(self, context):
        pass
