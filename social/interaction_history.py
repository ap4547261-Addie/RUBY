from datetime import datetime
from memory import database


class InteractionHistory:
    """
    A log of every interaction Ruby has ever had with every person.
    No caps. No pruning. Every exchange is remembered, forever.
    """

    def __init__(self):
        self._ensure_table()

    def _ensure_table(self):
        conn = database.get_connection()
        c = conn.cursor()
        c.execute("""
            CREATE TABLE IF NOT EXISTS interaction_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                subject TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                user_message TEXT,
                ruby_reply TEXT,
                emotion_at_time TEXT,
                mood_at_time TEXT
            )
        """)
        conn.commit()
        conn.close()

    def log(self, subject, user_message, ruby_reply,
            emotion_at_time="", mood_at_time=""):
        conn = database.get_connection()
        c = conn.cursor()
        c.execute("""
            INSERT INTO interaction_history
                (subject, timestamp, user_message, ruby_reply, emotion_at_time, mood_at_time)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            subject,
            datetime.now().isoformat(timespec="seconds"),
            user_message,
            ruby_reply,
            emotion_at_time,
            mood_at_time,
        ))
        conn.commit()
        conn.close()

    def for_subject(self, subject):
        """Every interaction with this subject. No cap."""
        conn = database.get_connection()
        c = conn.cursor()
        c.execute("""
            SELECT timestamp, user_message, ruby_reply
            FROM interaction_history
            WHERE subject = ?
            ORDER BY id ASC
        """, (subject,))
        rows = c.fetchall()
        conn.close()
        return rows

    def count_for(self, subject):
        conn = database.get_connection()
        c = conn.cursor()
        c.execute("SELECT COUNT(*) FROM interaction_history WHERE subject = ?", (subject,))
        n = c.fetchone()[0]
        conn.close()
        return n

    def total_count(self):
        conn = database.get_connection()
        c = conn.cursor()
        c.execute("SELECT COUNT(*) FROM interaction_history")
        n = c.fetchone()[0]
        conn.close()
        return n

    def all_subjects(self):
        conn = database.get_connection()
        c = conn.cursor()
        c.execute("""
            SELECT subject, COUNT(*) as cnt
            FROM interaction_history
            GROUP BY subject
            ORDER BY cnt DESC
        """)
        rows = c.fetchall()
        conn.close()
        return rows

    def wipe(self):
        conn = database.get_connection()
        c = conn.cursor()
        c.execute("DELETE FROM interaction_history")
        conn.commit()
        conn.close()
