from datetime import datetime
from memory import database


class PreferenceLearning:
    """
    Learns what Ruby actually likes/dislikes from experience.
    No caps. Preferences accumulate forever.
    """

    def __init__(self, user_name="not_set"):
        self.user_name = user_name
        self._ensure_table()

    def _ensure_table(self):
        conn = database.get_connection()
        c = conn.cursor()
        c.execute("""
            CREATE TABLE IF NOT EXISTS preferences (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_name TEXT NOT NULL,
                topic TEXT NOT NULL,
                feeling REAL DEFAULT 0.0,
                times_seen INTEGER DEFAULT 1,
                last_updated TEXT,
                UNIQUE(user_name, topic)
            )
        """)
        conn.commit()
        conn.close()

    def learn_from(self, user_message: str, emotions: dict):
        """
        When a message triggers strong emotion, associate it with the topics in that message.
        """
        # extract topics (simple — meaningful words)
        words = [w.lower().strip(".,!?") for w in user_message.split()]
        topics = [w for w in words if len(w) > 4]

        if not topics:
            return

        # overall emotional valence
        positive = emotions.get("joy", 0) + emotions.get("warmth", 0) + emotions.get("love", 0) + emotions.get("curiosity", 0)
        negative = emotions.get("anger", 0) + emotions.get("irritation", 0) + emotions.get("sadness", 0) + emotions.get("fear", 0) + emotions.get("jealousy", 0)

        score = positive - negative

        # only update if there was real feeling
        if abs(score) < 0.5:
            return

        for topic in topics:
            self._update_preference(topic, score)

    def _update_preference(self, topic: str, delta: float):
        conn = database.get_connection()
        c = conn.cursor()
        c.execute("""
            INSERT INTO preferences (user_name, topic, feeling, times_seen, last_updated)
            VALUES (?, ?, ?, 1, ?)
            ON CONFLICT(user_name, topic) DO UPDATE SET
                feeling = feeling + ?,
                times_seen = times_seen + 1,
                last_updated = excluded.last_updated
        """, (
            self.user_name, topic, delta,
            datetime.now().isoformat(timespec="seconds"),
            delta,
        ))
        conn.commit()
        conn.close()

    def get_all(self):
        conn = database.get_connection()
        c = conn.cursor()
        c.execute("""
            SELECT topic, feeling, times_seen FROM preferences
            WHERE user_name = ?
            ORDER BY feeling DESC
        """, (self.user_name,))
        rows = c.fetchall()
        conn.close()
        return rows

    def likes(self):
        return [r for r in self.get_all() if r[1] > 1]

    def dislikes(self):
        return [r for r in self.get_all() if r[1] < -1]

    def describe(self):
        likes = self.likes()[:3]
        dislikes = self.dislikes()[:3]
        parts = []
        if likes:
            parts.append("You enjoy: " + ", ".join(t for t, _, _ in likes))
        if dislikes:
            parts.append("You dislike: " + ", ".join(t for t, _, _ in dislikes))
        return ". ".join(parts) + "." if parts else ""

    def wipe(self):
        conn = database.get_connection()
        c = conn.cursor()
        c.execute("DELETE FROM preferences WHERE user_name = ?", (self.user_name,))
        conn.commit()
        conn.close()
