from datetime import datetime
from memory.storage import database


class RelationshipMemory:
    """How Ruby feels about the user — trust, mood, message count."""

    def __init__(self, user_name="Addie"):
        self.user_name = user_name
        self._ensure_row()

    def _ensure_row(self):
        conn = database.get_connection()
        c = conn.cursor()
        c.execute(
            "SELECT id FROM relationship WHERE user_name = ?",
            (self.user_name,),
        )
        if c.fetchone() is None:
            c.execute(
                """
                INSERT INTO relationship (user_name, message_count, trust_level, mood, last_updated)
                VALUES (?, 0, 0, 'guarded', ?)
                """,
                (self.user_name, datetime.now().isoformat(timespec="seconds")),
            )
            conn.commit()
        conn.close()

    def get_state(self):
        conn = database.get_connection()
        c = conn.cursor()
        c.execute(
            "SELECT message_count, trust_level, mood FROM relationship WHERE user_name = ?",
            (self.user_name,),
        )
        row = c.fetchone()
        conn.close()
        if row:
            return {
                "message_count": row[0],
                "trust_level": row[1],
                "mood": row[2],
            }
        return {"message_count": 0, "trust_level": 0, "mood": "guarded"}

    def increment_messages(self):
        conn = database.get_connection()
        c = conn.cursor()
        c.execute(
            """
            UPDATE relationship
            SET message_count = message_count + 1,
                last_updated = ?
            WHERE user_name = ?
            """,
            (datetime.now().isoformat(timespec="seconds"), self.user_name),
        )
        conn.commit()
        conn.close()

    def add_trust(self, amount=1):
        conn = database.get_connection()
        c = conn.cursor()
        c.execute(
            """
            UPDATE relationship
            SET trust_level = trust_level + ?,
                last_updated = ?
            WHERE user_name = ?
            """,
            (amount, datetime.now().isoformat(timespec="seconds"), self.user_name),
        )
        conn.commit()
        conn.close()

    def set_mood(self, mood):
        conn = database.get_connection()
        c = conn.cursor()
        c.execute(
            """
            UPDATE relationship
            SET mood = ?, last_updated = ?
            WHERE user_name = ?
            """,
            (mood, datetime.now().isoformat(timespec="seconds"), self.user_name),
        )
        conn.commit()
        conn.close()

    def wipe(self):
        conn = database.get_connection()
        c = conn.cursor()
        c.execute("DELETE FROM relationship WHERE user_name = ?", (self.user_name,))
        conn.commit()
        conn.close()
        self._ensure_row()
