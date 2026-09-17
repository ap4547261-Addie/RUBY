from memory import database
from reflection.self_reflection import SelfReflection
from reflection.experience_review import ExperienceReview
from reflection.long_term_reflection import LongTermReflection


# Ignore tiny drift — only react to meaningful change
STATE_CHANGE_THRESHOLD = 0.5
EMOTION_CHANGE_THRESHOLD = 0.2


class ReflectionEngine:
    """
    Reflects only on meaningful change.
    Ignores the tiny drift that every message causes.
    """

    def __init__(self, user_name="not_set"):
        self.user_name = user_name
        self.self_reflection = SelfReflection(user_name=user_name)
        self.experience_review = ExperienceReview(user_name=user_name)
        self.long_term_reflection = LongTermReflection(user_name=user_name)
        self._last_state = None

    def _snapshot(self, internal_state, emotions, beliefs):
        return {
            "energy": internal_state.get("energy", 0),
            "warmth": internal_state.get("warmth", 0),
            "tension": internal_state.get("tension", 0),
            "irritation": internal_state.get("irritation", 0),
            "emotions": dict(emotions),
            "belief_signature": "|".join(
                sorted(f"{b['statement']}:{round(b['confidence'], 2)}"
                       for b in (beliefs or []))
            ),
        }

    def _changes_since_last(self, internal_state, emotions, beliefs):
        current = self._snapshot(internal_state, emotions, beliefs)

        if self._last_state is None:
            self._last_state = current
            return {"first": True}

        changes = {}

        for key in ("energy", "warmth", "tension", "irritation"):
            delta = current[key] - self._last_state.get(key, 0)
            if abs(delta) > STATE_CHANGE_THRESHOLD:
                changes[key] = delta

        emo_changes = {}
        for name, value in current["emotions"].items():
            old = self._last_state.get("emotions", {}).get(name, 0)
            if abs(value - old) > EMOTION_CHANGE_THRESHOLD:
                emo_changes[name] = value - old
        if emo_changes:
            changes["emotions"] = emo_changes

        if current["belief_signature"] != self._last_state.get("belief_signature", ""):
            changes["beliefs_changed"] = True

        self._last_state = current
        return changes

    def process(self, internal_state, emotions, beliefs, message_count):
        changes = self._changes_since_last(internal_state, emotions, beliefs)

        if changes.get("first"):
            try:
                self.self_reflection.reflect(internal_state, emotions, beliefs)
            except Exception as e:
                print(f"⚠️ self_reflection failed: {e}")
            return

        if not changes:
            return

        try:
            self.self_reflection.reflect(internal_state, emotions, beliefs)
        except Exception as e:
            print(f"⚠️ self_reflection failed: {e}")

        if changes.get("emotions"):
            try:
                self.experience_review.review(hours=1)
            except Exception as e:
                print(f"⚠️ experience_review failed: {e}")

        if changes.get("beliefs_changed"):
            try:
                self.long_term_reflection.reflect()
            except Exception as e:
                print(f"⚠️ long_term_reflection failed: {e}")

        for key in ("warmth", "irritation", "tension"):
            if abs(changes.get(key, 0)) > STATE_CHANGE_THRESHOLD:
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
