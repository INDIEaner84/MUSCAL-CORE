import logging

from flask import Blueprint, jsonify

import config
from runtime.database import get_connection

log = logging.getLogger("muscal.api.state")

bp = Blueprint("state", __name__)


@bp.route("/api/state")
def api_state() -> dict:
    conn = get_connection(config.DB_PATH)
    try:
        from runtime.api import _obs_loop, _writer
        workers = [dict(r) for r in conn.execute(
            "SELECT id, model, status, current_task, last_event_seq FROM workers")]
        open_tasks = [dict(r) for r in conn.execute(
            "SELECT id, type, status, worker_id, created_at FROM tasks WHERE status='active' LIMIT 20")]
        recent_events = [dict(r) for r in conn.execute(
            "SELECT seq, ts, type, actor, domain, stream, severity FROM events ORDER BY seq DESC LIMIT 30")]
        gate_status = conn.execute(
            "SELECT COUNT(*) as n FROM intent_unknowns WHERE is_blocking=1 AND resolved=0"
        ).fetchone()["n"]
        last_snapshot = conn.execute(
            "SELECT last_seq, created_at FROM snapshots ORDER BY id DESC LIMIT 1"
        ).fetchone()
        return jsonify({
            "workers": workers,
            "open_tasks": open_tasks,
            "recent_events": recent_events,
            "gate": {"blocking_unknowns": gate_status, "open": gate_status == 0},
            "last_snapshot": dict(last_snapshot) if last_snapshot else None,
            "obs_loop": _obs_loop.health() if _obs_loop else {"alive": False},
            "writer_queue_depth": _writer._queue.qsize() if _writer else -1,
            "session_id": config.SESSION_ID,
        })
    finally:
        conn.close()


@bp.route("/api/health")
def api_health() -> dict:
    conn = get_connection(config.DB_PATH)
    try:
        from runtime.api import _obs_loop, _writer
        event_count = conn.execute("SELECT COUNT(*) FROM events").fetchone()[0]
        seq = conn.execute("SELECT value FROM sequences WHERE name='events'").fetchone()
        return jsonify({
            "status": "ok",
            "session_id": config.SESSION_ID,
            "event_count": event_count,
            "seq": seq["value"] if seq else 0,
            "writer_alive": _writer.is_alive() if _writer else False,
            "writer_queue": _writer._queue.qsize() if _writer else -1,
            "obs_loop": _obs_loop.health() if _obs_loop else {"alive": False},
        })
    finally:
        conn.close()


@bp.route("/api/ready")
def api_ready():
    from runtime.api import _server_ready
    if not _server_ready:
        return jsonify({"status": "not_ready"}), 503
    return jsonify({"status": "ready"})


@bp.route("/api/live")
def api_live():
    return jsonify({"status": "alive"})
