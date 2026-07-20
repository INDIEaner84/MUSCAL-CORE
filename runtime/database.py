import datetime
import logging
import sqlite3
from pathlib import Path
from typing import Optional

import config

log = logging.getLogger("muscal.db")


def _run(conn: sqlite3.Connection, sql: str) -> None:
    conn.execute(sql)


def get_connection(db_path: Optional[Path] = None) -> sqlite3.Connection:
    if db_path is None:
        db_path = config.DB_PATH
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path), timeout=10.0, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=FULL")
    conn.execute("PRAGMA foreign_keys=ON")
    conn.execute("PRAGMA busy_timeout=5000")
    conn.execute("PRAGMA cache_size=-32000")
    return conn


def _table_has_column(conn: sqlite3.Connection, table: str, col: str) -> bool:
    allowed_tables = {"workers", "tasks", "events", "decisions", "snapshots"}
    if table not in allowed_tables:
        return False
    cols = [r["name"] for r in conn.execute(f"PRAGMA table_info({table})")]
    return col in cols


def _next_seq(conn: sqlite3.Connection) -> int:
    conn.execute("UPDATE sequences SET value = value + 1 WHERE name = 'events'")
    row = conn.execute("SELECT value FROM sequences WHERE name = 'events'").fetchone()
    return row["value"]


def init_db(db_path: Optional[Path] = None) -> None:
    if db_path is None:
        db_path = config.DB_PATH
    conn = get_connection(db_path)

    _run(conn, "CREATE TABLE IF NOT EXISTS sequences (name TEXT PRIMARY KEY, value INTEGER NOT NULL DEFAULT 0)")
    _run(conn, "INSERT OR IGNORE INTO sequences (name, value) VALUES ('events', 0)")

    _run(conn, """CREATE TABLE IF NOT EXISTS events (
        id INTEGER PRIMARY KEY AUTOINCREMENT, seq INTEGER NOT NULL UNIQUE,
        ts TEXT NOT NULL, occurred_at TEXT, type TEXT NOT NULL,
        actor TEXT NOT NULL, actor_type TEXT NOT NULL DEFAULT 'worker',
        domain TEXT NOT NULL, layer TEXT NOT NULL,
        stream TEXT NOT NULL DEFAULT 'event', session_id TEXT NOT NULL,
        payload TEXT NOT NULL DEFAULT '{}', caused_by TEXT,
        schema_version INTEGER NOT NULL DEFAULT 1, idempotency_key TEXT UNIQUE,
        model_id TEXT, confidence REAL, trust_level INTEGER NOT NULL DEFAULT 1,
        severity TEXT NOT NULL DEFAULT 'info', aggregate_id TEXT,
        aggregate_type TEXT, replayable INTEGER NOT NULL DEFAULT 1,
        payload_sanitized INTEGER NOT NULL DEFAULT 0,
        CHECK(stream IN ('event','reasoning')),
        CHECK(domain IN ('execution','observation','reflection','projection','system','kernel')),
        CHECK(layer IN ('L1','L2','L3','L4','kernel','system')),
        CHECK(replayable IN (0,1)),
        CHECK(trust_level BETWEEN 0 AND 3),
        CHECK(severity IN ('debug','info','warn','error','critical'))
    )""")

    for idx_name in ("seq", "type", "session_id", "domain, ts", "stream, seq", "aggregate_type, aggregate_id"):
        _run(conn, f"CREATE INDEX IF NOT EXISTS idx_events_{idx_name.split(',')[0].strip()} ON events({idx_name})")

    _run(conn, """CREATE TABLE IF NOT EXISTS workers (
        id TEXT PRIMARY KEY, model TEXT NOT NULL,
        status TEXT NOT NULL DEFAULT 'idle', current_task TEXT,
        last_event_seq INTEGER, registered_at TEXT NOT NULL, started_at TEXT,
        CHECK(status IN ('idle','running','paused','error','retired'))
    )""")

    _run(conn, """CREATE TABLE IF NOT EXISTS tasks (
        id TEXT PRIMARY KEY, type TEXT NOT NULL,
        status TEXT NOT NULL DEFAULT 'pending', worker_id TEXT REFERENCES workers(id),
        document_id TEXT, source_event_seq INTEGER, created_at TEXT NOT NULL,
        started_at TEXT, completed_at TEXT, error_msg TEXT, confidence REAL,
        CHECK(status IN ('pending','active','completed','failed','timeout'))
    )""")
    _run(conn, "CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status)")
    _run(conn, "CREATE INDEX IF NOT EXISTS idx_tasks_worker ON tasks(worker_id, status)")

    _run(conn, """CREATE TABLE IF NOT EXISTS decisions (
        id TEXT PRIMARY KEY, task_id TEXT REFERENCES tasks(id),
        worker_id TEXT REFERENCES workers(id), confidence REAL, reasoning TEXT,
        made_at TEXT NOT NULL, model_id TEXT, source_event_seq INTEGER
    )""")
    _run(conn, "CREATE INDEX IF NOT EXISTS idx_decisions_task ON decisions(task_id)")
    _run(conn, "CREATE INDEX IF NOT EXISTS idx_decisions_time ON decisions(made_at)")

    _run(conn, """CREATE TABLE IF NOT EXISTS intent_documents (
        id TEXT PRIMARY KEY, title TEXT, proceed INTEGER NOT NULL DEFAULT 0,
        confidence REAL, session_id TEXT, created_at TEXT NOT NULL
    )""")

    _run(conn, """CREATE TABLE IF NOT EXISTS intent_unknowns (
        id TEXT PRIMARY KEY, document_id TEXT REFERENCES intent_documents(id),
        description TEXT, is_blocking INTEGER NOT NULL DEFAULT 1,
        resolved INTEGER NOT NULL DEFAULT 0, resolved_at TEXT
    )""")
    _run(conn, "CREATE INDEX IF NOT EXISTS idx_unknowns_blocking ON intent_unknowns(document_id, is_blocking, resolved)")

    _run(conn, """CREATE TABLE IF NOT EXISTS snapshots (
        id INTEGER PRIMARY KEY AUTOINCREMENT, last_seq INTEGER NOT NULL,
        state_json TEXT NOT NULL, event_count INTEGER NOT NULL, created_at TEXT NOT NULL
    )""")
    _run(conn, "CREATE INDEX IF NOT EXISTS idx_snapshots_seq ON snapshots(last_seq DESC)")

    _run(conn, """CREATE TABLE IF NOT EXISTS routing_policy (
        task_type TEXT PRIMARY KEY, worker_id TEXT NOT NULL,
        updated_by TEXT NOT NULL DEFAULT 'bootstrap', updated_at TEXT NOT NULL
    )""")

    _run(conn, "CREATE TABLE IF NOT EXISTS kernel_config (key TEXT PRIMARY KEY, value TEXT NOT NULL)")
    _run(conn, "INSERT OR IGNORE INTO kernel_config VALUES ('schema_version', '1')")
    _run(conn, "INSERT OR IGNORE INTO kernel_config VALUES ('kernel_version', '0.1')")

    _run(conn, """CREATE TABLE IF NOT EXISTS trigger_state (
        trigger_name TEXT PRIMARY KEY, last_event_id INTEGER NOT NULL DEFAULT 0,
        counter INTEGER NOT NULL DEFAULT 0, cooldown_until REAL NOT NULL DEFAULT 0,
        created_at TEXT NOT NULL DEFAULT '', updated_at TEXT NOT NULL DEFAULT ''
    )""")
    _run(conn, "INSERT OR IGNORE INTO trigger_state (trigger_name, last_event_id, counter, cooldown_until, created_at, updated_at) VALUES ('dataset_trigger', 0, 0, 0, '', '')")

    # ADR-010: SQLite Consolidation
    _run(conn, """CREATE TABLE IF NOT EXISTS mcxf_snapshots (
        id INTEGER PRIMARY KEY AUTOINCREMENT, input_text TEXT,
        mcxf_json TEXT, result_json TEXT, feedback_json TEXT,
        created_at TEXT DEFAULT (datetime('now'))
    )""")
    _run(conn, """CREATE TABLE IF NOT EXISTS audit_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT, entry_type TEXT NOT NULL,
        payload TEXT NOT NULL, created_at TEXT DEFAULT (datetime('now'))
    )""")
    _run(conn, """CREATE TABLE IF NOT EXISTS schema_version (
        version INTEGER PRIMARY KEY, applied_at TEXT DEFAULT (datetime('now')),
        description TEXT
    )""")
    _run(conn, "INSERT OR IGNORE INTO schema_version (version, description) VALUES (1, 'ADR-010: unified muscal.db')")

    if not _table_has_column(conn, "workers", "started_at"):
        try:
            conn.execute("ALTER TABLE workers ADD COLUMN started_at TEXT")
            log.info("Migration: started_at column added to workers")
        except Exception as e:
            log.warning("Migration failed (non-critical): %s", e)
    conn.commit()
    conn.close()
    log.info("DB initialized: %s", db_path)


def check_consistency_on_start(db_path: Optional[Path] = None) -> None:
    if db_path is None:
        db_path = config.DB_PATH
    conn = get_connection(db_path)
    now = datetime.datetime.now(datetime.timezone.utc).isoformat()
    stuck = conn.execute("""
        SELECT id FROM tasks WHERE status = 'active'
        AND started_at < datetime('now', '-5 minutes')
    """).fetchall()
    for row in stuck:
        conn.execute("UPDATE tasks SET status='timeout', error_msg='stuck_on_restart', completed_at=? WHERE id=?",
                     [now, row["id"]])
        conn.execute("UPDATE workers SET status='idle', current_task=NULL, started_at=NULL WHERE current_task=?",
                     [row["id"]])
    if stuck:
        log.warning("Marked %d stuck tasks as timeout on restart", len(stuck))
    conn.commit()
    conn.close()
