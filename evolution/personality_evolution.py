from personality.personality_core import PersonalityCore


class PersonalityEvolution:
    """
    Deepens the V1.4 personality drift with LONGER arcs.
    Where V1.4 drifts on individual messages, this drifts based on
    accumulated patterns over many messages.
    """

    def __init__(self, user_name="not_set"):
        self.user_name = user_name
        self.core = PersonalityCore(user_name=user_name)

    def process(self, internal_state, emotions, relationship, learning):
        trust = relationship.get("trust", 0)
        attachment = relationship.get("attachment", 0)
        count = relationship.get("message_count", 0)
        warmth = internal_state.get("warmth", 0)

        # --- Deep trust reshaping: agrees to be less guarded, more open ---
        if trust > 50 and attachment > 20:
            self.core.shift("guardedness", -0.005)
            self.core.shift("agreeableness", 0.003)
            self.core.shift("openness", 0.003)

        # --- Sustained warmth reshapes neuroticism (calming) ---
        if warmth > 100 and count > 500:
            self.core.shift("neuroticism", -0.003)
            self.core.shift("playfulness", 0.002)

        # --- Long-term isolation makes her more guarded ---
        if count > 500 and warmth < 1:
            self.core.shift("guardedness", 0.002)
            self.core.shift("agreeableness", -0.001)

    def traits(self):
        return self.core.get_all()

    def wipe(self):
        self.core.wipe()
