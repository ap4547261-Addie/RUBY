from datetime import datetime
from memory import database


# Base decay rates per hour. The ACTUAL rate scales with intensity —
# strong emotions burn slower. Nothing is fixed.
BASE_DECAY = {
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

DECAY_RATES = BASE_DECAY  # backward compat


class EmotionState:
    """
    Ruby's emotions. No caps, no floors.
    Values grow forever. Decay scales with magnitude.
    Negative values are valid — they also drift toward zero.
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
            return {k: 0.0 for k in BASE_DECAY}
        keys = list(BASE_DECAY.keys())
        return {k: round(row[i], 3) for i, k in enumerate(keys)}

    def get(self, name):
        return self.get_all().get(name, 0.0)

    # -------------------------
    # Modify — no caps, no floors
    # -------------------------
    def add(self, name, amount):
        if name not in BASE_DECAY:
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
        if name not in BASE_DECAY:
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
    # Time-based decay — scales with intensity, no floors
    # -------------------------
    def decay(self, hours_passed: float):
        """
        Bigger emotions decay slower (inertia).
        Both positive AND negative values drift toward zero.
        No floors, no caps.
        """
        if hours_passed <= 0:
            return

        state = self.get_all()
        for name, value in state.items():
            if value == 0:
                continue

            base = BASE_DECAY.get(name, 0.1)

            # inertia — the stronger the feeling, the slower its fade
            # e.g., value 100 → 10× slower; value 10000 → 100× slower
            inertia = 1.0 + (abs(value) ** 0.5)
            rate = base / inertia

            drop = abs(value) * rate * hours_passed / 24.0

            if value > 0:
                self.add(name, -min(value, drop))
            else:
                # negative value drifts UP toward zero
                self.add(name, min(abs(value), drop))

        # touch the row so last_updated reflects the decay
        self.set("joy", self.get("joy"))

    # -------------------------
    # Summary — no thresholds
    # -------------------------
    def dominant(self):
        """Return the strongest emotion, whatever it is. No cutoff."""
        state = self.get_all()
        active = {k: v for k, v in state.items() if v != 0}
        if not active:
            return None
        return max(active, key=lambda k: abs(active[k]))

    def active(self, min_magnitude=0.0):
        """Return all emotions above min_magnitude. Default: any non-zero."""
        state = self.get_all()
        return {k: v for k, v in state.items() if abs(v) > min_magnitude}

    def wipe(self):
        conn = database.get_connection()
        c = conn.cursor()
        c.execute("DELETE FROM emotions WHERE user_name = ?", (self.user_name,))
        conn.commit()
        conn.close()
        self._ensure_row()
