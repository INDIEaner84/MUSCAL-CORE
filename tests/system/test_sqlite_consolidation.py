import json
import os
import tempfile

import pytest


@pytest.fixture(autouse=True)
def reset_state():
    from plugin_registry import PLUGINS, HOOKS
    PLUGINS.clear()
    HOOKS.clear()
    HOOKS.update({
        "kernel_before": [], "kernel_after": [],
        "mkc_before": [], "mkc_after": [],
        "bridge_before": [], "bridge_after": [],
        "optimizer_before": [], "optimizer_after": [],
        "mel_before": [], "mel_after": [],
        "feedback_before": [], "feedback_after": [],
        "memory_before": [], "memory_after": [],
    })
    yield


class TestSQLiteConsolidation:
    def test_mcxf_snapshots_table_exists(self):
        import config
        from runtime.database import init_db, get_connection
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test.db")
            old_db = config.DB_PATH
            try:
                config.DB_PATH = type(config.DB_PATH)(db_path)
                init_db()
                conn = get_connection()
                tables = [r["name"] for r in conn.execute(
                    "SELECT name FROM sqlite_master WHERE type='table'"
                )]
                assert "mcxf_snapshots" in tables, f"Tables: {tables}"
                conn.close()
            finally:
                config.DB_PATH = old_db

    def test_audit_log_table_exists(self):
        import config
        from runtime.database import init_db, get_connection
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test.db")
            old_db = config.DB_PATH
            try:
                config.DB_PATH = type(config.DB_PATH)(db_path)
                init_db()
                conn = get_connection()
                tables = [r["name"] for r in conn.execute(
                    "SELECT name FROM sqlite_master WHERE type='table'"
                )]
                assert "audit_log" in tables
                conn.close()
            finally:
                config.DB_PATH = old_db

    def test_schema_version_table_exists(self):
        import config
        from runtime.database import init_db, get_connection
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test.db")
            old_db = config.DB_PATH
            try:
                config.DB_PATH = type(config.DB_PATH)(db_path)
                init_db()
                conn = get_connection()
                rows = conn.execute("SELECT version, description FROM schema_version").fetchall()
                assert len(rows) >= 1
                assert rows[0]["version"] == 1
                conn.close()
            finally:
                config.DB_PATH = old_db

    def _reset_memory_conn(self):
        import memory
        memory.reset_connection()

    def test_memory_store_snapshot_writes_to_muscal_db(self):
        import config
        from runtime.database import init_db, get_connection
        self._reset_memory_conn()
        with tempfile.TemporaryDirectory() as tmpdir:
            original = os.getcwd()
            os.chdir(tmpdir)
            try:
                db_path = os.path.join(tmpdir, "muscal.db")
                old_db = config.DB_PATH
                config.DB_PATH = type(config.DB_PATH)(db_path)
                init_db()
                self._reset_memory_conn()
                from memory import store_snapshot
                mid = store_snapshot("test input", {"cmd": "test"}, {"ok": True}, {"score": 0.9})
                assert mid is not None
                conn = get_connection()
                row = conn.execute("SELECT * FROM mcxf_snapshots WHERE id = ?", (mid,)).fetchone()
                assert row is not None
                assert row["input_text"] == "test input"
                assert json.loads(row["mcxf_json"]) == {"cmd": "test"}
                conn.close()
            finally:
                os.chdir(original)
                config.DB_PATH = old_db

    def test_memory_retrieve_by_id_works(self):
        import config
        from runtime.database import init_db
        self._reset_memory_conn()
        with tempfile.TemporaryDirectory() as tmpdir:
            original = os.getcwd()
            os.chdir(tmpdir)
            try:
                db_path = os.path.join(tmpdir, "muscal.db")
                old_db = config.DB_PATH
                config.DB_PATH = type(config.DB_PATH)(db_path)
                init_db()
                self._reset_memory_conn()
                from memory import store_snapshot, retrieve_by_id
                mid = store_snapshot("retrieve test", {"a": 1}, {"b": 2}, {"c": 3})
                result = retrieve_by_id(mid)
                assert result is not None
                assert result["input_text"] == "retrieve test"
                assert result["mcxf"] == {"a": 1}
            finally:
                os.chdir(original)
                config.DB_PATH = old_db

    def test_memory_log_writes_to_audit_log(self):
        import config
        from runtime.database import init_db, get_connection
        self._reset_memory_conn()
        with tempfile.TemporaryDirectory() as tmpdir:
            original = os.getcwd()
            os.chdir(tmpdir)
            try:
                db_path = os.path.join(tmpdir, "muscal.db")
                old_db = config.DB_PATH
                config.DB_PATH = type(config.DB_PATH)(db_path)
                init_db()
                self._reset_memory_conn()
                from memory import log_jsonl
                log_jsonl({"type": "test_event", "value": 42})
                conn = get_connection()
                rows = conn.execute("SELECT * FROM audit_log").fetchall()
                assert len(rows) >= 1
                assert rows[0]["entry_type"] == "test_event"
                conn.close()
            finally:
                os.chdir(original)
                config.DB_PATH = old_db

    def test_no_memory_db_file_created(self):
        import config
        from runtime.database import init_db
        self._reset_memory_conn()
        with tempfile.TemporaryDirectory() as tmpdir:
            original = os.getcwd()
            os.chdir(tmpdir)
            try:
                db_path = os.path.join(tmpdir, "muscal.db")
                old_db = config.DB_PATH
                config.DB_PATH = type(config.DB_PATH)(db_path)
                init_db()
                self._reset_memory_conn()
                from memory import store_snapshot
                store_snapshot("no old db", {}, {})
                assert not os.path.exists("storage/memory.db")
                assert os.path.exists(db_path)
            finally:
                os.chdir(original)
                config.DB_PATH = old_db
