from datetime import datetime
from memory import database


class BehaviorLearning:
    """
    Tracks which intents/tones worked well or poorly over time.
    No caps. Every outcome is remembered.
    """

    def __init__(self, user_name="not_set"):
        self.user_name = user_name
        self._ensure_table()

    def _ensure_table(self):
        conn = database.get_connection()
        c = conn.cursor()
        c.execute("""
            CREATE TABLE IF NOT EXISTS behavior_outcomes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_name TEXT NOT NULL,
                intent TEXT NOT NULL,
                tone TEXT NOT NULL,
                outcome_score REAL DEFAULT 0.0,
                times_used INTEGER DEFAULT 1,
                last_used TEXT,
                UNIQUE(user_name, intent, tone)
            )
        """)
        conn.commit()
        conn.close()

    def record_outcome(self, intent: str, tone: str, outcome_direction: str):
        """
        outcome_direction: "good" | "bad" | "neutral"
        Boost or shrink the (intent, tone) pair based on whether it worked.
        """
        delta = {"good": +1.0, "neutral": 0.0, "bad": -1.0}.get(outcome_direction, 0.0)
        if delta == 0.0:
            return

        conn = database.get_connection()
        c = conn.cursor()
        c.execute("""
            INSERT INTO behavior_outcomes
                (user_name, intent, tone, outcome_score, times_used, last_used)
            VALUES (?, ?, ?, ?, 1, ?)
            ON CONFLICT(user_name, intent, tone) DO UPDATE SET
                outcome_score = outcome_score + ?,
                times_used = times_used + 1,
                last_used = excluded.last_used
        """, (
            self.user_name, intent, tone, delta,
            datetime.now().isoformat(timespec="seconds"),
            delta,
        ))
        conn.commit()
        conn.close()

    def best_intents(self, limit=3):
        conn = database.get_connection()
        c = conn.cursor()
        c.execute("""
            SELECT intent, tone, outcome_score, times_used
            FROM behavior_outcomes
            WHERE user_name = ?
            ORDER BY outcome_score DESC
            LIMIT ?
        """, (self.user_name, limit))
        rows = c.fetchall()
        conn.close()
        return rows

    def worst_intents(self, limit=3):
        conn = database.get_connection()
        c = conn.cursor()
        c.execute("""
            SELECT intent, tone, outcome_score, times_used
            FROM behavior_outcomes
            WHERE user_name = ?
            ORDER BY outcome_score ASC
            LIMIT ?
        """, (self.user_name, limit))
        rows = c.fetchall()
        conn.close()
        return rows

    def describe(self):
        best = self.best_intents(2)
        worst = self.worst_intents(2)
        parts = []
        if best:
            parts.append("What works: " + ", ".join(f"{i}/{t}" for i, t, _, _ in best))
        if worst and worst[0][2] < -1:
            parts.append("What doesn't: " + ", ".join(f"{i}/{t}" for i, t, _, _ in worst))
        return ". ".join(parts) + "." if parts else ""

    def wipe(self):
        conn = database.get_connection()
        c = conn.cursor()
        c.execute("DELETE FROM behavior_outcomes WHERE user_name = ?", (self.user_name,))
        conn.commit()
        conn.close()
