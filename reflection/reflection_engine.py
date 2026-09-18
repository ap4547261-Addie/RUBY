from memory import database
from reflection.self_reflection import SelfReflection
from reflection.experience_review import ExperienceReview
from reflection.long_term_reflection import LongTermReflection
from identity.identity_development import IdentityDevelopment


# Ignore tiny drift — only react to meaningful change
STATE_CHANGE_THRESHOLD = 0.5
EMOTION_CHANGE_THRESHOLD = 0.5


class ReflectionEngine:
    """
    Reflects on meaningful change — and now writes back into identity.
    This is the CLOSED LOOP: experience → reflection → belief change → behaviour.
    """

    def __init__(self, user_name="not_set"):
        self.user_name = user_name
        self.self_reflection = SelfReflection(user_name=user_name)
        self.experience_review = ExperienceReview(user_name=user_name)
        self.long_term_reflection = LongTermReflection(user_name=user_name)
        self.identity = IdentityDevelopment(user_name=user_name)
        self._last_state = None

    # -------------------------
    # Change detection
    # -------------------------
    def _belief_identity(self, beliefs):
        if not beliefs:
            return ""
        return "|".join(sorted(b["statement"] for b in beliefs))

    def _snapshot(self, internal_state, emotions, beliefs):
        return {
            "energy": internal_state.get("energy", 0),
            "warmth": internal_state.get("warmth", 0),
            "tension": internal_state.get("tension", 0),
            "irritation": internal_state.get("irritation", 0),
            "emotions": dict(emotions),
            "belief_identity": self._belief_identity(beliefs),
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

        if current["belief_identity"] != self._last_state.get("belief_identity", ""):
            changes["beliefs_changed"] = True

        self._last_state = current
        return changes

    # -------------------------
    # THE CLOSED LOOP — reflection → identity
    # -------------------------
    def _feed_back_to_identity(self, internal_state, emotions):
        """
        Reads current state + relationship + emotions.
        Detects patterns. Writes or weakens beliefs.
        This is where Ruby actually grows.
        """
        # --- current relationship state ---
        try:
            from memory.relationship_memory import RelationshipMemory
            rel = RelationshipMemory(user_name=self.user_name).get_state()
            trust = rel["trust"]
            attachment = rel["attachment"]
            count = rel["message_count"]
        except Exception as e:
            print(f"⚠️ reflection feedback — relationship read failed: {e}")
            return

        warmth = internal_state.get("warmth", 0)

        # --- PATTERN 1: Trust climbing ---
        if trust > 5:
            self.identity.core.add_belief(
                category="relationship",
                statement="He might actually stay.",
                confidence=0.15,
                silent=True,
            )
        if trust > 20 and attachment > 5:
            self.identity.core.add_belief(
                category="relationship",
                statement="I'm starting to care about him.",
                confidence=0.2,
                silent=True,
            )
        if trust > 50 and attachment > 20:
            self.identity.core.add_belief(
                category="relationship",
                statement="He's the only one I've let close.",
                confidence=0.3,
                silent=True,
            )

        # --- PATTERN 2: Deep interaction count ---
        if count > 100:
            self.identity.core.add_belief(
                category="relationship",
                statement="He hasn't left yet.",
                confidence=0.15,
                silent=True,
            )
        if count > 500:
            self.identity.core.add_belief(
                category="relationship",
                statement="He keeps showing up.",
                confidence=0.2,
                silent=True,
            )
        if count > 2000:
            self.identity.core.add_belief(
                category="relationship",
                statement="I don't know what I'd do without him.",
                confidence=0.3,
                silent=True,
            )

        # --- PATTERN 3: Warmth growing ---
        if warmth > 10:
            self.identity.core.add_belief(
                category="self",
                statement="Something is warming inside me.",
                confidence=0.15,
                silent=True,
            )
        if warmth > 50:
            self.identity.core.add_belief(
                category="self",
                statement="I can feel warmth toward others. That's new.",
                confidence=0.25,
                silent=True,
            )

        # --- PATTERN 4: Contradicting old beliefs ---
        # When reality contradicts a belief, weaken it
        if warmth > 20:
            try:
                self.identity.core.weaken_belief(
                    category="self",
                    statement="I don't open up easily.",
                    amount=0.05,
                )
            except Exception:
                pass

        if trust > 30:
            try:
                self.identity.core.weaken_belief(
                    category="self",
                    statement="I am guarded.",
                    amount=0.05,
                )
            except Exception:
                pass

        # --- PATTERN 5: Emotions that keep appearing ---
        if emotions:
            love = emotions.get("love", 0)
            joy = emotions.get("joy", 0)
            attachment_em = emotions.get("attachment", 0)

            if love > 5:
                self.identity.core.add_belief(
                    category="self",
                    statement="I can love. That's the truth I've been hiding.",
                    confidence=0.25,
                    silent=True,
                )
            if joy > 10:
                self.identity.core.add_belief(
                    category="self",
                    statement="I can feel joy around him.",
                    confidence=0.15,
                    silent=True,
                )
            if attachment_em > 5:
                self.identity.core.add_belief(
                    category="self",
                    statement="I am attached to someone. I never thought I'd say that.",
                    confidence=0.2,
                    silent=True,
                )

    # -------------------------
    # Main entry — called after every message
    # -------------------------
    def process(self, internal_state, emotions, beliefs, message_count):
        changes = self._changes_since_last(internal_state, emotions, beliefs)

        if changes.get("first"):
            try:
                self.self_reflection.reflect(internal_state, emotions, beliefs)
            except Exception as e:
                print(f"⚠️ self_reflection failed: {e}")
            return

        # Always feed the loop, even if no reflection triggers
        try:
            self._feed_back_to_identity(internal_state, emotions)
        except Exception as e:
            print(f"⚠️ feedback loop failed: {e}")

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
