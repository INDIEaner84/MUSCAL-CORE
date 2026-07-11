#!/usr/bin/env python3
"""
MUSCAL CORE — SQLite Schema Migration Script.
"""
import json
import os
import sqlite3
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import config
from runtime.database import get_connection, init_db

MIGRATIONS = []


def _migration(version, description):
    def wrapper(fn):
        MIGRATIONS.append((version, description, fn))
        return fn
    return wrapper


def _current_version(conn):
    row = conn.execute("SELECT MAX(version) FROM schema_version").fetchone()
    return row[0] if row and row[0] else 0


def _mark_applied(conn, version, description):
    conn.execute(
        "INSERT OR IGNORE INTO schema_version (version, description) VALUES (?, ?)",
        (version, description)
    )
    conn.commit()


# ── Migrations ────────────────────────────────────────────────────────

@_migration(1, "Initial schema (ADR-010)")
def mig_001(conn):
    init_db(config.DB_PATH)


@_migration(2, "Memory confidence tracking table")
def mig_002(conn):
    conn.execute("""CREATE TABLE IF NOT EXISTS confidence_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        section TEXT NOT NULL,
        base REAL NOT NULL,
        adjustment REAL NOT NULL,
        effective REAL NOT NULL,
        logged_at TEXT DEFAULT (datetime('now'))
    )""")
    conn.execute("""CREATE INDEX IF NOT EXISTS idx_confidence_log_section
        ON confidence_log(section, logged_at DESC)""")


# ── Runner ────────────────────────────────────────────────────────────

def _legacy_migration(conn, new_conn):
    old_db_path = "storage/memory.db"
    if not os.path.isfile(old_db_path):
        return False
    old_conn = sqlite3.connect(old_db_path)
    old_conn.row_factory = sqlite3.Row
    tables = [r["name"] for r in old_conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table'"
    )]
    if "mcxf_store" not in tables:
        old_conn.close()
        return False

    existing = new_conn.execute(
        "SELECT COUNT(*) FROM mcxf_snapshots"
    ).fetchone()[0]
    if existing > 0:
        old_conn.close()
        return True

    rows = old_conn.execute(
        "SELECT id, input_text, mcxf_json, result_json, feedback_json, created_at FROM mcxf_store"
    ).fetchall()
    for row in rows:
        new_conn.execute(
            "INSERT INTO mcxf_snapshots (input_text, mcxf_json, result_json, feedback_json, created_at) "
            "VALUES (?, ?, ?, ?, ?)",
            (row["input_text"], row["mcxf_json"], row["result_json"], row["feedback_json"], row["created_at"])
        )

    if "memory" in tables:
        for row in old_conn.execute("SELECT id, data FROM memory").fetchall():
            try:
                json.loads(row["data"])
                new_conn.execute("INSERT INTO memory (data) VALUES (?)", (row["data"],))
            except (json.JSONDecodeError, TypeError):
                pass

    log_path = "storage/logs.jsonl"
    if os.path.isfile(log_path):
        with open(log_path) as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    entry = json.loads(line)
                    new_conn.execute(
                        "INSERT INTO audit_log (entry_type, payload) VALUES (?, ?)",
                        (entry.get("type", "info"), line)
                    )
                except json.JSONDecodeError:
                    pass

    new_conn.commit()
    old_conn.close()
    return True


def run_migrations():
    init_db(config.DB_PATH)
    conn = get_connection(config.DB_PATH)
    current = _current_version(conn)
    ran = 0
    for version, description, fn in sorted(MIGRATIONS, key=lambda x: x[0]):
        if version <= current:
            continue
        print(f"Migration v{version}: {description} ...")
        fn(conn)
        _mark_applied(conn, version, description)
        ran += 1

    legacy_done = _legacy_migration(conn, conn)

    conn.close()
    if ran:
        print(f"Applied {ran} migration(s).")
    if legacy_done:
        print("Legacy data migration checked/completed.")
    if not ran and not legacy_done:
        print("Schema is up to date.")
    return True


if __name__ == "__main__":
    success = run_migrations()
    sys.exit(0 if success else 1)
