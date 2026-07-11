import logging

from flask import Blueprint, jsonify, request

import config
from runtime.database import get_connection

log = logging.getLogger("muscal.api.events")

bp = Blueprint("events", __name__)


@bp.route("/api/events")
def api_events() -> dict:
    stream = request.args.get("stream")
    domain = request.args.get("domain")
    try:
        limit = min(int(request.args.get("limit", 50)), 500)
    except (ValueError, TypeError):
        limit = 50
    session = request.args.get("session_id", config.SESSION_ID)
    where = ["session_id = ?"]
    params = [session]
    if stream:
        where.append("stream = ?"); params.append(stream)
    if domain:
        where.append("domain = ?"); params.append(domain)
    conn = get_connection(config.DB_PATH)
    try:
        rows = conn.execute(
            f"SELECT * FROM events WHERE {' AND '.join(where)} ORDER BY seq DESC LIMIT ?",
            params + [limit]
        ).fetchall()
        return jsonify([dict(r) for r in rows])
    finally:
        conn.close()


@bp.route("/api/events/stats")
def api_events_stats() -> dict:
    try:
        window = min(int(request.args.get("window", 60)), 3600)
    except (ValueError, TypeError):
        window = 60
    try:
        limit = min(int(request.args.get("limit", 60)), 500)
    except (ValueError, TypeError):
        limit = 60
    session = request.args.get("session_id", config.SESSION_ID)
    conn = get_connection(config.DB_PATH)
    try:
        total = conn.execute(
            "SELECT COUNT(*) FROM events WHERE session_id = ?", [session]
        ).fetchone()[0]
        by_severity = dict(conn.execute(
            "SELECT severity, COUNT(*) FROM events WHERE session_id = ? GROUP BY severity",
            [session]
        ).fetchall())
        by_type = dict(conn.execute(
            "SELECT type, COUNT(*) FROM events WHERE session_id = ? GROUP BY type",
            [session]
        ).fetchall())
        rows = conn.execute(
            """SELECT
                (CAST(strftime('%%s', ts) AS INTEGER) / ?) * ? AS bucket,
                COUNT(*) AS cnt,
                SUM(CASE WHEN severity IN ('error','critical') THEN 1 ELSE 0 END) AS errs,
                SUM(CASE WHEN severity = 'warn' THEN 1 ELSE 0 END) AS warns
               FROM events
               WHERE session_id = ?
               GROUP BY bucket
               ORDER BY bucket DESC
               LIMIT ?""",
            [window, window, session, limit]
        ).fetchall()
        timeline = [
            {"ts": r["bucket"], "count": r["cnt"],
             "errors": r["errs"], "warns": r["warns"]}
            for r in rows
        ][::-1]
        return jsonify({
            "total": total, "by_severity": by_severity,
            "by_type": by_type, "timeline": timeline, "window_s": window,
        })
    finally:
        conn.close()
