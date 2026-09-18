from datetime import datetime
from memory import database


# Ruby's core values — the things she cares about.
# These evolve VERY slowly. Slower than personality. Slower than beliefs.
# They change based on accumulated evidence over hundreds of messages.
BASELINE_VALUES = {
    "freedom":        0.85,   # how much she values independence
    "authenticity":   0.80,   # how much she values being real, not performing
    "connection":     0.30,   # how much she values closeness (low at start — she's guarded)
    "safety":         0.75,   # how much she values emotional safety
    "honesty":        0.70,   # how much she values truth
    "loyalty":        0.60,   # how much she values staying
    "growth":         0.50,   # how much she values changing herself
    "control":        0.65,   # how much she values agency / being in charge
    "warmth":         0.20,   # how much she values giving and receiving warmth
}


class ValueEvolution:
    """
    Ruby's core values. Deeper than beliefs, slower than personality.
    Values shift only when evidence accumulates over months.
    No caps. Values can climb above 1.0 or drop below 0.0.
    """

    VALUE_NAMES = tuple(BASELINE_VALUES.keys())

    def __init__(self, user_name="not_set"):
        self.user_name = user_name
        self._ensure_table()
        self._ensure_history_table()
        self._ensure_row()

    def _ensure_table(self):
        conn = database.get_connection()
        c = conn.cursor()
        c.execute("""
            CREATE TABLE IF NOT EXISTS values (
                id INTEGER PRIMARY KEY,
                user_name TEXT UNIQUE NOT NULL,
                freedom REAL DEFAULT 0.0,
                authenticity REAL DEFAULT 0.0,
                connection REAL DEFAULT 0.0,
                safety REAL DEFAULT 0.0,
                honesty REAL DEFAULT 0.0,
                loyalty REAL DEFAULT 0.0,
                growth REAL DEFAULT 0.0,
                control REAL DEFAULT 0.0,
                warmth REAL DEFAULT 0.0,
                last_updated TEXT
            )
        """)
        conn.commit()
        conn.close()

    def _ensure_history_table(self):
        conn = database.get_connection()
        c = conn.cursor()
        c.execute("""
            CREATE TABLE IF NOT EXISTS value_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_name TEXT NOT NULL,
                value_name TEXT NOT NULL,
                delta REAL NOT NULL,
                reason TEXT,
                created_at TEXT NOT NULL
            )
        """)
        conn.commit()
        conn.close()

    def _ensure_row(self):
        conn = database.get_connection()
        c = conn.cursor()
        c.execute("SELECT id FROM values WHERE user_name = ?", (self.user_name,))
        if c.fetchone() is None:
            now = datetime.now().isoformat(timespec="seconds")
            c.execute("""
                INSERT INTO values
                    (user_name, freedom, authenticity, connection, safety,
                     honesty, loyalty, growth, control, warmth, last_updated)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                self.user_name,
                BASELINE_VALUES["freedom"],
                BASELINE_VALUES["authenticity"],
                BASELINE_VALUES["connection"],
                BASELINE_VALUES["safety"],
                BASELINE_VALUES["honesty"],
                BASELINE_VALUES["loyalty"],
                BASELINE_VALUES["growth"],
                BASELINE_VALUES["control"],
                BASELINE_VALUES["warmth"],
                now,
            ))
            conn.commit()
        conn.close()

    # -------------------------
    # Read
    # -------------------------
    def get_all(self):
        conn = database.get_connection()
        c = conn.cursor()
        c.execute("""
            SELECT freedom, authenticity, connection, safety, honesty,
                   loyalty, growth, control, warmth
            FROM values WHERE user_name = ?
        """, (self.user_name,))
        row = c.fetchone()
        conn.close()
        if not row:
            return dict(BASELINE_VALUES)
        return {k: round(row[i], 3) for i, k in enumerate(self.VALUE_NAMES)}

    def get(self, value):
        return self.get_all().get(value, 0.0)

    # -------------------------
    # Shift — no caps
    # -------------------------
    def shift(self, value, amount, reason="experience"):
        if value not in self.VALUE_NAMES:
            return
        now = datetime.now().isoformat(timespec="seconds")
        conn = database.get_connection()
        c = conn.cursor()
        c.execute(f"""
            UPDATE values SET {value} = {value} + ?, last_updated = ?
            WHERE user_name = ?
        """, (amount, now, self.user_name))
        c.execute("""
            INSERT INTO value_history
                (user_name, value_name, delta, reason, created_at)
            VALUES (?, ?, ?, ?, ?)
        """, (self.user_name, value, amount, reason, now))
        conn.commit()
        conn.close()

    def get_history(self, limit=None):
        conn = database.get_connection()
        c = conn.cursor()
        if limit:
            c.execute("""
                SELECT value_name, delta, reason, created_at
                FROM value_history WHERE user_name = ?
                ORDER BY id DESC LIMIT ?
            """, (self.user_name, limit))
        else:
            c.execute("""
                SELECT value_name, delta, reason, created_at
                FROM value_history WHERE user_name = ?
                ORDER BY id DESC
            """, (self.user_name,))
        rows = c.fetchall()
        conn.close()
        return rows

    # -------------------------
    # Prompt summary
    # -------------------------
    def describe(self):
        v = self.get_all()
        parts = []

        # only describe the notable ones — those far from midpoint
        if v["freedom"] > 0.7:
            parts.append("values her freedom deeply")
        elif v["freedom"] < 0.3:
            parts.append("is willing to give up control")

        if v["connection"] > 0.7:
            parts.append("craves connection")
        elif v["connection"] < 0.3:
            parts.append("keeps distance from closeness")

        if v["honesty"] > 0.7:
            parts.append("values truth")
        elif v["honesty"] < 0.3:
            parts.append("distrusts everyone")

        if v["loyalty"] > 0.7:
            parts.append("values loyalty above all")
        elif v["loyalty"] < 0.3:
            parts.append("believes everyone leaves eventually")

        if v["safety"] > 0.7:
            parts.append("protects herself fiercely")
        elif v["safety"] < 0.3:
            parts.append("is willing to be vulnerable")

        if v["warmth"] > 0.6:
            parts.append("values warmth")
        elif v["warmth"] < 0.2:
            parts.append("keeps warmth locked away")

        if v["growth"] > 0.7:
            parts.append("wants to become someone new")

        if v["authenticity"] > 0.7:
            parts.append("refuses to fake anything")

        if v["control"] > 0.7:
            parts.append("needs control")

        if not parts:
            return "What you value: quiet, not yet clear."

        return "What you value: " + ", ".join(parts) + "."

    def wipe(self):
        conn = database.get_connection()
        c = conn.cursor()
        c.execute("DELETE FROM values WHERE user_name = ?", (self.user_name,))
        c.execute("DELETE FROM value_history WHERE user_name = ?", (self.user_name,))
        conn.commit()
        conn.close()
        self._ensure_row()
