import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import config
from runtime.database import get_connection
from runtime.kernel.sanitizer import validate_no_injection
from runtime.kernel.writer import WriterThread

log = logging.getLogger("muscal.services")


def generate_handoff(writer: WriterThread, obs_loop=None, governance: Any = None) -> dict:
    conn = get_connection(config.DB_PATH)
    try:
        workers = [dict(r) for r in conn.execute(
            "SELECT id, model, status, current_task FROM workers")]
        open_tasks = [dict(r) for r in conn.execute(
            "SELECT id, type, status, worker_id FROM tasks "
            "WHERE status IN ('pending','active') ORDER BY created_at DESC LIMIT 50")]
        last_events = [dict(r) for r in conn.execute(
            "SELECT seq, ts, type, actor, severity FROM events "
            "ORDER BY seq DESC LIMIT 20")]
        routing = [dict(r) for r in conn.execute(
            "SELECT task_type, worker_id, updated_by, updated_at "
            "FROM routing_policy ORDER BY task_type")]
        health = {
            "writer_alive": writer.is_alive() if writer else False,
        }
    finally:
        conn.close()

    now = datetime.now(timezone.utc).isoformat()
    md = "# MUSCAL Session State \u2014 DYNAMISCH, nur Zustand\n\n"
    md += f"session_id: {config.SESSION_ID}\ngenerated_at: {now}\nkernel_version: 0.1\n\n"
    md += f"## Workers ({len(workers)})\n"
    for w in workers:
        md += f"- **{w['id']}** (`{w['model']}`): {w['status']}\n"
    md += f"\n## Offene Tasks ({len(open_tasks)})\n"
    for t in open_tasks:
        md += f"- `{t['id']}` [{t['type']}] {t['status']} \u2192 {t.get('worker_id','-')}\n"
    md += "\n## Letzte 20 Events\n"
    for e in last_events:
        md += f"- #{e['seq']} {e['ts']} **{e['type']}** by {e['actor']}\n"
    md += f"\n## Routing-Policy ({len(routing)})\n"
    for r in routing:
        md += f"- `{r['task_type']}` \u2192 `{r['worker_id']}` (by {r['updated_by']})\n"
    md += f"\n## Health\n- writer_alive: {health['writer_alive']}\n"

    is_safe, sanitized_md = validate_no_injection(md)
    if not is_safe:
        log.warning("Handoff-Output sanitized")

    out_path = Path("MUSCAL_SESSION_STATE.md")
    out_path.write_text(sanitized_md, encoding="utf-8")

    return {
        "status": "handoff_written",
        "path": str(out_path),
        "workers": len(workers),
        "open_tasks": len(open_tasks),
        "events": len(last_events),
    }
