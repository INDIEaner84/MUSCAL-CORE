from memory import get_recent, search_by_keyword


def retrieve(query: str, top_k: int = 3):
    words = [w.lower().strip(".,!?") for w in query.split() if len(w) > 3]
    if words:
        results = []
        seen = set()
        for word in words[:5]:
            for entry in search_by_keyword(word, limit=top_k):
                if entry["id"] not in seen:
                    seen.add(entry["id"])
                    results.append(entry)
        if results:
            return results[:top_k]
    return get_recent(limit=top_k)


def enrich(input_text: str, context: list):
    if not context:
        return input_text

    ctx_lines = []
    for entry in context:
        frag = entry.get("input_text", "")
        if frag:
            ctx_lines.append(f"[HISTORY {entry['id']}] {frag}")

    if not ctx_lines:
        return input_text

    return "\n".join(ctx_lines) + "\n---\n" + input_text
