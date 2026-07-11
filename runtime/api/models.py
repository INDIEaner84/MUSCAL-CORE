import logging

from flask import Blueprint, jsonify, request

from runtime.api.errors import api_error

import config
from runtime.llm.client import _ollama_ping

log = logging.getLogger("muscal.api.models")

bp = Blueprint("models", __name__)


@bp.route("/api/models")
def api_models_list() -> dict:
    from runtime.llm.models import ask_qwen
    return jsonify({"models": [
        {"name": config.QWEN_MODEL, "type": "chat", "built_in": True},
        {"name": config.SMOL_MODEL, "type": "chat", "built_in": True},
        {"name": config.R1_MODEL, "type": "reasoning", "built_in": True},
    ]})


@bp.route("/api/models/<name>/health")
def api_models_health(name: str) -> dict:
    alive = _ollama_ping()
    return jsonify({"name": name, "alive": alive})


@bp.route("/api/models", methods=["POST"])
def api_models_add() -> dict:
    return api_error("Model registry not available in MUSCAL CORE yet", 400)


@bp.route("/api/models/<name>", methods=["DELETE"])
def api_models_remove(name: str) -> dict:
    return api_error("Model registry not available in MUSCAL CORE yet", 400)
