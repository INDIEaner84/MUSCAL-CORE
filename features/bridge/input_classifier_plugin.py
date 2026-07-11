import json
import os


class Plugin:
    name = "input_classifier"

    def register(self, hooks):
        hooks.setdefault("mkc_after", []).append(self._classify)

    def _classify(self, ctx):
        rag_tags = ctx.get("rag_tags", {})
        word_count = rag_tags.get("word_count", 0)
        has_code = rag_tags.get("has_code", False)
        has_question = rag_tags.get("has_question", False)

        # Combine rag_tags with own analysis
        classification = {
            "type": "code" if has_code else "question" if has_question else "statement",
            "complexity": "high" if word_count > 100 else "medium" if word_count > 20 else "low",
            "needs_browser": any(kw in ctx.get("input_text", "").lower()
                               for kw in ["open ", "navigate", "browser", "url", "http"]),
            "word_count": word_count,
        }
        ctx["input_class"] = classification

        os.makedirs("storage", exist_ok=True)
        entry = {
            "input": ctx.get("input_text", "")[:60],
            "from_rag_tags": rag_tags,
            "classification": classification,
        }
        with open("storage/input_classifier.jsonl", "a") as f:
            f.write(json.dumps(entry) + "\n")

    def execute(self, context):
        pass
