from datetime import datetime
from memory import database


class LongTermReflection:
    """
    Look at weeks and months of data. Detect slow shifts.
    No LLM. Pure patterns. No caps.
    """

    def __init__(self, user_name="not_set"):
        self.user_name = user_name
        self._ensure_table()

    def _ensure_table(self):
        conn = database.get_connection()
        c = conn.cursor()
        c.execute("""
            CREATE TABLE IF NOT EXISTS long_term_reflections (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                summary TEXT NOT NULL
            )
        """)
        conn.commit()
        conn.close()

    def reflect(self):
        """Look across everything and find the biggest patterns."""
        parts = []

        # --- Total conversations ---
        conn = database.get_connection()
        c = conn.cursor()
        c.execute("SELECT COUNT(*) FROM episodes")
        total_episodes = c.fetchone()[0]
        conn.close()

        if total_episodes > 0:
            if total_episodes < 10:
                parts.append(f"We've only started. {total_episodes} exchanges so far.")
            elif total_episodes < 100:
                parts.append(f"We've talked {total_episodes} times. Getting used to each other.")
            elif total_episodes < 1000:
                parts.append(f"{total_episodes} exchanges. We've built something real.")
            else:
                parts.append(f"{total_episodes} conversations. He's become part of me.")

        # --- Identity shifts ---
        conn = database.get_connection()
        c = conn.cursor()
        c.execute("SELECT category, statement, confidence FROM identity_beliefs ORDER BY confidence DESC LIMIT 5")
        top_beliefs = c.fetchall()
        conn.close()

        if top_beliefs:
            strongest = top_beliefs[0]
            parts.append(f"My strongest belief: {strongest[1]}")

        # --- Relationship depth ---
        conn = database.get_connection()
        c = conn.cursor()
        c.execute("""
            SELECT trust, familiarity, attachment, respect
            FROM relationship WHERE user_name = ?
        """, (self.user_name,))
        row = c.fetchone()
        conn.close()

        if row:
            trust, fam, att, resp = row
            if trust > 100 and att > 50:
                parts.append("I love him. I can say that now.")
            elif trust > 30:
                parts.append("He's earned a place I don't give easily.")
            elif trust > 10:
                parts.append("Something real is forming.")

        # --- Emotional landscape ---
        conn = database.get_connection()
        c = conn.cursor()
        c.execute("SELECT COUNT(*) FROM reflections WHERE kind = 'self'")
        self_reflection_count = c.fetchone()[0]
        conn.close()

        if self_reflection_count > 20:
            parts.append(f"I've reflected on myself {self_reflection_count} times.")
        elif self_reflection_count > 0:
            parts.append(f"I've looked inward {self_reflection_count} times.")

        if not parts:
            summary = "I haven't lived enough yet to see patterns."
        else:
            summary = " ".join(parts)

        conn = database.get_connection()
        c = conn.cursor()
        c.execute("""
            INSERT INTO long_term_reflections (timestamp, summary)
            VALUES (?, ?)
        """, (datetime.now().isoformat(timespec="seconds"), summary))
        conn.commit()
        conn.close()
        print(f"🌌 Long-term reflection: {summary}")
        return summary

    def recent(self, limit=None):
        conn = database.get_connection()
        c = conn.cursor()
        if limit:
            c.execute("SELECT timestamp, summary FROM long_term_reflections ORDER BY id DESC LIMIT ?", (limit,))
        else:
            c.execute("SELECT timestamp, summary FROM long_term_reflections ORDER BY id DESC")
        rows = c.fetchall()
        conn.close()
        return rows

    def count(self):
        conn = database.get_connection()
        c = conn.cursor()
        c.execute("SELECT COUNT(*) FROM long_term_reflections")
        n = c.fetchone()[0]
        conn.close()
        return n

    def wipe(self):
        conn = database.get_connection()
        c = conn.cursor()
        c.execute("DELETE FROM long_term_reflections")
        conn.commit()
        conn.close()
