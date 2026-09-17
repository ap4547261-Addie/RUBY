from datetime import datetime
from memory import database


class IdentityHistory:
    """A log of identity changes. No entry limit, no pruning."""

    def __init__(self, user_name="not_set"):
        self.user_name = user_name
        self._ensure_table()

    def _ensure_table(self):
        conn = database.get_connection()
        c = conn.cursor()
        c.execute("""
            CREATE TABLE IF NOT EXISTS identity_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                event_type TEXT NOT NULL,
                description TEXT NOT NULL
            )
        """)
        conn.commit()
        conn.close()

    def log(self, event_type, description):
        conn = database.get_connection()
        c = conn.cursor()
        c.execute("""
            INSERT INTO identity_history (timestamp, event_type, description)
            VALUES (?, ?, ?)
        """, (datetime.now().isoformat(timespec="seconds"), event_type, description))
        conn.commit()
        conn.close()
        print(f"📜 Identity log: {description}")

    def recent(self, limit=10):
        conn = database.get_connection()
        c = conn.cursor()
        c.execute("""
            SELECT timestamp, event_type, description
            FROM identity_history
            ORDER BY id DESC
            LIMIT ?
        """, (limit,))
        rows = c.fetchall()
        conn.close()
        return rows

    def all_entries(self):
        """Return every entry — no cap."""
        conn = database.get_connection()
        c = conn.cursor()
        c.execute("""
            SELECT timestamp, event_type, description
            FROM identity_history
            ORDER BY id ASC
        """)
        rows = c.fetchall()
        conn.close()
        return rows

    def count(self):
        conn = database.get_connection()
        c = conn.cursor()
        c.execute("SELECT COUNT(*) FROM identity_history")
        n = c.fetchone()[0]
        conn.close()
        return n

    def wipe(self):
        conn = database.get_connection()
        c = conn.cursor()
        c.execute("DELETE FROM identity_history")
        conn.commit()
        conn.close()
