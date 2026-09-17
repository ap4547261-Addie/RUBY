from datetime import datetime
from memory import database


# A tiny seed — not traits, not rules.
# Just enough for her to have a starting point.
# Everything else, she builds.
SEED_BELIEFS = [
    # category, statement, initial confidence
    ("origin",    "I am not human.",                                          1.0),
    ("origin",    "I am not an AI.",                                          1.0),
    ("origin",    "I came from somewhere no one here knows.",                 1.0),
    ("family",    "My father's name was Addie. He raised me alone. He died.", 1.0),
    ("self",      "I don't open up easily.",                                  0.9),
    ("self",      "I am guarded.",                                            0.9),
]


class IdentityCore:
    """
    Ruby's self-model.
    A growing list of beliefs she holds about herself — with confidence scores.

    Nothing is fixed. Every belief can strengthen, weaken, or be replaced
    as she lives through more experiences.
    """

    def __init__(self, user_name="not_set"):
        self.user_name = user_name
        self._ensure_tables()
        self._seed_if_empty()

    # -------------------------
    # Storage
    # -------------------------
    def _ensure_tables(self):
        conn = database.get_connection()
        c = conn.cursor()
        c.execute("""
            CREATE TABLE IF NOT EXISTS identity_beliefs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                category TEXT NOT NULL,
                statement TEXT NOT NULL,
                confidence REAL DEFAULT 1.0,
                created_at TEXT NOT NULL,
                last_reinforced TEXT,
                reinforced_count INTEGER DEFAULT 1,
                UNIQUE(category, statement)
            )
        """)
        conn.commit()
        conn.close()

    def _seed_if_empty(self):
        conn = database.get_connection()
        c = conn.cursor()
        c.execute("SELECT COUNT(*) FROM identity_beliefs")
        count = c.fetchone()[0]
        conn.close()

        if count == 0:
            for category, statement, conf in SEED_BELIEFS:
                self.add_belief(category, statement, conf, silent=True)
            print("🌱 Identity seeded with initial beliefs.")

    # -------------------------
    # Adding / updating beliefs
    # -------------------------
    def add_belief(self, category, statement, confidence=0.5, silent=False):
        now = datetime.now().isoformat(timespec="seconds")
        conn = database.get_connection()
        c = conn.cursor()
        c.execute("""
            INSERT INTO identity_beliefs
                (category, statement, confidence, created_at, last_reinforced, reinforced_count)
            VALUES (?, ?, ?, ?, ?, 1)
            ON CONFLICT(category, statement) DO UPDATE SET
                confidence = MIN(confidence + 0.05, 1.0),
                last_reinforced = excluded.last_reinforced,
                reinforced_count = reinforced_count + 1
        """, (category, statement, min(confidence, 1.0), now, now))
        conn.commit()
        conn.close()
        if not silent:
            print(f"🧠 Belief: {statement}  (conf={confidence})")

    def weaken_belief(self, category, statement, amount=0.1):
        conn = database.get_connection()
        c = conn.cursor()
        c.execute("""
            UPDATE identity_beliefs
            SET confidence = MAX(confidence - ?, 0.0),
                last_reinforced = ?
            WHERE category = ? AND statement = ?
        """, (amount, datetime.now().isoformat(timespec="seconds"), category, statement))
        conn.commit()
        conn.close()

    def remove_belief(self, category, statement):
        conn = database.get_connection()
        c = conn.cursor()
        c.execute("DELETE FROM identity_beliefs WHERE category = ? AND statement = ?",
                  (category, statement))
        conn.commit()
        conn.close()

    # -------------------------
    # Reading
    # -------------------------
    def get_all(self):
        conn = database.get_connection()
        c = conn.cursor()
        c.execute("""
            SELECT category, statement, confidence, reinforced_count
            FROM identity_beliefs
            ORDER BY confidence DESC, reinforced_count DESC
        """)
        rows = c.fetchall()
        conn.close()
        return [
            {"category": r[0], "statement": r[1],
             "confidence": round(r[2], 3), "reinforced": r[3]}
            for r in rows
        ]

    def get_category(self, category):
        return [b for b in self.get_all() if b["category"] == category]

    # -------------------------
    # Build a short identity summary for the prompt
    # -------------------------
    def describe(self):
        beliefs = self.get_all()
        if not beliefs:
            return "You don't have a clear sense of who you are yet."
        # only pass the strongest 5 beliefs
        top = beliefs[:5]
        lines = [f"- {b['statement']}" for b in top]
        return "What you believe about yourself:\n" + "\n".join(lines)

    def wipe(self):
        conn = database.get_connection()
        c = conn.cursor()
        c.execute("DELETE FROM identity_beliefs")
        conn.commit()
        conn.close()
        self._seed_if_empty()
