from datetime import datetime
from memory import database


class EpisodicMemory:
    """Raw conversations — the timeline of everything that happened."""

    def remember(self, user_message, ruby_reply, importance=3):
        conn = database.get_connection()
        c = conn.cursor()
        c.execute(
            """
            INSERT INTO episodes (user_message, ruby_reply, timestamp, importance)
            VALUES (?, ?, ?, ?)
            """,
            (user_message, ruby_reply,
             datetime.now().isoformat(timespec="seconds"), importance),
        )
        conn.commit()
        conn.close()

    def get_recent(self, limit=5):
        conn = database.get_connection()
        c = conn.cursor()
        c.execute(
            "SELECT user_message, ruby_reply, timestamp FROM episodes ORDER BY id DESC LIMIT ?",
            (limit,),
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
            SELECT user_message, ruby_reply, timestamp
            FROM episodes
            WHERE LOWER(user_message) LIKE ? OR LOWER(ruby_reply) LIKE ?
            ORDER BY id DESC LIMIT ?
            """,
            (like, like, limit),
        )
        rows = c.fetchall()
        conn.close()
        return rows

    def count(self):
        conn = database.get_connection()
        c = conn.cursor()
        c.execute("SELECT COUNT(*) FROM episodes")
        n = c.fetchone()[0]
        conn.close()
        return n

    def wipe(self):
        conn = database.get_connection()
        c = conn.cursor()
        c.execute("DELETE FROM episodes")
        conn.commit()
        conn.close()
