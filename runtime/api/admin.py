import logging
from datetime import datetime, timezone

from flask import Blueprint, jsonify, request

import config
from runtime.api import _policy, _writer
from runtime.api.errors import api_error, api_status_error
from runtime.services.snapshot import create_snapshot

log = logging.getLogger("muscal.api.admin")

bp = Blueprint("admin", __name__)


@bp.route("/api/snapshot", methods=["POST"])
def api_snapshot() -> dict:
    result = create_snapshot(_writer)
    if "error" in result:
        return jsonify(result), 500
    return jsonify(result)


@bp.route("/api/handoff")
def api_handoff() -> dict:
    from runtime.api import _governance, _obs_loop
    from runtime.services.handoff import generate_handoff
    result = generate_handoff(_writer, _obs_loop, _governance)
    return jsonify(result)


_ALLOWED_COMMANDS = {
    "ps", "df -h", "free -h", "uptime", "who", "uname -a",
    "ls /tmp", "date", "hostname", "top -b -n1",
}

_ALLOWED_URL_PREFIXES = ("http://", "https://", "http://localhost", "https://localhost")


@bp.route("/api/hud-action", methods=["POST"])
def api_hud_action() -> dict:
    if _writer is None:
        return api_error("Server initializing", 503)
    data = request.get_json() or {}
    action = data.get("action", "")
    target = data.get("target", "")

    if action == "screenshot":
        try:
            import subprocess
            ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
            fname = f"/tmp/muscal_screenshot_{ts}.png"
            subprocess.run(["gnome-screenshot", "-f", fname],
                           capture_output=True, timeout=10)
            _writer.submit({
                "type": "hud.screenshot_taken",
                "domain": "system", "layer": "kernel",
                "stream": "event", "actor": "hud", "actor_type": "human",
                "session_id": config.SESSION_ID,
                "payload": {"path": fname, "action": "screenshot"},
            })
            return jsonify({"status": "ok", "path": fname})
        except Exception as e:
            log.warning("hud.screenshot error: %s", e)
            return api_status_error("Internal error", 500)

    elif action == "open_url":
        url = target or f"http://localhost:{config.RUNTIME_FLASK_PORT}"
        if not url.startswith(_ALLOWED_URL_PREFIXES):
            return api_status_error("url scheme not allowed", 400)
        import webbrowser
        webbrowser.open(url)
        return jsonify({"status": "ok", "url": url})

    elif action == "system_command":
        if not target:
            return api_status_error("empty command", 400)
        if target not in _ALLOWED_COMMANDS:
            return jsonify({"status": "blocked", "detail": "command not in allowlist"}), 403
        try:
            import shlex
            import subprocess
            args = shlex.split(target)
            result = subprocess.run(args, shell=False, capture_output=True,
                                    text=True, timeout=30)
            return jsonify({
                "status": "ok", "stdout": result.stdout[:500],
                "stderr": result.stderr[:500],
            })
        except Exception as e:
            log.warning("hud.system_command error: %s", e)
            return api_status_error("Internal error", 500)

    elif action == "compact":
        return jsonify({"status": "not_implemented", "detail": "Compact via snapshot API"})

    else:
        return api_status_error(f"unknown action: {action}", 400)
