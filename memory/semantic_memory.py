from datetime import datetime
from memory.storage import database


class SemanticMemory:
    """Facts about the user — the important, distilled stuff."""

    def remember_fact(self, subject, key, value):
        """Save or update a fact. Example: subject='Addie', key='favorite_color', value='blue'."""
        conn = database.get_connection()
        c = conn.cursor()
        c.execute(
            """
            INSERT INTO facts (subject, key, value, timestamp)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(subject, key) DO UPDATE SET
                value = excluded.value,
                timestamp = excluded.timestamp
            """,
            (subject.lower(), key.lower(), value,
             datetime.now().isoformat(timespec="seconds")),
        )
        conn.commit()
        conn.close()

    def get_fact(self, subject, key):
        conn = database.get_connection()
        c = conn.cursor()
        c.execute(
            "SELECT value FROM facts WHERE subject = ? AND key = ?",
            (subject.lower(), key.lower()),
        )
        row = c.fetchone()
        conn.close()
        return row[0] if row else None

    def get_all_for(self, subject):
        conn = database.get_connection()
        c = conn.cursor()
        c.execute(
            "SELECT key, value FROM facts WHERE subject = ? ORDER BY id DESC",
            (subject.lower(),),
        )
        rows = c.fetchall()
        conn.close()
        return rows

    def search(self, keyword, limit=5):
        if not keyword or len(keyword) < 3:
            return []
        conn = database.get_connection()
        c = conn.cursor()
        like = f"%{keyword.lower()}%"
        c.execute(
            """
            SELECT key, value FROM facts
            WHERE LOWER(key) LIKE ? OR LOWER(value) LIKE ?
            ORDER BY id DESC LIMIT ?
            """,
            (like, like, limit),
        )
        rows = c.fetchall()
        conn.close()
        return rows

    def wipe(self):
        conn = database.get_connection()
        c = conn.cursor()
        c.execute("DELETE FROM facts")
        conn.commit()
        conn.close()
