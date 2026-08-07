"""Research Memory - export helpers.

Render stored records as JSON / NDJSON / Markdown for reporting, dashboards or
the future Knowledge Foundation ingestion pipeline. These are pure functions
(no IO) plus one convenience wrapper that writes to a destination path.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone


def records_to_json(records: list, pretty: bool = True) -> str:
    payload = {
        "exported_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "count": len(records),
        "records": [r.to_dict() for r in records],
    }
    return json.dumps(payload, indent=2 if pretty else None, sort_keys=True)


def records_to_jsonl(records: list) -> str:
    return "\n".join(json.dumps(r.to_dict(), sort_keys=True) for r in records)


def records_to_markdown(records: list) -> str:
    if not records:
        return "# Research Memory Export\n\n(no records)"
    chunks = ["# Research Memory Export", f"\n{len(records)} record(s)\n"]
    for r in records:
        chunks.append("-" * 60)
        chunks.append(f"### {r.query}")
        chunks.append(
            f"- id: {r.id} | status: {r.status} | confidence: {r.confidence} | hash: {r.hash[:12]}"
        )
        if r.context:
            chunks.append(f"- context: {r.context}")
        if r.domain:
            chunks.append(f"- domain: {r.domain}")
        if r.facts:
            chunks.append("- facts: " + "; ".join(r.facts))
        if r.analysis:
            chunks.append("- analysis: " + r.analysis[:200])
        if r.recommendation:
            chunks.append("- recommendation: " + r.recommendation)
        if r.sources:
            chunks.append("- sources: " + ", ".join(s.url for s in r.sources))
        chunks.append("")
    return "\n".join(chunks)


FORMATS = {"json": records_to_json, "jsonl": records_to_jsonl, "md": records_to_markdown, "markdown": records_to_markdown}


def export_records(
    records: list, fmt: str = "json", destination: str | None = None
) -> str:
    """Serialize records; if destination is given the text is also written."""
    func = FORMATS.get(fmt.lower(), records_to_json)
    text = func(records)
    if destination:
        with open(destination, "w", encoding="utf-8") as fh:
            fh.write(text)
    return text