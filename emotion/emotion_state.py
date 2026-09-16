from datetime import datetime
from memory import database


# Emotion decay rates — how fast each fades per hour
# Love and attachment decay slowly; irritation and anger fast.
DECAY_RATES = {
    "joy":        0.30,
    "warmth":     0.05,
    "love":       0.005,
    "attachment": 0.003,
    "trust":      0.002,
    "irritation": 0.40,
    "anger":      0.25,
    "jealousy":   0.15,
    "sadness":    0.10,
    "loneliness": 0.08,
    "fear":       0.20,
    "curiosity":  0.35,
    "pride":      0.20,
    "guilt":      0.15,
}


class EmotionState:
    """
    Holds Ruby's active emotions as (name → intensity) pairs.
    Values grow without cap. They decay over time.
    Persisted in SQLite so emotions survive restarts.
    """

    def __init__(self, user_name="not_set"):
        self.user_name = user_name
        self._ensure_table()
        self._ensure_row()

    def _ensure_table(self):
        conn = database.get_connection()
        c = conn.cursor()
        c.execute("""
            CREATE TABLE IF NOT EXISTS emotions (
                id INTEGER PRIMARY KEY,
                user_name TEXT UNIQUE NOT NULL,
                joy REAL DEFAULT 0.0,
                warmth REAL DEFAULT 0.0,
                love REAL DEFAULT 0.0,
                attachment REAL DEFAULT 0.0,
                trust REAL DEFAULT 0.0,
                irritation REAL DEFAULT 0.0,
                anger REAL DEFAULT 0.0,
                jealousy REAL DEFAULT 0.0,
                sadness REAL DEFAULT 0.0,
                loneliness REAL DEFAULT 0.0,
                fear REAL DEFAULT 0.0,
                curiosity REAL DEFAULT 0.0,
                pride REAL DEFAULT 0.0,
                guilt REAL DEFAULT 0.0,
                last_updated TEXT
            )
        """)
        conn.commit()
        conn.close()

    def _ensure_row(self):
        conn = database.get_connection()
        c = conn.cursor()
        c.execute("SELECT id FROM emotions WHERE user_name = ?", (self.user_name,))
        if c.fetchone() is None:
            c.execute(
                "INSERT INTO emotions (user_name, last_updated) VALUES (?, ?)",
                (self.user_name, datetime.now().isoformat(timespec="seconds")),
            )
            conn.commit()
        conn.close()

    # -------------------------
    # Read
    # -------------------------
    def get_all(self):
        conn = database.get_connection()
        c = conn.cursor()
        c.execute("""
            SELECT joy, warmth, love, attachment, trust,
                   irritation, anger, jealousy, sadness,
                   loneliness, fear, curiosity, pride, guilt
            FROM emotions WHERE user_name = ?
        """, (self.user_name,))
        row = c.fetchone()
        conn.close()
        if not row:
            return {k: 0.0 for k in DECAY_RATES}
        keys = list(DECAY_RATES.keys())
        return {k: round(row[i], 3) for i, k in enumerate(keys)}

    def get(self, name):
        return self.get_all().get(name, 0.0)

    # -------------------------
    # Modify (no caps)
    # -------------------------
    def add(self, name, amount):
        if name not in DECAY_RATES:
            return
        conn = database.get_connection()
        c = conn.cursor()
        c.execute(f"""
            UPDATE emotions
            SET {name} = {name} + ?, last_updated = ?
            WHERE user_name = ?
        """, (amount, datetime.now().isoformat(timespec="seconds"), self.user_name))
        conn.commit()
        conn.close()

    def add_many(self, deltas: dict):
        for name, amount in deltas.items():
            if amount != 0:
                self.add(name, amount)

    def set(self, name, value):
        if name not in DECAY_RATES:
            return
        conn = database.get_connection()
        c = conn.cursor()
        c.execute(f"""
            UPDATE emotions
            SET {name} = ?, last_updated = ?
            WHERE user_name = ?
        """, (value, datetime.now().isoformat(timespec="seconds"), self.user_name))
        conn.commit()
        conn.close()

    # -------------------------
    # Time-based decay
    # -------------------------
    def decay(self, hours_passed: float):
        if hours_passed <= 0:
            return
        state = self.get_all()
        for name, value in state.items():
            if value <= 0:
                continue
            rate = DECAY_RATES.get(name, 0.1)
            # proportional decay — bigger values decay faster
            drop = value * rate * hours_passed / 24.0
            self.add(name, -min(value, drop))
        # refresh last_updated
        self.set("joy", self.get("joy"))  # touches the row

    # -------------------------
    # Summary
    # -------------------------
    def dominant(self):
        """Return the strongest currently-active emotion."""
        state = self.get_all()
        active = {k: v for k, v in state.items() if v > 0.5}
        if not active:
            return None
        return max(active, key=active.get)

    def wipe(self):
        conn = database.get_connection()
        c = conn.cursor()
        c.execute("DELETE FROM emotions WHERE user_name = ?", (self.user_name,))
        conn.commit()
        conn.close()
        self._ensure_row()
