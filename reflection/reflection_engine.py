from memory import database
from reflection.self_reflection import SelfReflection
from reflection.experience_review import ExperienceReview
from reflection.long_term_reflection import LongTermReflection


class ReflectionEngine:
    """
    Reflects on EVERY message. No intervals. No caps.
    The depth of reflection scales with what actually changed.
    """

    def __init__(self, user_name="not_set"):
        self.user_name = user_name
        self.self_reflection = SelfReflection(user_name=user_name)
        self.experience_review = ExperienceReview(user_name=user_name)
        self.long_term_reflection = LongTermReflection(user_name=user_name)

        # Snapshot of the last state we saw — for change detection
        self._last_state = None

    def _changes_since_last(self, internal_state, emotions, beliefs):
        """Return dict of what actually shifted since last reflection."""
        current = {
            "energy": internal_state.get("energy", 0),
            "warmth": internal_state.get("warmth", 0),
            "tension": internal_state.get("tension", 0),
            "irritation": internal_state.get("irritation", 0),
            "emotions": dict(emotions),
            "belief_count": len(beliefs) if beliefs else 0,
        }

        if self._last_state is None:
            self._last_state = current
            return {"first": True}

        changes = {}

        for key in ("energy", "warmth", "tension", "irritation"):
            delta = current[key] - self._last_state.get(key, 0)
            if abs(delta) > 0.001:
                changes[key] = delta

        emo_deltas = {}
        for name, value in current["emotions"].items():
            old = self._last_state.get("emotions", {}).get(name, 0)
            diff = value - old
            if abs(diff) > 0.001:
                emo_deltas[name] = diff
        if emo_deltas:
            changes["emotions"] = emo_deltas

        if current["belief_count"] != self._last_state.get("belief_count", 0):
            changes["beliefs_changed"] = current["belief_count"]

        self._last_state = current
        return changes

    def process(self, internal_state, emotions, beliefs, message_count):
        """
        Called after every message. Always reflects.
        Depth scales with what changed.
        """
        changes = self._changes_since_last(internal_state, emotions, beliefs)

        # ----- ALWAYS: self-reflection, every message -----
        try:
            self.self_reflection.reflect(internal_state, emotions, beliefs)
        except Exception as e:
            print(f"⚠️ self_reflection failed: {e}")

        # ----- Experience review: whenever emotions shifted -----
        if "emotions" in changes and changes["emotions"]:
            try:
                self.experience_review.review(hours=1)
            except Exception as e:
                print(f"⚠️ experience_review failed: {e}")

        # ----- Long-term reflection: whenever identity shifted -----
        if "beliefs_changed" in changes:
            try:
                self.long_term_reflection.reflect()
            except Exception as e:
                print(f"⚠️ long_term_reflection failed: {e}")

        # ----- Deep reflection: whenever internal state moved a lot -----
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
