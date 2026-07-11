from flask import jsonify


def api_error(message: str, status: int = 500):
    return jsonify({"error": message}), status


def api_status_error(detail: str, status: int = 400):
    return jsonify({"status": "error", "detail": detail}), status
