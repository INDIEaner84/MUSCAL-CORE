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
    _run(conn, "INSERT OR IGNORE INTO sequences (name, value) VALUES ('decisions', 0)")

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

    for col_name, col_def in [
        ("trace_id", "trace_id TEXT"),
        ("span_id", "span_id TEXT"),
        ("decision_type", "decision_type TEXT NOT NULL DEFAULT 'governance'"),
        ("decision_status", "decision_status TEXT NOT NULL DEFAULT 'active'"),
        ("governance_action", "governance_action TEXT"),
        ("parent_decision_id", "parent_decision_id TEXT REFERENCES decisions(id)"),
    ]:
        if not _table_has_column(conn, "decisions", col_name):
            try:
                conn.execute(f"ALTER TABLE decisions ADD COLUMN {col_def}")
                log.info("Migration: %s column added to decisions", col_name)
            except Exception as e:
                log.warning("Migration failed (non-critical): %s", e)

    for idx_name, idx_col in [
        ("idx_decisions_trace", "trace_id"),
        ("idx_decisions_span", "span_id"),
        ("idx_decisions_status", "decision_status"),
    ]:
        try:
            conn.execute(f"CREATE INDEX IF NOT EXISTS {idx_name} ON decisions({idx_col})")
        except Exception as e:
            log.warning("Index creation failed (non-critical): %s", e)

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

    _run(conn, """CREATE TABLE IF NOT EXISTS validation_artifacts (
        validation_id TEXT PRIMARY KEY,
        evaluation_id TEXT NOT NULL,
        execution_id TEXT NOT NULL,
        trace_id TEXT NOT NULL DEFAULT '',
        span_id TEXT NOT NULL DEFAULT '',
        decision_id TEXT NOT NULL DEFAULT '',
        agent_id TEXT NOT NULL DEFAULT '',
        model_id TEXT NOT NULL DEFAULT '',
        outcome_id TEXT NOT NULL DEFAULT '',
        validation_result TEXT NOT NULL DEFAULT 'INCONCLUSIVE',
        evidence_status TEXT NOT NULL DEFAULT 'MISSING',
        rationale TEXT NOT NULL DEFAULT '',
        integrity_hash TEXT NOT NULL DEFAULT '',
        created_at REAL NOT NULL DEFAULT 0,
        finalized INTEGER NOT NULL DEFAULT 0
    )""")
    _run(conn, "CREATE INDEX IF NOT EXISTS idx_valart_ev ON validation_artifacts(evaluation_id)")
    _run(conn, "CREATE INDEX IF NOT EXISTS idx_valart_exec ON validation_artifacts(execution_id)")

    if not _table_has_column(conn, "workers", "started_at"):
        try:
            conn.execute("ALTER TABLE workers ADD COLUMN started_at TEXT")
            log.info("Migration: started_at column added to workers")
        except Exception as e:
            log.warning("Migration failed (non-critical): %s", e)

    # MCPL tables (MC-006)
    _run(conn, """CREATE TABLE IF NOT EXISTS mcpl_intents (
        intent_id TEXT PRIMARY KEY,
        description TEXT,
        created_at TEXT,
        correlation_id TEXT,
        causation_id TEXT,
        tenant_id TEXT,
        status TEXT DEFAULT 'created',
        metadata TEXT DEFAULT '{}'
    )""")

    _run(conn, """CREATE TABLE IF NOT EXISTS mcpl_tasks (
        task_id TEXT PRIMARY KEY,
        intent_id TEXT,
        description TEXT,
        created_at TEXT,
        correlation_id TEXT,
        causation_id TEXT,
        tenant_id TEXT,
        status TEXT DEFAULT 'created',
        agent_id TEXT,
        join_id TEXT,
        metadata TEXT DEFAULT '{}',
        FOREIGN KEY (intent_id) REFERENCES mcpl_intents(intent_id)
    )""")
    _run(conn, "CREATE INDEX IF NOT EXISTS idx_mcpl_tasks_intent ON mcpl_tasks(intent_id)")

    _run(conn, """CREATE TABLE IF NOT EXISTS mcpl_agents (
        agent_id TEXT PRIMARY KEY,
        name TEXT,
        version TEXT DEFAULT '1.0.0',
        agent_type TEXT DEFAULT 'llm',
        created_at TEXT,
        tenant_id TEXT
    )""")

    _run(conn, """CREATE TABLE IF NOT EXISTS mcpl_models (
        model_id TEXT PRIMARY KEY,
        provider TEXT,
        model_name TEXT,
        model_version TEXT DEFAULT '',
        created_at TEXT,
        temperature REAL DEFAULT 0.0,
        top_p REAL DEFAULT 1.0,
        seed INTEGER,
        sampling_parameters TEXT DEFAULT '{}',
        system_prompt_hash TEXT DEFAULT '',
        runtime_environment TEXT DEFAULT '{}',
        tool_versions TEXT DEFAULT '{}'
    )""")

    _run(conn, """CREATE TABLE IF NOT EXISTS mcpl_model_outputs (
        output_id TEXT PRIMARY KEY,
        model_id TEXT,
        agent_id TEXT,
        prompt_hash TEXT DEFAULT '',
        input_artifact_hashes TEXT DEFAULT '[]',
        retrieved_context_refs TEXT DEFAULT '[]',
        knowledge_snapshot TEXT DEFAULT '',
        candidates TEXT DEFAULT '[]',
        raw_output TEXT DEFAULT '',
        output_hash TEXT DEFAULT '',
        created_at TEXT,
        correlation_id TEXT,
        causation_id TEXT,
        tenant_id TEXT,
        metadata TEXT DEFAULT '{}'
    )""")

    _run(conn, """CREATE TABLE IF NOT EXISTS mcpl_decisions (
        decision_id TEXT PRIMARY KEY,
        decision_type TEXT,
        task_id TEXT,
        agent_id TEXT,
        created_at TEXT,
        correlation_id TEXT,
        causation_id TEXT,
        tenant_id TEXT,
        status TEXT DEFAULT 'active',
        reasoning TEXT DEFAULT '',
        confidence REAL DEFAULT 0.0,
        model_output_id TEXT DEFAULT '',
        parent_decision_id TEXT DEFAULT '',
        candidates TEXT DEFAULT '[]',
        selected TEXT DEFAULT '',
        selection_rationale TEXT DEFAULT '',
        policy_id TEXT DEFAULT '',
        policy_version TEXT DEFAULT '',
        match_result TEXT DEFAULT '',
        human_action TEXT DEFAULT '',
        human_id TEXT DEFAULT '',
        automated_decision_id TEXT DEFAULT '',
        rationale TEXT DEFAULT ''
    )""")
    _run(conn, "CREATE INDEX IF NOT EXISTS idx_mcpl_decisions_task ON mcpl_decisions(task_id)")

    _run(conn, """CREATE TABLE IF NOT EXISTS mcpl_executions (
        execution_id TEXT PRIMARY KEY,
        task_id TEXT,
        tool_name TEXT,
        created_at TEXT,
        correlation_id TEXT,
        causation_id TEXT,
        tenant_id TEXT,
        status TEXT DEFAULT 'requested',
        authorization_id TEXT DEFAULT '',
        decision_id TEXT DEFAULT '',
        attempt_count INTEGER DEFAULT 0,
        replay_of TEXT DEFAULT '',
        replay_classification TEXT DEFAULT '',
        metadata TEXT DEFAULT '{}',
        FOREIGN KEY (task_id) REFERENCES mcpl_tasks(task_id)
    )""")
    _run(conn, "CREATE INDEX IF NOT EXISTS idx_mcpl_executions_task ON mcpl_executions(task_id)")

    _run(conn, """CREATE TABLE IF NOT EXISTS mcpl_attempts (
        attempt_id TEXT PRIMARY KEY,
        execution_id TEXT,
        attempt_number INTEGER,
        created_at TEXT,
        started_at TEXT DEFAULT '',
        completed_at TEXT DEFAULT '',
        status TEXT DEFAULT 'started',
        error TEXT DEFAULT '',
        error_type TEXT DEFAULT '',
        duration_ms REAL DEFAULT 0.0,
        result_hash TEXT DEFAULT '',
        receipt_id TEXT DEFAULT '',
        tenant_id TEXT,
        FOREIGN KEY (execution_id) REFERENCES mcpl_executions(execution_id)
    )""")
    _run(conn, "CREATE INDEX IF NOT EXISTS idx_mcpl_attempts_execution ON mcpl_attempts(execution_id)")

    _run(conn, """CREATE TABLE IF NOT EXISTS mcpl_tool_calls (
        tool_call_id TEXT PRIMARY KEY,
        execution_id TEXT,
        attempt_id TEXT DEFAULT '',
        tool_name TEXT DEFAULT '',
        args_hash TEXT DEFAULT '',
        result_hash TEXT DEFAULT '',
        success INTEGER DEFAULT 0,
        duration_ms REAL DEFAULT 0.0,
        created_at TEXT,
        correlation_id TEXT DEFAULT '',
        causation_id TEXT DEFAULT '',
        tenant_id TEXT DEFAULT '',
        receipt_id TEXT DEFAULT '',
        integrity_hash TEXT DEFAULT ''
    )""")

    _run(conn, """CREATE TABLE IF NOT EXISTS mcpl_artifacts (
        artifact_id TEXT PRIMARY KEY,
        name TEXT,
        artifact_type TEXT,
        content_hash TEXT,
        content_ref TEXT DEFAULT '',
        mime_type TEXT DEFAULT '',
        size_bytes INTEGER DEFAULT 0,
        created_at TEXT,
        tool_call_id TEXT DEFAULT '',
        execution_id TEXT DEFAULT '',
        tenant_id TEXT DEFAULT '',
        metadata TEXT DEFAULT '{}'
    )""")
    _run(conn, "CREATE INDEX IF NOT EXISTS idx_mcpl_artifacts_execution ON mcpl_artifacts(execution_id)")

    _run(conn, """CREATE TABLE IF NOT EXISTS mcpl_states (
        state_id TEXT PRIMARY KEY,
        artifact_id TEXT,
        state_type TEXT,
        previous_hash TEXT DEFAULT '',
        current_hash TEXT DEFAULT '',
        scope TEXT DEFAULT '',
        created_at TEXT,
        execution_id TEXT DEFAULT '',
        tenant_id TEXT DEFAULT '',
        metadata TEXT DEFAULT '{}'
    )""")

    _run(conn, """CREATE TABLE IF NOT EXISTS mcpl_verifications (
        verification_id TEXT PRIMARY KEY,
        subject_id TEXT,
        subject_type TEXT,
        verifier_type TEXT,
        verifier_id TEXT DEFAULT '',
        method TEXT DEFAULT '',
        expected_condition TEXT DEFAULT '{}',
        observed_result TEXT DEFAULT '{}',
        status TEXT DEFAULT 'requested',
        confidence REAL DEFAULT 0.0,
        evidence_ref TEXT DEFAULT '',
        created_at TEXT,
        verified_at TEXT DEFAULT '',
        correlation_id TEXT DEFAULT '',
        causation_id TEXT DEFAULT '',
        tenant_id TEXT DEFAULT '',
        decision_id TEXT DEFAULT ''
    )""")
    _run(conn, "CREATE INDEX IF NOT EXISTS idx_mcpl_verifications_subject ON mcpl_verifications(subject_id)")

    _run(conn, """CREATE TABLE IF NOT EXISTS mcpl_joins (
        join_id TEXT PRIMARY KEY,
        intent_id TEXT,
        condition TEXT DEFAULT 'all',
        required_count INTEGER DEFAULT 0,
        timeout_ms INTEGER DEFAULT 0,
        branch_ids TEXT DEFAULT '[]',
        completed_branches TEXT DEFAULT '[]',
        status TEXT DEFAULT 'pending',
        created_at TEXT,
        tenant_id TEXT DEFAULT '',
        metadata TEXT DEFAULT '{}'
    )""")

    _run(conn, """CREATE TABLE IF NOT EXISTS mcpl_provenance_events (
        event_id TEXT PRIMARY KEY,
        schema_version TEXT DEFAULT '1.0.0',
        parent_id TEXT DEFAULT '',
        causation_id TEXT DEFAULT '',
        correlation_id TEXT DEFAULT '',
        event_type TEXT,
        timestamp TEXT,
        tenant_id TEXT DEFAULT '',
        actor TEXT DEFAULT '{}',
        subject TEXT DEFAULT '{}',
        causal_links TEXT DEFAULT '[]',
        payload TEXT DEFAULT '{}',
        integrity TEXT DEFAULT '{}',
        retention TEXT DEFAULT '{}'
    )""")
    _run(conn, "CREATE INDEX IF NOT EXISTS idx_mcpl_events_type ON mcpl_provenance_events(event_type)")
    _run(conn, "CREATE INDEX IF NOT EXISTS idx_mcpl_events_correlation ON mcpl_provenance_events(correlation_id)")
    _run(conn, "CREATE INDEX IF NOT EXISTS idx_mcpl_events_causation ON mcpl_provenance_events(causation_id)")
    _run(conn, "CREATE INDEX IF NOT EXISTS idx_mcpl_events_timestamp ON mcpl_provenance_events(timestamp)")

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
