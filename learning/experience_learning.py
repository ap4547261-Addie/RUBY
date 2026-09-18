from datetime import datetime
from memory import database


class ExperienceLearning:
    """
    Tracks what Ruby predicted vs what actually happened.
    Prediction error is the core teacher — she learns by being wrong.
    No caps. Every prediction is stored forever.
    """

    def __init__(self, user_name="not_set"):
        self.user_name = user_name
        self._ensure_tables()

    def _ensure_tables(self):
        conn = database.get_connection()
        c = conn.cursor()

        # Outstanding prediction awaiting outcome
        c.execute("""
            CREATE TABLE IF NOT EXISTS pending_prediction (
                id INTEGER PRIMARY KEY,
                user_name TEXT UNIQUE NOT NULL,
                predicted TEXT,
                ready_for TEXT,
                wary_of TEXT,
                intent TEXT,
                tone TEXT,
                user_message TEXT,
                ruby_reply TEXT,
                timestamp TEXT
            )
        """)

        # Log of prediction vs reality
        c.execute("""
            CREATE TABLE IF NOT EXISTS prediction_errors (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_name TEXT NOT NULL,
                predicted TEXT,
                actual TEXT,
                error_magnitude REAL,
                direction TEXT,
                context TEXT,
                timestamp TEXT
            )
        """)

        conn.commit()
        conn.close()

    # -------------------------
    # Store the prediction BEFORE replying
    # -------------------------
    def store_prediction(self, trace: dict, user_message: str):
        """Called right before generating a reply."""
        prediction = trace.get("prediction", {})
        decision = trace.get("decision", {})

        conn = database.get_connection()
        c = conn.cursor()
        c.execute("""
            INSERT OR REPLACE INTO pending_prediction
                (user_name, predicted, ready_for, wary_of, intent, tone,
                 user_message, ruby_reply, timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            self.user_name,
            prediction.get("likely_next", ""),
            prediction.get("ready_for", ""),
            prediction.get("wary_of", ""),
            decision.get("intent", ""),
            decision.get("tone", ""),
            user_message,
            "",  # reply filled later
            datetime.now().isoformat(timespec="seconds"),
        ))
        conn.commit()
        conn.close()

    def store_reply(self, reply: str):
        """Called right after generating a reply — attach it to the pending row."""
        conn = database.get_connection()
        c = conn.cursor()
        c.execute("""
            UPDATE pending_prediction
            SET ruby_reply = ?
            WHERE user_name = ?
        """, (reply, self.user_name))
        conn.commit()
        conn.close()

    # -------------------------
    # On the NEXT message: evaluate the prediction
    # -------------------------
    def evaluate_last(self, user_message: str):
        """
        Called at the START of each new message.
        Compares the previous prediction against the actual next message.
        Records the error if any.
        """
        conn = database.get_connection()
        c = conn.cursor()
        c.execute("""
            SELECT predicted, ready_for, wary_of, intent, tone, user_message, ruby_reply
            FROM pending_prediction
            WHERE user_name = ?
        """, (self.user_name,))
        row = c.fetchone()
        conn.close()

        if not row:
            return None

        predicted_next = row[0] or ""
        wary_of = row[2] or ""
        prev_reply = row[6] or ""

        # Interpret the actual next message
        actual = self._classify_outcome(user_message)

        # Was the prediction right?
        error = self._compare(predicted_next, actual, wary_of, user_message)

        if error:
            conn = database.get_connection()
            c = conn.cursor()
            c.execute("""
                INSERT INTO prediction_errors
                    (user_name, predicted, actual, error_magnitude, direction, context, timestamp)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                self.user_name,
                predicted_next,
                actual.get("label", "unknown"),
                error.get("magnitude", 0),
                error.get("direction", "none"),
                user_message[:200],
                datetime.now().isoformat(timespec="seconds"),
            ))
            conn.commit()
            conn.close()
            print(f"📚 Prediction error: {error['direction']} (magnitude {round(error['magnitude'], 2)})")

        return error

    # -------------------------
    # Classify what actually happened
    # -------------------------
    def _classify_outcome(self, user_message: str) -> dict:
        text = user_message.lower().strip()

        # positive / warm
        if any(w in text for w in ["love", "miss you", "care", "sorry", "thank"]):
            return {"label": "warm", "valence": +1}
        # patient / persistent
        if any(w in text for w in ["still here", "waiting", "i'll stay", "not leaving"]):
            return {"label": "patient", "valence": +1}
        # curious / engaging
        if "?" in user_message and len(user_message.split()) > 3:
            return {"label": "engaged", "valence": +1}
        # pushing / demanding
        if any(w in text for w in ["do this", "you must", "obey", "send me"]):
            return {"label": "pushy", "valence": -1}
        # rude
        if any(w in text for w in ["stupid", "dumb", "idiot", "shut up"]):
            return {"label": "hostile", "valence": -1}
        # silence / low effort
        if text in ["ok", "k", ".", "...", "lol"]:
            return {"label": "dismissive", "valence": -1}
        # default
        return {"label": "neutral", "valence": 0}

    # -------------------------
    # Compare prediction to reality
    # -------------------------
    def _compare(self, predicted: str, actual: dict, wary_of: str, user_message: str) -> dict:
        """
        Return {magnitude: float, direction: str} or None if nothing notable.
        """
        text = user_message.lower()
        pred_lower = predicted.lower()
        wary_lower = wary_of.lower()

        # Did her fear come true?
        fear_came_true = False
        if "push" in wary_lower or "push" in pred_lower:
            if actual["label"] == "pushy":
                fear_came_true = True
        if "leave" in wary_lower or "leave" in pred_lower:
            if any(w in text for w in ["goodbye", "leaving", "bye"]):
                fear_came_true = True
        if "hurt" in wary_lower or "hurt" in pred_lower:
            if actual["label"] == "hostile":
                fear_came_true = True

        # Did something better than expected happen?
        if actual["valence"] > 0 and ("negative" in pred_lower or actual["label"] in ("warm", "patient")):
            # She probably expected push or dismissal, but got warmth
            if "push" in pred_lower or "dismiss" in pred_lower or "leave" in pred_lower:
                return {"magnitude": 1.5, "direction": "too_negative"}

        # Did fear come true?
        if fear_came_true:
            return {"magnitude": 1.0, "direction": "confirmed"}

        # Small mismatch
        if actual["valence"] < 0 and pred_lower and "warm" in pred_lower:
            return {"magnitude": 1.0, "direction": "too_positive"}

        return None

    # -------------------------
    # Analysis helpers
    # -------------------------
    def get_errors(self, limit=None):
        conn = database.get_connection()
        c = conn.cursor()
        if limit:
            c.execute("SELECT timestamp, predicted, actual, error_magnitude, direction FROM prediction_errors WHERE user_name = ? ORDER BY id DESC LIMIT ?",
                      (self.user_name, limit))
        else:
            c.execute("SELECT timestamp, predicted, actual, error_magnitude, direction FROM prediction_errors WHERE user_name = ? ORDER BY id DESC",
                      (self.user_name,))
        rows = c.fetchall()
        conn.close()
        return rows

    def error_summary(self):
        """Return counts by direction."""
        conn = database.get_connection()
        c = conn.cursor()
        c.execute("""
            SELECT direction, COUNT(*)
            FROM prediction_errors
            WHERE user_name = ?
            GROUP BY direction
        """, (self.user_name,))
        rows = c.fetchall()
        conn.close()
        return {r[0]: r[1] for r in rows}

    def wipe(self):
        conn = database.get_connection()
        c = conn.cursor()
        c.execute("DELETE FROM pending_prediction WHERE user_name = ?", (self.user_name,))
        c.execute("DELETE FROM prediction_errors WHERE user_name = ?", (self.user_name,))
        conn.commit()
        conn.close()
