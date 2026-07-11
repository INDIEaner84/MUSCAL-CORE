import logging

from flask import Blueprint, jsonify, request

from runtime.api.errors import api_error

import config
from runtime.api import _writer
from runtime.database import get_connection

log = logging.getLogger("muscal.api.workers")

bp = Blueprint("workers", __name__)
WRITER_TIMEOUT = 5.0


@bp.route("/api/worker/<worker_id>/pause", methods=["POST"])
def api_pause_worker(worker_id: str) -> dict:
    if _writer is None:
        return api_error("Server initializing", 503)
    def _tx(conn):
        conn.execute("UPDATE workers SET status='paused' WHERE id=?", [worker_id])
    future = _writer.submit({
        "type": "worker.pause_requested", "domain": "execution", "layer": "L1",
        "stream": "event", "trust_level": 2, "actor": "api",
        "actor_type": "human", "session_id": config.SESSION_ID,
        "aggregate_id": worker_id, "aggregate_type": "worker",
        "payload": {"worker_id": worker_id},
    }, transaction_fn=_tx)
    future.result(timeout=WRITER_TIMEOUT)
    return jsonify({"status": "paused", "worker_id": worker_id})


@bp.route("/api/worker/<worker_id>/resume", methods=["POST"])
def api_resume_worker(worker_id: str) -> dict:
    if _writer is None:
        return api_error("Server initializing", 503)
    def _tx(conn):
        conn.execute("UPDATE workers SET status='idle' WHERE id=?", [worker_id])
    future = _writer.submit({
        "type": "worker.resume_requested", "domain": "execution", "layer": "L1",
        "stream": "event", "trust_level": 2, "actor": "api",
        "actor_type": "human", "session_id": config.SESSION_ID,
        "aggregate_id": worker_id, "aggregate_type": "worker",
        "payload": {"worker_id": worker_id},
    }, transaction_fn=_tx)
    future.result(timeout=WRITER_TIMEOUT)
    return jsonify({"status": "resumed", "worker_id": worker_id})


@bp.route("/api/workers/pause", methods=["POST"])
def api_pause_all_workers() -> dict:
    if _writer is None:
        return api_error("Server initializing", 503)
    conn = get_connection(config.DB_PATH)
    running = conn.execute("SELECT id FROM workers WHERE status='running'").fetchall()
    conn.close()
    paused = []
    for row in running:
        wid = row["id"]
        def _tx(conn, wid=wid):
            conn.execute("UPDATE workers SET status='paused' WHERE id=?", [wid])
        future = _writer.submit({
            "type": "worker.pause_requested", "domain": "execution", "layer": "L1",
            "stream": "event", "trust_level": 2, "actor": "api",
            "actor_type": "system", "session_id": config.SESSION_ID,
            "aggregate_id": wid, "aggregate_type": "worker",
            "payload": {"worker_id": wid},
        }, transaction_fn=_tx)
        future.result(timeout=WRITER_TIMEOUT)
        paused.append(wid)
    return jsonify({"status": "paused", "workers": paused})


@bp.route("/api/workers/resume", methods=["POST"])
def api_resume_all_workers() -> dict:
    if _writer is None:
        return api_error("Server initializing", 503)
    conn = get_connection(config.DB_PATH)
    rows = conn.execute("SELECT id FROM workers WHERE status='paused'").fetchall()
    conn.close()
    resumed = []
    for row in rows:
        wid = row["id"]
        def _tx(conn, wid=wid):
            conn.execute("UPDATE workers SET status='idle' WHERE id=?", [wid])
        future = _writer.submit({
            "type": "worker.resume_requested", "domain": "execution", "layer": "L1",
            "stream": "event", "trust_level": 2, "actor": "api",
            "actor_type": "system", "session_id": config.SESSION_ID,
            "aggregate_id": wid, "aggregate_type": "worker",
            "payload": {"worker_id": wid},
        }, transaction_fn=_tx)
        future.result(timeout=WRITER_TIMEOUT)
        resumed.append(wid)
    return jsonify({"status": "resumed", "workers": resumed})
