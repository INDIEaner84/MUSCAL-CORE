import logging

from flask import Blueprint, jsonify, request

from runtime.api.errors import api_error

log = logging.getLogger("muscal.api.rag")

bp = Blueprint("rag", __name__)


@bp.route("/api/rag/search", methods=["POST"])
def api_rag_search() -> dict:
    data = request.get_json() or {}
    query = data.get("query", "").strip()
    try:
        k = min(int(data.get("k", 3)), 10)
    except (ValueError, TypeError):
        k = 3
    if not query:
        return jsonify({"results": [], "chunks": 0})
    try:
        from runtime.kernel.rag_index import get_rag_index
        rag = get_rag_index()
        results = rag.search(query, k=k)
        return jsonify({"results": results, "chunks": len(rag._chunks)})
    except Exception as e:
        log.warning("rag.search error: %s", e)
        return api_error("Internal error"), {"results": []}


@bp.route("/api/rag/reload", methods=["POST"])
def api_rag_reload() -> dict:
    try:
        from runtime.kernel.rag_index import reload_rag_index
        n = reload_rag_index()
        return jsonify({"status": "ok", "chunks": n})
    except Exception as e:
        log.warning("rag.reload error: %s", e)
        return jsonify({"status": "error", "detail": "Internal error"})
