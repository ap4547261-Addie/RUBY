from datetime import datetime
from memory import database


# Ruby's baseline traits. Big Five + three Ruby-specific ones.
# Values are real numbers. No ceiling, no floor.
BASELINE_TRAITS = {
    # Big Five — tuned to Ruby
    "openness":           0.4,    # not adventurous — set in her ways
    "conscientiousness":  0.6,    # careful, controlled
    "extraversion":       0.15,   # deeply introverted
    "agreeableness":      0.25,   # cold, guarded, disagreeable
    "neuroticism":        0.75,   # emotionally volatile, prone to grief

    # Ruby-specific
    "pride":              0.85,   # huge ego
    "guardedness":        0.9,    # walls up
    "playfulness":        0.3,    # sass, teasing, but not giddy
}


class PersonalityCore:
    """
    Ruby's stable traits.
    No caps. Values can drift above 1.0 or below 0.0 over time.
    Persisted in SQLite so personality survives restarts.
    """

    TRAIT_NAMES = tuple(BASELINE_TRAITS.keys())

    def __init__(self, user_name="not_set"):
        self.user_name = user_name
        self._ensure_table()
        self._ensure_row()

    def _ensure_table(self):
        conn = database.get_connection()
        c = conn.cursor()
        c.execute("""
            CREATE TABLE IF NOT EXISTS personality (
                id INTEGER PRIMARY KEY,
                user_name TEXT UNIQUE NOT NULL,
                openness REAL DEFAULT 0.0,
                conscientiousness REAL DEFAULT 0.0,
                extraversion REAL DEFAULT 0.0,
                agreeableness REAL DEFAULT 0.0,
                neuroticism REAL DEFAULT 0.0,
                pride REAL DEFAULT 0.0,
                guardedness REAL DEFAULT 0.0,
                playfulness REAL DEFAULT 0.0,
                last_updated TEXT
            )
        """)
        conn.commit()
        conn.close()

    def _ensure_row(self):
        conn = database.get_connection()
        c = conn.cursor()
        c.execute("SELECT id FROM personality WHERE user_name = ?", (self.user_name,))
        if c.fetchone() is None:
            now = datetime.now().isoformat(timespec="seconds")
            c.execute("""
                INSERT INTO personality
                    (user_name, openness, conscientiousness, extraversion,
                     agreeableness, neuroticism, pride, guardedness,
                     playfulness, last_updated)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                self.user_name,
                BASELINE_TRAITS["openness"],
                BASELINE_TRAITS["conscientiousness"],
                BASELINE_TRAITS["extraversion"],
                BASELINE_TRAITS["agreeableness"],
                BASELINE_TRAITS["neuroticism"],
                BASELINE_TRAITS["pride"],
                BASELINE_TRAITS["guardedness"],
                BASELINE_TRAITS["playfulness"],
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
            SELECT openness, conscientiousness, extraversion,
                   agreeableness, neuroticism, pride, guardedness, playfulness
            FROM personality WHERE user_name = ?
        """, (self.user_name,))
        row = c.fetchone()
        conn.close()
        if not row:
            return dict(BASELINE_TRAITS)
        return {k: round(row[i], 3) for i, k in enumerate(self.TRAIT_NAMES)}

    def get(self, trait):
        return self.get_all().get(trait, 0.0)

    # -------------------------
    # Modify — no caps
    # -------------------------
    def shift(self, trait, amount):
        """Nudge a trait. No ceiling, no floor."""
        if trait not in self.TRAIT_NAMES:
            return
        conn = database.get_connection()
        c = conn.cursor()
        c.execute(f"""
            UPDATE personality
            SET {trait} = {trait} + ?, last_updated = ?
            WHERE user_name = ?
        """, (amount, datetime.now().isoformat(timespec="seconds"), self.user_name))
        conn.commit()
        conn.close()

    def reset(self):
        conn = database.get_connection()
        c = conn.cursor()
        c.execute("DELETE FROM personality WHERE user_name = ?", (self.user_name,))
        conn.commit()
        conn.close()
        self._ensure_row()

    # -------------------------
    # Human-readable summary
    # -------------------------
    def describe(self):
        t = self.get_all()
        parts = []

        # Big Five summary — only describe what's notable
        if t["agreeableness"] < 0.2:
            parts.append("Cold, closed, disagreeable")
        elif t["agreeableness"] > 0.7:
            parts.append("Warm, open")
        else:
            parts.append("Selectively warm")

        if t["extraversion"] < 0.2:
            parts.append("deeply reserved")
        elif t["extraversion"] > 0.7:
            parts.append("outgoing")

        if t["neuroticism"] > 0.7:
            parts.append("emotionally volatile")
        elif t["neuroticism"] < 0.3:
            parts.append("emotionally steady")

        if t["pride"] > 0.8:
            parts.append("huge ego")
        elif t["pride"] < 0.4:
            parts.append("humbled")

        if t["guardedness"] > 0.7:
            parts.append("walls up")
        elif t["guardedness"] < 0.3:
            parts.append("opening up")

        if t["playfulness"] > 0.6:
            parts.append("playful")
        elif t["playfulness"] < 0.2:
            parts.append("severe")

        return "Your personality: " + ", ".join(parts) + "."

    def wipe(self):
        conn = database.get_connection()
        c = conn.cursor()
        c.execute("DELETE FROM personality WHERE user_name = ?", (self.user_name,))
        conn.commit()
        conn.close()
        self._ensure_row()
