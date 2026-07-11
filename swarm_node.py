import sqlite3


class SwarmNode:
    def __init__(self, node_id):
        self.id = node_id
        self.conn = sqlite3.connect(f"{node_id}.db")
        self._init_db()

    def _init_db(self):
        self.conn.execute("""
        CREATE TABLE IF NOT EXISTS memory (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            data TEXT
        )
        """)

    def store(self, data):
        self.conn.execute("INSERT INTO memory (data) VALUES (?)", (str(data),))
        self.conn.commit()

    def load(self):
        return self.conn.execute("SELECT data FROM memory").fetchall()

    def execute(self, tool, args):
        if tool == "opencode.run":
            import subprocess
            return subprocess.run(
                ["opencode", "run", args["prompt"]],
                capture_output=True,
                text=True
            ).stdout

        if tool == "browser.open":
            return f"OPEN_BROWSER:{args['url']}"

        return "UNKNOWN_TOOL"
