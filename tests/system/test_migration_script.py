import json
import os
import sqlite3
import tempfile

import pytest


class TestMigrationScript:
    def _create_old_db(self, tmpdir):
        old_db = os.path.join(tmpdir, "storage", "memory.db")
        os.makedirs(os.path.dirname(old_db), exist_ok=True)
        conn = sqlite3.connect(old_db)
        conn.execute("CREATE TABLE IF NOT EXISTS mcxf_store ("
                     "id INTEGER PRIMARY KEY AUTOINCREMENT, input_text TEXT,"
                     "mcxf_json TEXT, result_json TEXT, feedback_json TEXT, created_at TEXT)")
        conn.execute("INSERT INTO mcxf_store (input_text, mcxf_json, result_json, feedback_json) "
                     "VALUES (?, ?, ?, ?)", ("test input", '{"cmd": "test"}', '{"ok": true}', '{"score": 0.9}'))
        conn.commit()
        conn.close()
        return old_db

    def _create_old_jsonl(self, tmpdir):
        log_path = os.path.join(tmpdir, "storage", "logs.jsonl")
        entries = [
            {"type": "test_event", "value": 42},
            {"type": "pipeline_run", "duration_ms": 150},
        ]
        with open(log_path, "w") as f:
            for e in entries:
                f.write(json.dumps(e) + "\n")
        return log_path

    def test_migration_script_migrates_old_db(self):
        import config
        from scripts.migrate_sqlite import run_migrations
        with tempfile.TemporaryDirectory() as tmpdir:
            original = os.getcwd()
            os.chdir(tmpdir)
            try:
                self._create_old_db(tmpdir)
                self._create_old_jsonl(tmpdir)
                db_path = os.path.join(tmpdir, "muscal.db")
                config.DB_PATH = type(config.DB_PATH)(db_path)
                success = run_migrations()
                assert success
                from runtime.database import get_connection
                conn = get_connection()
                snapshots = conn.execute("SELECT COUNT(*) FROM mcxf_snapshots").fetchone()[0]
                assert snapshots >= 1
                logs = conn.execute("SELECT COUNT(*) FROM audit_log").fetchone()[0]
                assert logs >= 1
                conn.close()
            finally:
                os.chdir(original)

    def test_migration_idempotent(self):
        import config
        from scripts.migrate_sqlite import run_migrations
        with tempfile.TemporaryDirectory() as tmpdir:
            original = os.getcwd()
            os.chdir(tmpdir)
            try:
                self._create_old_db(tmpdir)
                self._create_old_jsonl(tmpdir)
                db_path = os.path.join(tmpdir, "muscal.db")
                config.DB_PATH = type(config.DB_PATH)(db_path)
                run_migrations()
                run_migrations()
                from runtime.database import get_connection
                conn = get_connection()
                snapshots = conn.execute("SELECT COUNT(*) FROM mcxf_snapshots").fetchone()[0]
                assert snapshots == 1
                conn.close()
            finally:
                os.chdir(original)
