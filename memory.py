import json
import threading

import config
from runtime.database import get_connection

MAX_MEMORY_ENTRIES = 10000
_lock = threading.RLock()
_conn = None


def _get_conn():
    global _conn
    if _conn is None:
        _conn = get_connection(config.DB_PATH)
    return _conn


def reset_connection():
    global _conn
    if _conn is not None:
        _conn.close()
    _conn = None


def init():
    with _lock:
        c = _get_conn()
        c.execute("""
        CREATE TABLE IF NOT EXISTS memory (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            data TEXT
        )
        """)
        c.execute("""
        CREATE TABLE IF NOT EXISTS mcxf_snapshots (
            id INTEGER PRIMARY KEY AUTOINCREMENT, input_text TEXT,
            mcxf_json TEXT, result_json TEXT, feedback_json TEXT,
            created_at TEXT DEFAULT (datetime('now'))
        )
        """)
        c.execute("""
        CREATE TABLE IF NOT EXISTS audit_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT, entry_type TEXT NOT NULL,
            payload TEXT NOT NULL, created_at TEXT DEFAULT (datetime('now'))
        )
        """)
        c.execute("""
        CREATE TABLE IF NOT EXISTS schema_version (
            version INTEGER PRIMARY KEY, applied_at TEXT DEFAULT (datetime('now')),
            description TEXT
        )
        """)
        c.commit()


def store(plan, result):
    with _lock:
        c = _get_conn()
        c.execute(
            "INSERT INTO memory (data) VALUES (?)",
            (json.dumps({"plan": plan, "result": result}),)
        )
        c.commit()


def store_snapshot(input_text, mcxf, result, feedback=None):
    mcxf_json = json.dumps(mcxf, default=lambda o: o.__dict__ if hasattr(o, '__dict__') else str(o))
    result_json = json.dumps(result, default=lambda o: o.__dict__ if hasattr(o, '__dict__') else str(o))
    feedback_json = json.dumps(feedback, default=lambda o: o.__dict__ if hasattr(o, '__dict__') else str(o)) if feedback else "{}"

    with _lock:
        c = _get_conn()
        cur = c.execute(
            "INSERT INTO mcxf_snapshots (input_text, mcxf_json, result_json, feedback_json) VALUES (?, ?, ?, ?)",
            (input_text, mcxf_json, result_json, feedback_json)
        )
        c.commit()
        _prune_snapshots()
        return cur.lastrowid


def retrieve_by_id(memory_id: int):
    with _lock:
        c = _get_conn()
        cur = c.execute(
            "SELECT id, input_text, mcxf_json, result_json, feedback_json, created_at FROM mcxf_snapshots WHERE id = ?",
            (memory_id,)
        )
        row = cur.fetchone()
        if row is None:
            return None
        return {
            "id": row[0],
            "input_text": row[1],
            "mcxf": json.loads(row[2]),
            "result": json.loads(row[3]),
            "feedback": json.loads(row[4]),
            "created_at": row[5]
        }


def search_by_keyword(keyword: str, limit: int = 5):
    like = f"%{keyword}%"
    with _lock:
        c = _get_conn()
        cur = c.execute(
            "SELECT id, input_text, mcxf_json, result_json, created_at FROM mcxf_snapshots "
            "WHERE input_text LIKE ? OR mcxf_json LIKE ? ORDER BY id DESC LIMIT ?",
            (like, like, limit)
        )
        rows = cur.fetchall()
        return [
            {
                "id": r[0],
                "input_text": r[1],
                "mcxf": json.loads(r[2]),
                "result": json.loads(r[3]),
                "created_at": r[4]
            }
            for r in rows
        ]


def get_recent(limit: int = 3):
    with _lock:
        c = _get_conn()
        cur = c.execute(
            "SELECT id, input_text, mcxf_json, result_json, created_at FROM mcxf_snapshots "
            "ORDER BY id DESC LIMIT ?",
            (limit,)
        )
        rows = cur.fetchall()
        return [
            {
                "id": r[0],
                "input_text": r[1],
                "mcxf": json.loads(r[2]),
                "result": json.loads(r[3]),
                "created_at": r[4]
            }
            for r in rows
        ]


def log_jsonl(entry):
    c = _get_conn()
    c.execute(
        "INSERT INTO audit_log (entry_type, payload) VALUES (?, ?)",
        (entry.get("type", "info"), json.dumps(entry))
    )
    c.commit()


def _prune_snapshots():
    c = _get_conn()
    c.execute("""
        DELETE FROM mcxf_snapshots WHERE id NOT IN (
            SELECT id FROM mcxf_snapshots ORDER BY id DESC LIMIT ?
        )
    """, (MAX_MEMORY_ENTRIES,))
    c.commit()
