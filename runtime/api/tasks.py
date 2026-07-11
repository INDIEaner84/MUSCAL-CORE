import logging
import time

from flask import Blueprint, jsonify, request

from runtime.api.errors import api_error, api_status_error

import config
from runtime.api import _governance, _policy, _writer
from runtime.kernel.gate import resolve_unknown, start_task_atomic

log = logging.getLogger("muscal.api.tasks")

bp = Blueprint("tasks", __name__)


@bp.route("/api/task", methods=["POST"])
def api_submit_task() -> dict:
    if _writer is None:
        return api_error("Server initializing", 503)
    data = request.get_json() or {}
    task_id = data.get("task_id") or f"task_{int(time.time()*1000)}"
    task_type = data.get("task_type", "routing")
    doc_id = data.get("document_id", "")
    result = start_task_atomic(_writer, task_id, task_type, doc_id, _policy, _governance)
    return jsonify(result)


@bp.route("/api/governance")
def api_governance() -> dict:
    if _governance is None:
        return jsonify({"status": "disabled"})
    return jsonify(_governance.to_dict())


@bp.route("/api/governance/reset", methods=["POST"])
def api_governance_reset() -> dict:
    token = request.headers.get("X-Governance-Reset-Token", "")
    expected = getattr(config, "SESSION_ID", None)
    if not expected or token != expected:
        return api_status_error("invalid or missing token", 403)
    from runtime.kernel.governance import GovernanceSync
    global _governance
    old = _governance
    _governance = GovernanceSync(limits=old.limits if old else None)
    return jsonify({"status": "reset"})


@bp.route("/api/unknown/<unknown_id>/resolve", methods=["POST"])
def api_resolve_unknown(unknown_id: str) -> dict:
    if _writer is None:
        return api_error("Server initializing", 503)
    data = request.get_json() or {}
    doc_id = data.get("document_id", "")
    result = resolve_unknown(_writer, unknown_id, doc_id)
    return jsonify(result)
