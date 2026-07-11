import json
import os
import time


class Plugin:
    name = "rag_enrichment"

    def register(self, hooks):
        hooks.setdefault("mkc_before", []).append(self._enrich)

    def _enrich(self, ctx):
        enriched = ctx.get("enriched_input", "")
        if not enriched:
            return
        word_count = len(enriched.split())
        has_code = "```" in enriched
        os.makedirs("storage", exist_ok=True)
        tags = {
            "word_count": word_count,
            "has_code": has_code,
            "has_question": "?" in enriched,
            "length_category": "short" if word_count < 20 else "medium" if word_count < 100 else "long",
        }
        ctx["rag_tags"] = tags
        entry = {
            "timestamp": time.time(),
            "input": str(ctx.get("input_text", ""))[:80],
            "tags": tags,
        }
        with open("storage/rag_enrich.jsonl", "a") as f:
            f.write(json.dumps(entry) + "\n")

    def execute(self, context):
        pass
