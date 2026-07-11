import sqlite3
from runtime.database import _table_has_column, get_connection


class TestDatabaseValidation:
    def setup_method(self):
        self.conn = sqlite3.connect(":memory:")
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("CREATE TABLE workers (id INTEGER, started_at TEXT, name TEXT)")

    def test_known_table_known_column(self):
        assert _table_has_column(self.conn, "workers", "started_at") is True

    def test_known_table_unknown_column(self):
        assert _table_has_column(self.conn, "workers", "nonexistent") is False

    def test_unknown_table_name(self):
        assert _table_has_column(self.conn, "users", "id") is False

    def test_sql_injection_table_name(self):
        assert _table_has_column(self.conn, "workers; DROP TABLE workers", "id") is False

    def test_sql_injection_attempt_2(self):
        assert _table_has_column(self.conn, "workers' OR '1'='1", "id") is False

    def test_workers_table_intact_after_injection_attempts(self):
        cursor = self.conn.execute("SELECT COUNT(*) FROM workers")
        count = cursor.fetchone()[0]
        assert count == 0
