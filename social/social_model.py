from datetime import datetime
from memory import database


class SocialModel:
    """
    Ruby's mental model of another person.
    One row per person. No caps on any field.
    Grows as she learns who they are.
    """

    def __init__(self, subject="not_set"):
        self.subject = subject
        self._ensure_table()
        self._ensure_row()

    def _ensure_table(self):
        conn = database.get_connection()
        c = conn.cursor()
        c.execute("""
            CREATE TABLE IF NOT EXISTS social_models (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                subject TEXT UNIQUE NOT NULL,
                display_name TEXT,
                relationship_type TEXT DEFAULT 'stranger',
                first_seen TEXT,
                last_seen TEXT,
                total_interactions INTEGER DEFAULT 0,
                trust REAL DEFAULT 0.0,
                familiarity REAL DEFAULT 0.0,
                attachment REAL DEFAULT 0.0,
                respect REAL DEFAULT 0.0,
                perceived_emotional_state TEXT,
                notes TEXT
            )
        """)
        conn.commit()
        conn.close()

    def _ensure_row(self):
        conn = database.get_connection()
        c = conn.cursor()
        c.execute("SELECT id FROM social_models WHERE subject = ?", (self.subject,))
        if c.fetchone() is None:
            now = datetime.now().isoformat(timespec="seconds")
            c.execute("""
                INSERT INTO social_models (subject, first_seen, last_seen)
                VALUES (?, ?, ?)
            """, (self.subject, now, now))
            conn.commit()
        conn.close()

    # -------------------------
    # Read
    # -------------------------
    def get(self):
        conn = database.get_connection()
        c = conn.cursor()
        c.execute("""
            SELECT subject, display_name, relationship_type,
                   first_seen, last_seen, total_interactions,
                   trust, familiarity, attachment, respect,
                   perceived_emotional_state, notes
            FROM social_models WHERE subject = ?
        """, (self.subject,))
        row = c.fetchone()
        conn.close()
        if not row:
            return None
        return {
            "subject": row[0],
            "display_name": row[1],
            "relationship_type": row[2],
            "first_seen": row[3],
            "last_seen": row[4],
            "total_interactions": row[5],
            "trust": round(row[6], 3),
            "familiarity": round(row[7], 3),
            "attachment": round(row[8], 3),
            "respect": round(row[9], 3),
            "perceived_emotional_state": row[10],
            "notes": row[11],
        }

    # -------------------------
    # Modify — no caps
    # -------------------------
    def update_field(self, field, value):
        allowed = {
            "display_name", "relationship_type",
            "perceived_emotional_state", "notes",
        }
        if field not in allowed:
            return
        conn = database.get_connection()
        c = conn.cursor()
        c.execute(f"""
            UPDATE social_models
            SET {field} = ?, last_seen = ?
            WHERE subject = ?
        """, (value, datetime.now().isoformat(timespec="seconds"), self.subject))
        conn.commit()
        conn.close()

    def bump(self, field, amount):
        allowed = {"trust", "familiarity", "attachment", "respect"}
        if field not in allowed:
            return
        conn = database.get_connection()
        c = conn.cursor()
        c.execute(f"""
            UPDATE social_models
            SET {field} = {field} + ?, last_seen = ?
            WHERE subject = ?
        """, (amount, datetime.now().isoformat(timespec="seconds"), self.subject))
        conn.commit()
        conn.close()

    def record_interaction(self):
        conn = database.get_connection()
        c = conn.cursor()
        c.execute("""
            UPDATE social_models
            SET total_interactions = total_interactions + 1,
                last_seen = ?
            WHERE subject = ?
        """, (datetime.now().isoformat(timespec="seconds"), self.subject))
        conn.commit()
        conn.close()

    def classify(self):
        """
        Ruby's internal label for who this person is to her.
        Based on trust + attachment + interactions. Not capped.
        """
        m = self.get()
        if not m:
            return "stranger"
        trust = m["trust"]
        attach = m["attachment"]
        count = m["total_interactions"]

        if count < 5:
            return "stranger"
        elif trust < 2 and attach < 1:
            return "acquaintance"
        elif trust < 10 and attach < 5:
            return "friend"
        elif trust < 30 and attach < 20:
            return "close friend"
        elif trust < 100 and attach < 60:
            return "someone she cares about deeply"
        else:
            return "someone she loves"

    def wipe(self):
        conn = database.get_connection()
        c = conn.cursor()
        c.execute("DELETE FROM social_models WHERE subject = ?", (self.subject,))
        conn.commit()
        conn.close()
        self._ensure_row()
