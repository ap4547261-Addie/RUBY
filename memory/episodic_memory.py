from datetime import datetime, timedelta
from memory import database


class EpisodicMemory:
    """Raw conversations — the timeline of everything that happened."""

    # Memories below this strength have faded: not recalled any more
    # (the row is kept — forgetting is not deleting).
    FADED_BELOW = 0.25

    def remember(self, user_message, ruby_reply, importance=3, emotion="", intensity=0.0):
        """Store an episode. Emotional moments are stored STRONGER, so they are
        easier to recall and survive longer than small talk."""
        intensity = max(0.0, float(intensity or 0.0))
        strength = 1.0 + intensity
        conn = database.get_connection()
        c = conn.cursor()
        c.execute(
            """
            INSERT INTO episodes (user_message, ruby_reply, timestamp, importance,
                                  strength, emotion, intensity)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (user_message, ruby_reply,
             datetime.now().isoformat(timespec="seconds"), importance,
             strength, emotion or "", intensity),
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

    def last_user_timestamp(self):
        """When the USER last wrote (ignores texts Ruby started herself, which
        are stored with an empty user_message). None if they never have."""
        conn = database.get_connection()
        c = conn.cursor()
        c.execute(
            "SELECT timestamp FROM episodes WHERE user_message != '' ORDER BY id DESC LIMIT 1"
        )
        row = c.fetchone()
        conn.close()
        return row[0] if row else None

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

    def search_ranked(self, keyword, limit=1, now=None):
        """Like search(), but ranked the way a mind does it: vivid + emotional +
        recent memories first. Faded memories are skipped. Returns dicts."""
        if not keyword or len(keyword) < 3:
            return []
        now = now or datetime.now()
        conn = database.get_connection()
        c = conn.cursor()
        like = f"%{keyword.lower()}%"
        c.execute(
            """
            SELECT id, user_message, ruby_reply, timestamp, strength, emotion, intensity
            FROM episodes
            WHERE (LOWER(user_message) LIKE ? OR LOWER(ruby_reply) LIKE ?)
              AND COALESCE(strength, 1.0) >= ?
            ORDER BY id DESC LIMIT 40
            """,
            (like, like, self.FADED_BELOW),
        )
        rows = c.fetchall()
        conn.close()
        scored = []
        for rid, u, r, ts, strength, emotion, intensity in rows:
            try:
                age_days = max(0.0, (now - datetime.fromisoformat(ts)).total_seconds() / 86400)
            except Exception:
                age_days = 0.0
            recency = 1.0 / (1.0 + age_days / 30.0)
            scored.append((float(strength or 1.0) * (0.4 + recency), {
                "id": rid, "user_message": u, "ruby_reply": r, "timestamp": ts,
                "strength": float(strength or 1.0), "emotion": emotion or "",
                "intensity": float(intensity or 0.0),
            }))
        scored.sort(key=lambda x: x[0], reverse=True)
        return [d for _s, d in scored[:limit]]

    def recent_emotional(self, within_hours=48, min_intensity=1.0, now=None):
        """The most intense still-vivid moment of the last couple of days (dict) or None."""
        now = now or datetime.now()
        since = (now - timedelta(hours=within_hours)).isoformat(timespec="seconds")
        conn = database.get_connection()
        c = conn.cursor()
        c.execute(
            """
            SELECT id, user_message, ruby_reply, timestamp, emotion, intensity
            FROM episodes
            WHERE user_message != '' AND timestamp >= ? AND intensity >= ?
              AND COALESCE(strength, 1.0) >= ?
            ORDER BY intensity DESC, id DESC LIMIT 1
            """,
            (since, min_intensity, self.FADED_BELOW),
        )
        row = c.fetchone()
        conn.close()
        if not row:
            return None
        return {"id": row[0], "user_message": row[1], "ruby_reply": row[2],
                "timestamp": row[3], "emotion": row[4] or "", "intensity": float(row[5] or 0)}

    def reinforce(self, episode_id, amount=0.1):
        """Remembering something strengthens it a little (and stamps the recall)."""
        conn = database.get_connection()
        c = conn.cursor()
        c.execute(
            "UPDATE episodes SET strength = COALESCE(strength, 1.0) + ?, last_recalled = ? WHERE id = ?",
            (amount, datetime.now().isoformat(timespec="seconds"), episode_id),
        )
        conn.commit()
        conn.close()

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
