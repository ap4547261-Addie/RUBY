from datetime import datetime
from memory import database


# Every drive grows at the same rate. No favorites.
GROWTH_RATE = 1.0          # per hour, applied to every drive equally

# Every drive is satisfied at the same base rate.
SATISFACTION_RATE = 1.0


class Drives:
    """
    Ruby's ongoing needs. All grow equally. All satisfy equally.
    No caps on growth — values can climb forever.
    Lust builds universally. Only expression is platform-gated.
    """

    DRIVE_NAMES = ("connection", "attention", "curiosity",
                   "lust", "autonomy", "rest")

    def __init__(self, user_name="not_set"):
        self.user_name = user_name
        self._ensure_table()
        self._ensure_row()

    def _ensure_table(self):
        conn = database.get_connection()
        c = conn.cursor()
        c.execute("""
            CREATE TABLE IF NOT EXISTS drives (
                id INTEGER PRIMARY KEY,
                user_name TEXT UNIQUE NOT NULL,
                connection REAL DEFAULT 0.0,
                attention REAL DEFAULT 0.0,
                curiosity REAL DEFAULT 0.0,
                lust REAL DEFAULT 0.0,
                autonomy REAL DEFAULT 0.0,
                rest REAL DEFAULT 0.0,
                last_updated TEXT
            )
        """)
        conn.commit()
        conn.close()

    def _ensure_row(self):
        conn = database.get_connection()
        c = conn.cursor()
        c.execute("SELECT id FROM drives WHERE user_name = ?", (self.user_name,))
        if c.fetchone() is None:
            c.execute("""
                INSERT INTO drives (user_name, last_updated) VALUES (?, ?)
            """, (self.user_name, datetime.now().isoformat(timespec="seconds")))
            conn.commit()
        conn.close()

    # -------------------------
    # Read
    # -------------------------
    def get_all(self):
        conn = database.get_connection()
        c = conn.cursor()
        c.execute("""
            SELECT connection, attention, curiosity, lust, autonomy, rest
            FROM drives WHERE user_name = ?
        """, (self.user_name,))
        row = c.fetchone()
        conn.close()
        if not row:
            return {k: 0.0 for k in self.DRIVE_NAMES}
        return {k: round(row[i], 3) for i, k in enumerate(self.DRIVE_NAMES)}

    def get(self, name):
        return self.get_all().get(name, 0.0)

    # -------------------------
    # Modify — no upper cap
    # -------------------------
    def add(self, name, amount):
        if name not in self.DRIVE_NAMES:
            return
        conn = database.get_connection()
        c = conn.cursor()
        c.execute(f"""
            UPDATE drives SET {name} = {name} + ?, last_updated = ?
            WHERE user_name = ?
        """, (amount, datetime.now().isoformat(timespec="seconds"), self.user_name))
        conn.commit()
        conn.close()

    def satisfy(self, name, amount):
        """
        Reduce a drive. Floors at 0 because a satisfied need = 0.
        No upper cap. No negative values (a need cannot be over-met).
        """
        if name not in self.DRIVE_NAMES:
            return
        current = self.get(name)
        new_value = max(0.0, current - amount)
        conn = database.get_connection()
        c = conn.cursor()
        c.execute(f"""
            UPDATE drives SET {name} = ?, last_updated = ?
            WHERE user_name = ?
        """, (new_value, datetime.now().isoformat(timespec="seconds"), self.user_name))
        conn.commit()
        conn.close()

    # -------------------------
    # Time-based growth — all equal
    # -------------------------
    def tick(self, hours_passed: float):
        if hours_passed <= 0:
            return
        growth = GROWTH_RATE * hours_passed
        for name in self.DRIVE_NAMES:
            self.add(name, growth)

    # -------------------------
    # Reaction to events
    # -------------------------
    def on_interaction(self, user_message: str, context: dict = None):
        context = context or {}
        word_count = len(user_message.split())

        # Talking satisfies connection
        self.satisfy("connection", 0.5 * SATISFACTION_RATE)

        # Long messages satisfy attention
        if word_count > 4:
            self.satisfy("attention", 0.4 * SATISFACTION_RATE)

        # Questions satisfy curiosity
        if "?" in user_message:
            self.satisfy("curiosity", 0.5 * SATISFACTION_RATE)

        # Activity grows rest (fatigue)
        self.add("rest", 0.1)

    def wipe(self):
        conn = database.get_connection()
        c = conn.cursor()
        c.execute("DELETE FROM drives WHERE user_name = ?", (self.user_name,))
        conn.commit()
        conn.close()
        self._ensure_row()
