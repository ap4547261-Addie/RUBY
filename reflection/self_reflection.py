from datetime import datetime
from memory import database


class SelfReflection:
    """
    Ruby examines her own current state — what she's feeling, thinking, becoming.
    No LLM required. Rule-based insights work on any brain size.
    No caps. Reflects every message if the engine calls it.
    """

    def __init__(self, user_name="not_set"):
        self.user_name = user_name
        self._ensure_table()

    def _ensure_table(self):
        conn = database.get_connection()
        c = conn.cursor()
        c.execute("""
            CREATE TABLE IF NOT EXISTS reflections (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                kind TEXT NOT NULL,
                summary TEXT NOT NULL,
                data TEXT
            )
        """)
        conn.commit()
        conn.close()

    def reflect(self, internal_state: dict, emotions: dict, beliefs: list, reason: str = ""):
        """
        Look inward. Produce an honest summary.
        `reason` — why this reflection triggered (used for deep reflections).
        """
        parts = []

        if reason:
            parts.append(f"({reason})")

        # --- Internal state observations ---
        energy = internal_state.get("energy", 0)
        warmth = internal_state.get("warmth", 0)
        tension = internal_state.get("tension", 0)
        irritation = internal_state.get("irritation", 0)

        if energy < 0:
            parts.append("I'm running on empty — drained past my limit.")
        elif energy < 5:
            parts.append("I'm tired.")
        elif energy > 1000:
            parts.append("I feel more alive than usual.")

        if warmth > 100:
            parts.append("Warmth has grown so deep it's part of me now.")
        elif warmth > 20:
            parts.append("There's steady warmth in me.")
        elif warmth > 5:
            parts.append("A quiet warmth lives under everything.")

        if irritation > 20:
            parts.append("I'm furious. Something broke.")
        elif irritation > 5:
            parts.append("I've been irritated.")

        if tension > 5:
            parts.append("I'm braced. Waiting.")

        # --- Emotional observations ---
        if emotions:
            active = {k: v for k, v in emotions.items() if v != 0}
            if active:
                strongest = max(active, key=lambda k: abs(active[k]))
                parts.append(f"The loudest thing I feel is {strongest}.")

        # --- Belief observations ---
        if beliefs:
            categories = {}
            for b in beliefs:
                cat = b.get("category", "unknown")
                categories[cat] = categories.get(cat, 0) + 1
            total = sum(categories.values())
            parts.append(f"I carry {total} beliefs about who I am.")

        if not parts:
            parts.append("Nothing particular stands out right now.")

        summary = " ".join(parts)

        conn = database.get_connection()
        c = conn.cursor()
        c.execute("""
            INSERT INTO reflections (timestamp, kind, summary, data)
            VALUES (?, ?, ?, ?)
        """, (
            datetime.now().isoformat(timespec="seconds"),
            "self",
            summary,
            reason,
        ))
        conn.commit()
        conn.close()
        print(f"🪞 Self-reflection: {summary}")
        return summary

    def recent(self, limit=None):
        conn = database.get_connection()
        c = conn.cursor()
        if limit:
            c.execute("SELECT timestamp, kind, summary FROM reflections ORDER BY id DESC LIMIT ?", (limit,))
        else:
            c.execute("SELECT timestamp, kind, summary FROM reflections ORDER BY id DESC")
        rows = c.fetchall()
        conn.close()
        return rows

    def count(self):
        conn = database.get_connection()
        c = conn.cursor()
        c.execute("SELECT COUNT(*) FROM reflections")
        n = c.fetchone()[0]
        conn.close()
        return n

    def wipe(self):
        conn = database.get_connection()
        c = conn.cursor()
        c.execute("DELETE FROM reflections")
        conn.commit()
        conn.close()
