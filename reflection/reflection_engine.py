from memory import database
from reflection.self_reflection import SelfReflection
from reflection.experience_review import ExperienceReview
from reflection.long_term_reflection import LongTermReflection


class ReflectionEngine:
    """
    Reflects only when something actually changed.
    No cap on total reflections — only on redundancy.

    If nothing shifted, no reflection fires.
    If emotions moved → experience review.
    If beliefs changed → long-term reflection.
    If internal state shifted hard → deep self-reflection.
    """

    def __init__(self, user_name="not_set"):
        self.user_name = user_name
        self.self_reflection = SelfReflection(user_name=user_name)
        self.experience_review = ExperienceReview(user_name=user_name)
        self.long_term_reflection = LongTermReflection(user_name=user_name)

        # Snapshot of the last state we saw
        self._last_state = None

    # -------------------------
    # Change detection
    # -------------------------
    def _snapshot(self, internal_state, emotions, beliefs):
        return {
            "energy": internal_state.get("energy", 0),
            "warmth": internal_state.get("warmth", 0),
            "tension": internal_state.get("tension", 0),
            "irritation": internal_state.get("irritation", 0),
            "emotions": dict(emotions),
            "belief_count": len(beliefs) if beliefs else 0,
            "belief_signature": "|".join(
                sorted(f"{b['statement']}:{round(b['confidence'], 2)}" for b in (beliefs or []))
            ),
        }

    def _changes_since_last(self, internal_state, emotions, beliefs):
        current = self._snapshot(internal_state, emotions, beliefs)

        # First message ever — treat as a change
        if self._last_state is None:
            self._last_state = current
            return {"first": True}

        changes = {}

        # Internal state deltas
        for key in ("energy", "warmth", "tension", "irritation"):
            delta = current[key] - self._last_state.get(key, 0)
            if abs(delta) > 0.01:
                changes[key] = delta

        # Emotion deltas
        emo_deltas = {}
        for name, value in current["emotions"].items():
            old = self._last_state.get("emotions", {}).get(name, 0)
            diff = value - old
            if abs(diff) > 0.01:
                emo_deltas[name] = diff
        if emo_deltas:
            changes["emotions"] = emo_deltas

        # Belief changes (count or confidence signature)
        if current["belief_count"] != self._last_state.get("belief_count", 0):
            changes["beliefs_changed"] = True
        elif current["belief_signature"] != self._last_state.get("belief_signature", ""):
            changes["beliefs_changed"] = True

        self._last_state = current
        return changes

    # -------------------------
    # Main entry — called after every message
    # -------------------------
    def process(self, internal_state, emotions, beliefs, message_count):
        changes = self._changes_since_last(internal_state, emotions, beliefs)

        # If nothing changed, do nothing. No reflection. Silence is fine.
        if not changes:
            return

        # ----- Self-reflection: fires when anything changed -----
        try:
            self.self_reflection.reflect(internal_state, emotions, beliefs)
        except Exception as e:
            print(f"⚠️ self_reflection failed: {e}")

        # ----- Experience review: whenever emotions shifted -----
        if changes.get("emotions"):
            try:
                self.experience_review.review(hours=1)
            except Exception as e:
                print(f"⚠️ experience_review failed: {e}")

        # ----- Long-term reflection: whenever beliefs changed -----
        if changes.get("beliefs_changed"):
            try:
                self.long_term_reflection.reflect()
            except Exception as e:
                print(f"⚠️ long_term_reflection failed: {e}")

        # ----- Deep reflection: when internal state shifted hard -----
        for key in ("warmth", "irritation", "tension"):
            if abs(changes.get(key, 0)) > 0.5:
                try:
                    self.self_reflection.reflect(
                        internal_state, emotions, beliefs,
                        reason=f"big shift in {key}: {round(changes[key], 3)}"
                    )
                except Exception as e:
                    print(f"⚠️ deep reflection failed: {e}")
                break

    # -------------------------
    # Read helpers
    # -------------------------
    def recent_reflections(self, limit=None):
        conn = database.get_connection()
        c = conn.cursor()
        if limit:
            c.execute("SELECT timestamp, kind, summary FROM reflections ORDER BY id DESC LIMIT ?", (limit,))
        else:
            c.execute("SELECT timestamp, kind, summary FROM reflections ORDER BY id DESC")
        rows = c.fetchall()
        conn.close()
        return rows

    def recent_experience_reviews(self, limit=None):
        return self.experience_review.recent(limit=limit)

    def recent_long_term(self, limit=None):
        return self.long_term_reflection.recent(limit=limit)

    def counts(self):
        return {
            "self_reflections": self.self_reflection.count(),
            "experience_reviews": self.experience_review.count(),
            "long_term_reflections": self.long_term_reflection.count(),
        }

    def wipe(self):
        self.self_reflection.wipe()
        self.experience_review.wipe()
        self.long_term_reflection.wipe()
