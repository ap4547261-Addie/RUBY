from datetime import datetime
from memory import database


class RelationshipMemory:
    """
    Ruby's feelings toward the user — multiple continuous dimensions,
    each growing (or shrinking) based on real interactions. No caps.
    """

    def __init__(self, user_name="Addie"):
        self.user_name = user_name
        self._ensure_row()

    def _ensure_row(self):
        conn = database.get_connection()
        c = conn.cursor()
        c.execute("""
            CREATE TABLE IF NOT EXISTS relationship (
                id INTEGER PRIMARY KEY,
                user_name TEXT UNIQUE NOT NULL,
                message_count INTEGER DEFAULT 0,
                trust REAL DEFAULT 0.0,
                familiarity REAL DEFAULT 0.0,
                attachment REAL DEFAULT 0.0,
                respect REAL DEFAULT 0.0,
                last_updated TEXT
            )
        """)
        c.execute("SELECT id FROM relationship WHERE user_name = ?", (self.user_name,))
        if c.fetchone() is None:
            c.execute(
                """
                INSERT INTO relationship
                    (user_name, message_count, trust, familiarity, attachment, respect, last_updated)
                VALUES (?, 0, 0.0, 0.0, 0.0, 0.0, ?)
                """,
                (self.user_name, datetime.now().isoformat(timespec="seconds")),
            )
            conn.commit()
        conn.close()

    def get_state(self):
        conn = database.get_connection()
        c = conn.cursor()
        c.execute("""
            SELECT message_count, trust, familiarity, attachment, respect
            FROM relationship WHERE user_name = ?
        """, (self.user_name,))
        row = c.fetchone()
        conn.close()
        if row:
            return {
                "message_count": row[0],
                "trust": round(row[1], 3),
                "familiarity": round(row[2], 3),
                "attachment": round(row[3], 3),
                "respect": round(row[4], 3),
            }
        return {"message_count": 0, "trust": 0, "familiarity": 0, "attachment": 0, "respect": 0}

    def _bump(self, column, amount):
        conn = database.get_connection()
        c = conn.cursor()
        c.execute(
            f"""
            UPDATE relationship
            SET {column} = {column} + ?, last_updated = ?
            WHERE user_name = ?
            """,
            (amount, datetime.now().isoformat(timespec="seconds"), self.user_name),
        )
        conn.commit()
        conn.close()

    # -------------------------
    # Growth dimensions (no caps — they can grow forever)
    # -------------------------
    def add_message(self):
        conn = database.get_connection()
        c = conn.cursor()
        c.execute(
            "UPDATE relationship SET message_count = message_count + 1, last_updated = ? WHERE user_name = ?",
            (datetime.now().isoformat(timespec="seconds"), self.user_name),
        )
        conn.commit()
        conn.close()

    def grow_familiarity(self, amount=0.02):
        """Always grows a little — just for showing up."""
        self._bump("familiarity", amount)

    def grow_trust(self, amount=0.05):
        """Grows when the user says something honest or personal."""
        self._bump("trust", amount)

    def grow_respect(self, amount=0.03):
        """Grows when the user says something clever, funny, or real."""
        self._bump("respect", amount)

    def grow_attachment(self, amount=0.01):
        """Grows slowly — time + consistency. This is the deep one."""
        self._bump("attachment", amount)

    def shrink_trust(self, amount=0.1):
        """Shrinks if the user is rude, fake, or pushy."""
        self._bump("trust", -amount)

    def shrink_respect(self, amount=0.1):
        """Shrinks if the user says something dumb or childish."""
        self._bump("respect", -amount)

    def wipe(self):
        conn = database.get_connection()
        c = conn.cursor()
        c.execute("DELETE FROM relationship WHERE user_name = ?", (self.user_name,))
        conn.commit()
        conn.close()
        self._ensure_row()
