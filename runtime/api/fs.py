import logging

from flask import Blueprint, jsonify, request

from runtime.api.errors import api_error

log = logging.getLogger("muscal.api.fs")

bp = Blueprint("fs", __name__)


def _err_response(msg="Internal error"):
    return api_error(msg, 500)


@bp.route("/api/fs/list", methods=["GET"])
def api_fs_list() -> dict:
    try:
        from runtime.kernel.fs_api import list_dir
        data, code = list_dir(request.args.get("path", "/"))
        return jsonify(data), code
    except Exception as e:
        log.warning("fs.list error: %s", e)
        return _err_response()


@bp.route("/api/fs/read", methods=["GET"])
def api_fs_read() -> dict:
    try:
        from runtime.kernel.fs_api import read_file
        data, code = read_file(request.args.get("path", ""))
        return jsonify(data), code
    except Exception as e:
        log.warning("fs.read error: %s", e)
        return _err_response()


@bp.route("/api/fs/write", methods=["POST"])
def api_fs_write() -> dict:
    try:
        from runtime.kernel.fs_api import write_file
        body = request.get_json(silent=True) or {}
        data, code = write_file(body.get("path", ""), body.get("content", ""))
        return jsonify(data), code
    except Exception as e:
        log.warning("fs.write error: %s", e)
        return _err_response()


@bp.route("/api/fs/delete", methods=["POST"])
def api_fs_delete() -> dict:
    try:
        from runtime.kernel.fs_api import delete_file
        body = request.get_json(silent=True) or {}
        data, code = delete_file(body.get("path", ""))
        return jsonify(data), code
    except Exception as e:
        log.warning("fs.delete error: %s", e)
        return _err_response()
