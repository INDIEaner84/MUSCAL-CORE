import warnings

import json
import sqlite3

warnings.warn(
    "mcxf_sql.py is DEPRECATED (ADR-010). Use runtime.database directly.",
    DeprecationWarning, stacklevel=2
)


class MCXFSQL:
    def __init__(self, db="mcxf.db"):
        self.conn = sqlite3.connect(db)
        self._init()

    def _init(self):
        self.conn.execute("""
        CREATE TABLE IF NOT EXISTS mcxf (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            content TEXT
        )
        """)

    def insert(self, mcxf):
        self.conn.execute(
            "INSERT INTO mcxf (content) VALUES (?)",
            (json.dumps(mcxf),)
        )
        self.conn.commit()

    def fetch_all(self):
        cur = self.conn.execute("SELECT content FROM mcxf")
        return [json.loads(row[0]) for row in cur.fetchall()]

    def count(self):
        cur = self.conn.execute("SELECT COUNT(*) FROM mcxf")
        return cur.fetchone()[0]
