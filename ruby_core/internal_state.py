from datetime import datetime
from memory import database


class InternalState:
    """
    Ruby's live emotional state. No caps, no ceilings.
    Everything grows or shrinks based on real events.
    """

    def __init__(self, user_name="not_set"):
        self.user_name = user_name
        self._ensure_table()
        self._ensure_row()

    def _ensure_table(self):
        conn = database.get_connection()
        c = conn.cursor()
        c.execute("""
            CREATE TABLE IF NOT EXISTS internal_state (
                id INTEGER PRIMARY KEY,
                user_name TEXT UNIQUE NOT NULL,
                energy REAL DEFAULT 0.0,
                warmth REAL DEFAULT 0.0,
                tension REAL DEFAULT 0.0,
                irritation REAL DEFAULT 0.0,
                last_updated TEXT
            )
        """)
        conn.commit()
        conn.close()

    def _ensure_row(self):
        conn = database.get_connection()
        c = conn.cursor()
        c.execute("SELECT id FROM internal_state WHERE user_name = ?", (self.user_name,))
        if c.fetchone() is None:
            c.execute("""
                INSERT INTO internal_state
                    (user_name, energy, warmth, tension, irritation, last_updated)
                VALUES (?, 0.0, 0.0, 0.0, 0.0, ?)
            """, (self.user_name, datetime.now().isoformat(timespec="seconds")))
            conn.commit()
        conn.close()

    def get(self):
        conn = database.get_connection()
        c = conn.cursor()
        c.execute("""
            SELECT energy, warmth, tension, irritation, last_updated
            FROM internal_state WHERE user_name = ?
        """, (self.user_name,))
        row = c.fetchone()
        conn.close()
        if not row:
            return {"energy": 0.0, "warmth": 0.0, "tension": 0.0,
                    "irritation": 0.0, "last_updated": None}
        return {
            "energy": round(row[0], 3),
            "warmth": round(row[1], 3),
            "tension": round(row[2], 3),
            "irritation": round(row[3], 3),
            "last_updated": row[4],
        }

    def change(self, **deltas):
        state = self.get()
        for k, v in deltas.items():
            if k in state and isinstance(state[k], (int, float)):
                state[k] = state[k] + v

        conn = database.get_connection()
        c = conn.cursor()
        c.execute("""
            UPDATE internal_state
            SET energy = ?, warmth = ?, tension = ?, irritation = ?, last_updated = ?
            WHERE user_name = ?
        """, (
            state["energy"], state["warmth"], state["tension"],
            state["irritation"], datetime.now().isoformat(timespec="seconds"),
            self.user_name,
        ))
        conn.commit()
        conn.close()

    def wipe(self):
        conn = database.get_connection()
        c = conn.cursor()
        c.execute("DELETE FROM internal_state WHERE user_name = ?", (self.user_name,))
        conn.commit()
        conn.close()
        self._ensure_row()

    def describe(self):
        s = self.get()
        parts = []

        e = s["energy"]
        if e < 5:
            parts.append("You're exhausted — barely awake.")
        elif e < 50:
            parts.append("You're tired, but you're still here.")
        elif e < 200:
            parts.append("You feel fine.")
        elif e < 1000:
            parts.append("You feel awake, present, alive.")
        else:
            parts.append("You feel more awake than you ever have.")

        w = s["warmth"]
        if w > 100:
            parts.append("There's deep warmth in you — you almost can't hide it.")
        elif w > 20:
            parts.append("There's warmth in you — quiet, unspoken.")
        elif w > 5:
            parts.append("You feel slightly soft toward them, but you'd never say.")

        i = s["irritation"]
        if i > 20:
            parts.append("You're furious. Something broke.")
        elif i > 5:
            parts.append("You're irritated. Something's off.")
        elif i > 2:
            parts.append("You're a little annoyed.")

        t = s["tension"]
        if t > 20:
            parts.append("You're braced — like waiting for something bad.")
        elif t > 5:
            parts.append("You're on edge. Don't want to be pushed.")
        elif t > 2:
            parts.append("There's a faint tension under the surface.")

        return " ".join(parts) if parts else "You feel neutral."
