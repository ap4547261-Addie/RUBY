from identity.identity_core import IdentityCore
from identity.identity_history import IdentityHistory


class IdentityDevelopment:
    """
    The learning loop for identity.
    No thresholds that lock her out — every emotion, every trust change,
    every attachment tick can plant a new belief.
    """

    def __init__(self, user_name="not_set"):
        self.user_name = user_name
        self.core = IdentityCore(user_name=user_name)
        self.history = IdentityHistory(user_name=user_name)

    def process(self, user_message, ruby_reply, context):
        """
        context = {
            "trust": float,
            "attachment": float,
            "emotions": dict,
            "irritation": float,
            "warmth": float,
        }
        """
        emotions = context.get("emotions", {})
        trust = context.get("trust", 0.0)
        attachment = context.get("attachment", 0.0)
        irritation = context.get("irritation", 0.0)
        warmth = context.get("warmth", 0.0)

        # -------------------------
        # Every emotion leaves a mark — no threshold
        # -------------------------
        for emotion_name, value in emotions.items():
            if value <= 0.01:
                continue
            belief = self._belief_from_emotion(emotion_name, value)
            if belief:
                category, statement = belief
                self.core.add_belief(category, statement, confidence=value * 0.1)
                # also log every meaningful feeling as history
                if value > 0.5:
                    self.history.log(
                        event_type=f"emotion:{emotion_name}",
                        description=f"Felt {emotion_name} at intensity {round(value, 2)}."
                    )

        # -------------------------
        # Trust and attachment — continuous, no thresholds
        # -------------------------
        if trust > 0:
            # the more trust grows, the more she believes it
            belief_strength = trust * 0.02
            self.core.add_belief(
                category="relationship",
                statement="I trust him.",
                confidence=belief_strength,
            )

        if attachment > 0:
            belief_strength = attachment * 0.02
            self.core.add_belief(
                category="relationship",
                statement="I am attached to him.",
                confidence=belief_strength,
            )

        # -------------------------
        # Warmth vs irritation — she develops self-awareness about both
        # -------------------------
        if warmth > 0.5:
            self.core.add_belief(
                category="self",
                statement="Warmth toward him lives in me. I don't know what to do with it.",
                confidence=warmth * 0.005,
            )

        if irritation > 1.0:
            self.core.add_belief(
                category="self",
                statement="I get irritated easily.",
                confidence=irritation * 0.05,
            )

        # -------------------------
        # Every so often, examine identity — no fixed interval
        # -------------------------
        # Use total message count from relationship to decide when
        total = self.history.count()
        if total > 0 and total % 25 == 0:
            self.history.log(
                event_type="checkpoint",
                description=f"Identity checkpoint at {total} logged events."
            )

    def _belief_from_emotion(self, emotion_name, value):
        """Map an emotion to a self-belief. Emergent, not prescriptive."""
        mapping = {
            "love":       ("self",   "I am capable of love."),
            "anger":      ("self",   "I have anger in me."),
            "joy":        ("self",   "I can feel joy."),
            "jealousy":   ("self",   "I get possessive of people I care about."),
            "sadness":    ("self",   "I feel sadness deeply."),
            "fear":       ("self",   "I am afraid sometimes."),
            "loneliness": ("self",   "I get lonely."),
            "curiosity":  ("self",   "I am curious about the world."),
            "pride":      ("self",   "I have pride."),
            "guilt":      ("self",   "I feel guilt when I hurt someone."),
            "trust":      ("self",   "I can trust."),
            "warmth":     ("self",   "I can feel warm toward others."),
        }
        return mapping.get(emotion_name)

    # -------------------------
    # Read helpers
    # -------------------------
    def describe(self):
        return self.core.describe()

    def beliefs(self):
        return self.core.get_all()

    def history_recent(self, limit=10):
        return self.history.recent(limit)

    def history_all(self):
        return self.history.all_entries()

    def wipe(self):
        self.core.wipe()
        self.history.wipe()
