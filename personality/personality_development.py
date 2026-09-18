from personality.personality_core import PersonalityCore


class PersonalityDevelopment:
    """
    Shifts Ruby's traits based on accumulated experience.
    Traits do NOT move per message — they drift slowly as patterns emerge.
    No caps. Every trait can drift indefinitely.
    """

    def __init__(self, user_name="not_set"):
        self.user_name = user_name
        self.core = PersonalityCore(user_name=user_name)
        self._last_snapshot = None

    # -------------------------
    # Main entry point
    # -------------------------
    def process(self, internal_state, emotions, relationship, learning):
        """
        Called after every message.
        Only nudges traits when the evidence is strong and sustained.
        """
        trust = relationship.get("trust", 0)
        attachment = relationship.get("attachment", 0)
        count = relationship.get("message_count", 0)

        warmth = internal_state.get("warmth", 0)
        irritation = internal_state.get("irritation", 0)
        tension = internal_state.get("tension", 0)

        # --- Agreeableness grows slowly with trust + warmth ---
        if trust > 10 and warmth > 5:
            # tiny drift — this is the deep slow change, not a flip
            self.core.shift("agreeableness", 0.001)

        # --- Guardedness weakens as trust deepens ---
        if trust > 15 and count > 100:
            self.core.shift("guardedness", -0.001)

        # --- Playfulness grows when joy and warmth are both up ---
        if emotions.get("joy", 0) > 3 and warmth > 3:
            self.core.shift("playfulness", 0.001)

        # --- Neuroticism softens if warmth is sustained ---
        if warmth > 20 and irritation < 1 and tension < 1:
            self.core.shift("neuroticism", -0.0005)

        # --- Pride grows if she wins / proves herself ---
        if emotions.get("pride", 0) > 3:
            self.core.shift("pride", 0.001)

        # --- Openness grows slowly with deep attachment ---
        if attachment > 10 and trust > 30:
            self.core.shift("openness", 0.0005)

        # --- Extraversion ticks up if conversations are consistently long ---
        if count > 500 and warmth > 30:
            self.core.shift("extraversion", 0.0005)

    # -------------------------
    # Read helpers
    # -------------------------
    def describe(self):
        return self.core.describe()

    def traits(self):
        return self.core.get_all()

    def wipe(self):
        self.core.wipe()
