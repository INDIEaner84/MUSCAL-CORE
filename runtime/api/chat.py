import logging

from flask import Blueprint, jsonify, request

import config
from runtime.api import _policy, _writer
from runtime.database import get_connection
from runtime.llm.client import _ollama_ping
from runtime.llm.models import ask_qwen, ask_smol

log = logging.getLogger("muscal.api.chat")

bp = Blueprint("chat", __name__)

_GREETING_KEYWORDS = {"hallo", "hi", "hey", "gr\u00fc\u00df", "moin", "servus", "tag", "nabend",
                      "guten morgen", "guten tag", "guten abend", "tsch\u00fcss", "bye",
                      "ciao", "danke", "thanks", "ok", "ja", "nein", "super"}


def system_info() -> str:
    import sqlite3
    conn = get_connection(config.DB_PATH)
    try:
        ec = conn.execute("SELECT COUNT(*) FROM events").fetchone()[0]
        wc = conn.execute("SELECT COUNT(*) FROM workers").fetchone()[0]
        tc = conn.execute("SELECT COUNT(*) FROM tasks WHERE status='active'").fetchone()[0]
    finally:
        conn.close()
    return (
        f"**MUSCAL CORE** | Session: `{config.SESSION_ID}` | "
        f"Events: {ec} | Worker: {wc} | Tasks: {tc}"
    )


@bp.route("/api/chat", methods=["POST"])
def api_chat() -> dict:
    data = request.get_json() or {}
    message = data.get("message", "").strip()
    if not message:
        return jsonify({"response": "Sag was oder /help", "type": "system"})

    if message.startswith("/"):
        return jsonify(handle_command(message))

    if not _ollama_ping():
        return jsonify({
            "response": f"{system_info()}\n\n*Ollama ist offline.*",
            "type": "system",
        })

    is_greeting = any(kw in message.lower() for kw in _GREETING_KEYWORDS)
    rag_context = ""
    rag_used = False
    if not is_greeting:
        try:
            from runtime.kernel.rag_index import get_rag_index
            rag = get_rag_index()
            rag_context = rag.get_context(message, k=2, max_chars=1500)
            if rag_context:
                rag_used = True
        except Exception:
            pass

    if rag_context:
        smol_prompt = (
            f"Du bist Alita, ein Cognitive OS. Beantworte die Frage des Users "
            f"basierend auf folgendem Kontext. Wenn der Kontext nicht zur Frage passt, "
            f"antworte trotzdem freundlich.\n\n"
            f"Kontext:\n{rag_context}\n\n"
            f"Frage: {message}"
        )
    else:
        smol_system = "Du bist Alita, ein hilfreicher KI-Assistent. Antworte kurz und freundlich."
        smol_prompt = f"{smol_system}\n\nUser: {message}\nAlita:"
    smol_resp = ask_smol(smol_prompt)

    if not smol_resp or len(smol_resp) < 15:
        flash_prompt = message
        if rag_context:
            flash_prompt = f"Kontext:\n{rag_context}\n\nFrage: {message}"
        flash_resp = ask_qwen(f"User: {flash_prompt}\nAssistant:")
        return jsonify({
            "response": flash_resp, "type": "chat",
            "model": config.QWEN_MODEL, "rag": rag_used,
        })

    return jsonify({
        "response": smol_resp, "type": "chat",
        "model": config.SMOL_MODEL, "rag": rag_used,
    })


def handle_command(message: str) -> dict:
    cmd = message.split()[0].lower()
    args = message.split()[1:] if len(message.split()) > 1 else []

    if cmd == "/help":
        text = """**Verf\u00fcgbare Befehle:**
  `/help` \u2013 Diese Hilfe
  `/status` \u2013 System-Zusammenfassung
  `/workers` \u2013 Worker-Liste mit Status
  `/events [N]` \u2013 Letzte N Events (default 10)
  `/gate` \u2013 Gate-Status
  `/snapshot` \u2013 Snapshot ausl\u00f6sen
  `/chat <text>` \u2013 Nachricht an Qwen (wenn online)"""
        return {"response": text, "type": "system"}

    elif cmd == "/status":
        return {"response": system_info(), "type": "system"}

    elif cmd == "/workers":
        conn = get_connection(config.DB_PATH)
        rows = conn.execute(
            "SELECT id, model, status, current_task, last_event_seq FROM workers"
        ).fetchall()
        conn.close()
        lines = [f"**{r['id']}** (`{r['model']}`): {r['status']}" +
                 (f" \u2192 {r['current_task']}" if r['current_task'] else "")
                 for r in rows]
        return {"response": f"**{len(rows)} Worker:**\n" + "\n".join(lines), "type": "system"}

    elif cmd == "/events":
        n = int(args[0]) if args and args[0].isdigit() else 10
        conn = get_connection(config.DB_PATH)
        rows = conn.execute(
            "SELECT seq, ts, type, actor, domain, severity FROM events ORDER BY seq DESC LIMIT ?",
            [n]
        ).fetchall()
        conn.close()
        lines = [f"#{r['seq']} {r['type']} [{r['severity']}] by {r['actor']}" for r in rows]
        text = f"**Letzte {len(rows)} Events:**\n" + "\n".join(lines) if lines else "Keine Events."
        return {"response": text, "type": "system"}

    elif cmd == "/gate":
        conn = get_connection(config.DB_PATH)
        blocking = conn.execute(
            "SELECT COUNT(*) as n FROM intent_unknowns WHERE is_blocking=1 AND resolved=0"
        ).fetchone()["n"]
        conn.close()
        status = "GATE OFFEN" if blocking == 0 else f"{blocking} unbekannte(s) Problem(e)"
        return {"response": f"**Gate:** {status}", "type": "system"}

    elif cmd == "/snapshot":
        from runtime.services.snapshot import create_snapshot
        result = create_snapshot(_writer)
        if result.get("status") == "queued":
            return {"response": "Snapshot wird erstellt.", "type": "system"}
        return {"response": "Snapshot fehlgeschlagen.", "type": "system"}

    elif cmd == "/chat":
        text = " ".join(args)
        if not text:
            return {"response": "Usage: /chat <deine Nachricht>", "type": "system"}
        if _ollama_ping():
            resp = ask_qwen(f"User: {text}\nAssistant:")
            return {"response": resp, "type": "chat"}
        return {"response": f"Ollama offline. ```\n{system_info()}\n```", "type": "system"}

    else:
        return {"response": f"Unbekannter Befehl: {cmd}. Tippe /help.", "type": "system"}
