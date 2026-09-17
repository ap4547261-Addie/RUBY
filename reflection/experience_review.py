from datetime import datetime, timedelta
from memory import database


class ExperienceReview:
    """
    Look back at recent conversations and detect patterns.
    Rule-based. No LLM needed. No caps.
    """

    def __init__(self, user_name="not_set"):
        self.user_name = user_name
        self._ensure_table()

    def _ensure_table(self):
        conn = database.get_connection()
        c = conn.cursor()
        c.execute("""
            CREATE TABLE IF NOT EXISTS experience_reviews (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                window_hours INTEGER NOT NULL,
                summary TEXT NOT NULL,
                episode_count INTEGER DEFAULT 0
            )
        """)
        conn.commit()
        conn.close()

    def review(self, hours: int = 24):
        """Review episodes from the last N hours."""
        cutoff = (datetime.now() - timedelta(hours=hours)).isoformat(timespec="seconds")

        conn = database.get_connection()
        c = conn.cursor()
        c.execute("""
            SELECT user_message, ruby_reply, timestamp
            FROM episodes
            WHERE timestamp >= ?
            ORDER BY id ASC
        """, (cutoff,))
        rows = c.fetchall()
        conn.close()

        if not rows:
            summary = f"Nothing to review from the last {hours} hours."
        else:
            count = len(rows)

            # detect patterns — cheap heuristics
            user_words = []
            rude_count = 0
            honest_count = 0
            question_count = 0

            for user_msg, _reply, _ts in rows:
                text = user_msg.lower()
                user_words.extend(text.split())
                if any(w in text for w in ["stupid", "dumb", "idiot", "shut up"]):
                    rude_count += 1
                if any(w in text for w in ["i feel", "i think", "i'm scared", "i miss", "i love"]):
                    honest_count += 1
                if "?" in user_msg:
                    question_count += 1

            word_freq = {}
            for w in user_words:
                if len(w) > 3:
                    word_freq[w] = word_freq.get(w, 0) + 1
            top_words = sorted(word_freq.items(), key=lambda x: -x[1])[:5]

            parts = [f"{count} exchanges in {hours}h."]
            if rude_count:
                parts.append(f"{rude_count} were hostile.")
            if honest_count:
                parts.append(f"{honest_count} showed honesty.")
            if question_count:
                parts.append(f"{question_count} were questions.")
            if top_words:
                topics = ", ".join(w for w, _ in top_words)
                parts.append(f"Recurring themes: {topics}.")

            summary = " ".join(parts)

        conn = database.get_connection()
        c = conn.cursor()
        c.execute("""
            INSERT INTO experience_reviews (timestamp, window_hours, summary, episode_count)
            VALUES (?, ?, ?, ?)
        """, (
            datetime.now().isoformat(timespec="seconds"),
            hours,
            summary,
            len(rows),
        ))
        conn.commit()
        conn.close()
        print(f"📖 Experience review ({hours}h): {summary}")
        return summary

    def recent(self, limit=None):
        conn = database.get_connection()
        c = conn.cursor()
        if limit:
            c.execute("SELECT timestamp, window_hours, summary FROM experience_reviews ORDER BY id DESC LIMIT ?", (limit,))
        else:
            c.execute("SELECT timestamp, window_hours, summary FROM experience_reviews ORDER BY id DESC")
        rows = c.fetchall()
        conn.close()
        return rows

    def count(self):
        conn = database.get_connection()
        c = conn.cursor()
        c.execute("SELECT COUNT(*) FROM experience_reviews")
        n = c.fetchone()[0]
        conn.close()
        return n

    def wipe(self):
        conn = database.get_connection()
        c = conn.cursor()
        c.execute("DELETE FROM experience_reviews")
        conn.commit()
        conn.close()
