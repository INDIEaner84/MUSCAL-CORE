import logging

from flask import Blueprint, jsonify

from runtime.api import _governance, _obs_loop, _writer
from runtime.services.handoff import generate_handoff

log = logging.getLogger("muscal.api.handoff")

bp = Blueprint("handoff", __name__)


@bp.route("/api/handoff")
def api_handoff() -> dict:
    result = generate_handoff(_writer, _obs_loop, _governance)
    return jsonify(result)
