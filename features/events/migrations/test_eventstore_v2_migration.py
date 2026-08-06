"""EventStore v2 additive migration tests (P0-1).

Covers the `eventstore_v2_migration` module contract:
- fresh DB: missing v2 fields are added, data unaffected
- existing DB: legacy v1 rows stay byte-identical, new fields defaulted
- double migration: second run is a no-op (idempotent)
- rollback simulation: added columns dropped only when default-valued;
  refused when non-default values present (no data loss)
- schema validation: final column set and types match the contract
"""

import os
import sqlite3
import sys
from pathlib import Path

import pytest

sys.path.insert(0, os.path.dirname(__file__))

from eventstore_v2_migration import (  # noqa: E402
    DEFAULT_VALUES,
    MIGRATION_ADDED_FIELDS,
    TABLE,
    V2_FIELDS,
    backup_db,
    current_columns,
    rollback_migration,
    run_migration,
    schema_status,
)

CURRENT_COLUMNS = [
    "seq",
    "topic",
    "payload",
    "source",
    "priority",
    "timestamp",
    "event_id",
    "created_at",
    "execution_id",
    "correlation_id",
    "causation_id",
    "execution_mode",
    "verification_state",
    "execution_state",
    "schema_version",
    "is_replayed",
    "receipt_id",
    "aggregate_id",
    "aggregate_type",
    "metadata",
    "payload_delta",
    "parent_event_id",
    "prev_hash",
    "logical_time",
]

# Fields this migration adds (missing in CURRENT_COLUMNS)
ADDED_COLUMNS = ["event_version", "agent_id", "task_id", "previous_hash", "event_hash", "confidence"]


def _make_v1_db(tmp_path: Path, n_rows: int = 5) -> Path:
    db = tmp_path / "legacy.db"
    conn = sqlite3.connect(str(db))
    conn.execute(
        """CREATE TABLE stored_events (
            seq        INTEGER PRIMARY KEY AUTOINCREMENT,
            topic      TEXT NOT NULL,
            payload    TEXT NOT NULL DEFAULT '{}',
            source     TEXT NOT NULL DEFAULT '',
            priority   TEXT NOT NULL DEFAULT 'NORMAL',
            timestamp  REAL NOT NULL,
            event_id   TEXT NOT NULL UNIQUE,
            created_at TEXT NOT NULL,
            execution_id TEXT NOT NULL DEFAULT '',
            correlation_id TEXT NOT NULL DEFAULT '',
            causation_id TEXT NOT NULL DEFAULT '',
            execution_mode TEXT NOT NULL DEFAULT 'real',
            execution_state TEXT NOT NULL DEFAULT 'planned',
            verification_state TEXT NOT NULL DEFAULT 'unverified',
            is_replayed INTEGER NOT NULL DEFAULT 0,
            receipt_id TEXT NOT NULL DEFAULT '',
            aggregate_id TEXT NOT NULL DEFAULT '',
            aggregate_type TEXT NOT NULL DEFAULT '',
            metadata TEXT NOT NULL DEFAULT '{}',
            payload_delta TEXT NOT NULL DEFAULT '{}',
            parent_event_id TEXT NOT NULL DEFAULT '',
            prev_hash TEXT NOT NULL DEFAULT '',
            logical_time INTEGER NOT NULL DEFAULT 0,
            schema_version INTEGER NOT NULL DEFAULT 1
        )"""
    )
    for i in range(n_rows):
        conn.execute(
            "INSERT INTO stored_events (topic, payload, source, timestamp, event_id, created_at)"
            " VALUES (?, ?, ?, ?, ?, ?)",
            (f"legacy.{i}", '{"n": %d}' % i, "v1", i + 0.5, f"evt-{i}", "2026-08-01T00:00:00"),
        )
    conn.commit()
    conn.close()
    return db


def _read_rows(db: Path, columns: list | None = None) -> list:
    conn = sqlite3.connect(str(db))
    try:
        cols = ", ".join(columns) if columns else "*"
        return conn.execute(f"SELECT {cols} FROM {TABLE} ORDER BY seq").fetchall()
    finally:
        conn.close()


def _cols_with_types(db: Path) -> dict:
    conn = sqlite3.connect(str(db))
    try:
        return {
            r[1]: (r[2], r[3], r[4])
            for r in conn.execute(f"PRAGMA table_info({TABLE})").fetchall()
        }
    finally:
        conn.close()


class TestFreshDb:
    def test_missing_fields_added(self, tmp_path):
        db = _make_v1_db(tmp_path, n_rows=0)
        result = run_migration(db)
        assert result["status"] == "MIGRATED"
        assert set(result["applied_columns"]) == set(ADDED_COLUMNS)

    def test_legacy_columns_untouched(self, tmp_path):
        db = _make_v1_db(tmp_path, n_rows=0)
        before = _cols_with_types(db)
        run_migration(db)
        after = _cols_with_types(db)
        for col, info in before.items():
            assert after[col] == info, f"column {col} was modified"

    def test_fresh_db_data_still_empty(self, tmp_path):
        db = _make_v1_db(tmp_path, n_rows=0)
        run_migration(db)
        assert _read_rows(db) == []


class TestExistingDb:
    def test_legacy_rows_byte_identical(self, tmp_path):
        db = _make_v1_db(tmp_path, n_rows=7)
        before = _read_rows(db, columns=CURRENT_COLUMNS)
        run_migration(db)
        assert _read_rows(db, columns=CURRENT_COLUMNS) == before

    def test_new_fields_defaulted(self, tmp_path):
        db = _make_v1_db(tmp_path, n_rows=3)
        run_migration(db)
        rows = _read_rows(db, columns=["event_version", "agent_id", "task_id", "previous_hash", "event_hash", "confidence", "metadata", "source", "verification_state"])
        for d in rows:
            assert d[0] == 2  # event_version
            assert d[1] == ""  # agent_id
            assert d[2] == ""  # task_id
            assert d[3] == ""  # previous_hash
            assert d[4] == ""  # event_hash
            assert d[5] == 0.0  # confidence
            assert d[6] == "{}"  # metadata
            assert d[7] == "v1"  # source untouched
            assert d[8] == "unverified"  # verification_state untouched


class TestDoubleMigration:
    def test_second_run_noop(self, tmp_path):
        db = _make_v1_db(tmp_path, n_rows=4)
        first = run_migration(db)
        second = run_migration(db)
        assert first["status"] == "MIGRATED"
        assert second["status"] == "ALREADY_UP_TO_DATE"
        assert second["applied_columns"] == []

    def test_three_runs_schema_stable(self, tmp_path):
        db = _make_v1_db(tmp_path)
        run_migration(db)
        run_migration(db)
        run_migration(db)
        assert len(_cols_with_types(db)) == len(CURRENT_COLUMNS) + len(ADDED_COLUMNS)


class TestRollbackSimulation:
    def test_rollback_drops_added_default_columns(self, tmp_path):
        db = _make_v1_db(tmp_path, n_rows=2)
        run_migration(db)
        result = rollback_migration(db, dry_run=False)
        assert result["status"] == "ROLLED_BACK"
        cols = _cols_with_types(db)
        for f in MIGRATION_ADDED_FIELDS:
            assert f not in cols
        for f in CURRENT_COLUMNS:
            assert f in cols
        assert _read_rows(db) is not None

    def test_rollback_dry_run_no_change(self, tmp_path):
        db = _make_v1_db(tmp_path, n_rows=2)
        run_migration(db)
        result = rollback_migration(db, dry_run=True)
        assert result["status"] == "DRY_RUN"
        assert set(result["droppable"]) == set(MIGRATION_ADDED_FIELDS)
        assert len(_cols_with_types(db)) == len(CURRENT_COLUMNS) + len(ADDED_COLUMNS)

    def test_rollback_refused_when_data_present(self, tmp_path):
        db = _make_v1_db(tmp_path, n_rows=1)
        run_migration(db)
        conn = sqlite3.connect(str(db))
        conn.execute(f"UPDATE {TABLE} SET event_hash = 'non-default' WHERE seq = 1")
        conn.commit()
        conn.close()
        result = rollback_migration(db, dry_run=False)
        assert result["status"] == "REFUSED"
        assert "event_hash" in result["refused"]
        assert "agent_id" in result["droppable"]
        cols = _cols_with_types(db)
        assert "event_hash" in cols


class TestSchemaValidation:
    def test_expected_final_schema(self, tmp_path):
        db = _make_v1_db(tmp_path)
        run_migration(db)
        cols = _cols_with_types(db)
        assert set(cols) == set(CURRENT_COLUMNS) | set(V2_FIELDS)

    def test_schema_status_reports_missing(self, tmp_path):
        db = _make_v1_db(tmp_path)
        conn = sqlite3.connect(str(db))
        try:
            status = schema_status(conn)
        finally:
            conn.close()
        assert set(status["missing"]) == set(ADDED_COLUMNS)

    def test_backup_created(self, tmp_path):
        db = _make_v1_db(tmp_path, n_rows=3)
        backup = backup_db(db)
        assert backup.exists()
        assert _read_rows(backup) == _read_rows(db)
