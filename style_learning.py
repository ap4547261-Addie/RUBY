# learning/style_learning.py
# Ruby learns her own style — jokes, flirts, tease, warmth, distance.
# Not by being corrected. By noticing what landed.

import re
from datetime import datetime
from memory import database


class StyleLearning:
    """
    Tracks Ruby's stylistic moves and how the user reacted.

    Moves are things like:
        joke, flirt, tease, warmth, coldness, question, revelation, boundary

    Reactions are scored -2 to +2:
        -2  user shut down, pulled away
        -1  user replied short or cold
         0  neutral
        +1  user engaged, replied longer
        +2  user laughed, flirted back, said something warm
    """

    MOVES = [
        "joke", "flirt", "tease", "warmth",
        "coldness", "question", "revelation", "boundary",
    ]

    def __init__(self, user_name="not_set"):
        self.user_name = user_name
        self._ensure_tables()

    def _ensure_tables(self):
        conn = database.get_connection()
        c = conn.cursor()

        # Every move Ruby made and how it landed
        c.execute("""
            CREATE TABLE IF NOT EXISTS style_moves (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_name TEXT NOT NULL,
                move TEXT NOT NULL,
                context_mood TEXT,
                topic TEXT,
                ruby_reply TEXT,
                reaction_score REAL,
                user_reaction TEXT,
                timestamp TEXT
            )
        """)

        # Aggregate: which moves work best, per mood
        c.execute("""
            CREATE TABLE IF NOT EXISTS style_stats (
                user_name TEXT NOT NULL,
                move TEXT NOT NULL,
                context_mood TEXT,
                total_score REAL DEFAULT 0,
                attempts INTEGER DEFAULT 0,
                last_updated TEXT,
                PRIMARY KEY (user_name, move, context_mood)
            )
        """)

        conn.commit()
        conn.close()

    # ============================================================
    # DETECT WHAT RUBY JUST DID
    # ============================================================

    def detect_move(self, reply: str) -> str:
        """Classify Ruby's reply into a stylistic move."""
        t = reply.lower().strip()

        # Playful insult / dry tease
        if any(w in t for w in ["idiot", "dummy", "you're impossible",
                                 "ridiculous", "oh shut up"]):
            return "tease"

        # Flirtation / romantic hint
        if any(w in t for w in ["handsome", "cute", "you're kind of",
                                 "don't make me", "careful now"]):
            return "flirt"

        # Direct humor / joke
        if any(w in t for w in ["haha", "lol", "😂", "joke",
                                 "kidding", "just kidding"]):
            return "joke"
        if t.endswith("😏") or t.endswith("🙃"):
            return "joke"

        # Warmth — softness, care
        if any(w in t for w in ["i care", "i'm here", "you matter",
                                 "i'm glad", "i like"]):
            return "warmth"

        # Coldness / distance
        if any(w in t for w in ["doesn't matter", "whatever",
                                 "not my problem", "fine"]):
            return "coldness"

        # Boundary
        if any(w in t for w in ["don't ask", "not talking about",
                                 "drop it", "that's enough"]):
            return "boundary"

        # Revelation — revealing something about herself
        if any(w in t for w in ["i remember", "when i was",
                                 "i used to", "i never told"]):
            return "revelation"

        # Default: question
        if "?" in reply:
            return "question"

        return "none"

    # ============================================================
    # SCORE HOW THE USER REACTED
    # ============================================================

    def score_reaction(self, user_message: str) -> tuple:
        """Return (score, label)."""
        t = user_message.lower().strip()
        words = t.split()

        # Laughter / loved it
        if any(w in t for w in ["lol", "lmao", "haha", "hehe", "😂", "🤣"]):
            return +2.0, "laughed"

        # Flirt back
        if any(w in t for w in ["you too", "same", "blushing", "😏", "🥰"]):
            return +2.0, "flirted_back"

        # Warm engagement
        if any(w in t for w in ["thank you", "love that", "that's sweet",
                                 "i like that", "aww"]):
            return +2.0, "warm_response"

        # Cold / pulled away
        if any(w in t for w in ["stop", "don't", "creep", "weird",
                                 "not funny", "whatever"]):
            return -2.0, "rejected"

        # Silence / dismissal
        if t in ("ok", "k", ".", "...", "lol.", "sure", "yeah"):
            return -1.0, "dismissed"

        # Long engaged reply
        if len(words) > 15:
            return +1.0, "engaged"

        # Question back
        if "?" in t and len(words) > 3:
            return +1.0, "curious"

        return 0.0, "neutral"

    # ============================================================
    # STORE THE MOVE + REACTION
    # ============================================================

    def observe(self, context_mood: str, topic: str,
                ruby_reply: str, next_user_message: str):
        """Called when the user replies — evaluates Ruby's previous move."""
        move = self.detect_move(ruby_reply)
        if move == "none":
            return

        score, label = self.score_reaction(next_user_message)

        conn = database.get_connection()
        c = conn.cursor()

        c.execute("""
            INSERT INTO style_moves
                (user_name, move, context_mood, topic, ruby_reply,
                 reaction_score, user_reaction, timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            self.user_name, move, context_mood or "neutral",
            topic or "", ruby_reply[:300], score, label,
            datetime.now().isoformat(timespec="seconds"),
        ))

        # Update aggregate stats
        c.execute("""
            INSERT INTO style_stats
                (user_name, move, context_mood, total_score, attempts, last_updated)
            VALUES (?, ?, ?, ?, 1, ?)
            ON CONFLICT(user_name, move, context_mood) DO UPDATE SET
                total_score = total_score + excluded.total_score,
                attempts = attempts + 1,
                last_updated = excluded.last_updated
        """, (
            self.user_name, move, context_mood or "neutral",
            score, datetime.now().isoformat(timespec="seconds"),
        ))

        conn.commit()
        conn.close()
        print(f"🎭 style move: {move} in [{context_mood}] → {label} ({score:+.1f})")

    # ============================================================
    # QUERY: WHAT WORKS IN THIS MOOD?
    # ============================================================

    def best_moves(self, context_mood: str, limit: int = 3) -> list:
        """Which stylistic moves score highest in this mood?"""
        conn = database.get_connection()
        c = conn.cursor()
        c.execute("""
            SELECT move, total_score, attempts,
                   total_score / MAX(attempts, 1) AS avg_score
            FROM style_stats
            WHERE user_name = ?
              AND context_mood = ?
              AND attempts >= 2
            ORDER BY avg_score DESC
            LIMIT ?
        """, (self.user_name, context_mood, limit))
        rows = c.fetchall()
        conn.close()
        return [
            {"move": r[0], "total": r[1], "attempts": r[2],
             "avg": round(r[3], 2)}
            for r in rows
        ]

    def worst_moves(self, context_mood: str, limit: int = 3) -> list:
        conn = database.get_connection()
        c = conn.cursor()
        c.execute("""
            SELECT move, total_score, attempts,
                   total_score / MAX(attempts, 1) AS avg_score
            FROM style_stats
            WHERE user_name = ?
              AND context_mood = ?
              AND attempts >= 2
            ORDER BY avg_score ASC
            LIMIT ?
        """, (self.user_name, context_mood, limit))
        rows = c.fetchall()
        conn.close()
        return [
            {"move": r[0], "total": r[1], "attempts": r[2],
             "avg": round(r[3], 2)}
            for r in rows
        ]

    def recent_landed(self, move: str, limit: int = 5) -> list:
        """Retrieve recent times this move landed well — for prompt examples."""
        conn = database.get_connection()
        c = conn.cursor()
        c.execute("""
            SELECT ruby_reply, user_reaction, reaction_score
            FROM style_moves
            WHERE user_name = ?
              AND move = ?
              AND reaction_score >= 1.0
            ORDER BY id DESC
            LIMIT ?
        """, (self.user_name, move, limit))
        rows = c.fetchall()
        conn.close()
        return [
            {"said": r[0], "reaction": r[1], "score": r[2]}
            for r in rows
        ]

    def describe(self, context_mood: str = "neutral") -> str:
        """Short prompt-ready summary of what works right now."""
        best = self.best_moves(context_mood, 3)
        if not best:
            return ""

        lines = [f"When the mood is {context_mood}:"]
        for m in best:
            lines.append(f"- {m['move']} works (avg {m['avg']:+.1f}, n={m['attempts']})")

        worst = self.worst_moves(context_mood, 2)
        if worst:
            lines.append("Avoid:")
            for m in worst:
                lines.append(f"- {m['move']} (avg {m['avg']:+.1f})")

        return "\n".join(lines)

    def wipe(self):
        conn = database.get_connection()
        c = conn.cursor()
        c.execute("DELETE FROM style_moves WHERE user_name = ?", (self.user_name,))
        c.execute("DELETE FROM style_stats WHERE user_name = ?", (self.user_name,))
        conn.commit()
        conn.close()
