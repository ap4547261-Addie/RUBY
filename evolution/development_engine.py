from evolution.value_evolution import ValueEvolution
from evolution.personality_evolution import PersonalityEvolution
from evolution.preference_evolution import PreferenceEvolution


class DevelopmentEngine:
    """
    The coordinator of all long-term evolution.
    Called after every message. Decides what (if anything) needs to shift.
    """

    def __init__(self, user_name="not_set"):
        self.user_name = user_name
        self.values = ValueEvolution(user_name=user_name)
        self.personality = PersonalityEvolution(user_name=user_name)
        self.preferences = PreferenceEvolution(user_name=user_name)

    def process(self, internal_state, emotions, relationship, learning):
        # --- Personality arc ---
        try:
            self.personality.process(
                internal_state, emotions, relationship, learning
            )
        except Exception as e:
            print(f"⚠️ personality_evolution failed: {e}")

        # --- Preference evolution ---
        try:
            self.preferences.process()
        except Exception as e:
            print(f"⚠️ preference_evolution failed: {e}")

        # --- Value evolution ---
        try:
            self._evolve_values(internal_state, emotions, relationship)
        except Exception as e:
            print(f"⚠️ value_evolution failed: {e}")

    # -------------------------
    # Value drift rules
    # -------------------------
    def _evolve_values(self, internal_state, emotions, relationship):
        trust = relationship.get("trust", 0)
        attachment = relationship.get("attachment", 0)
        count = relationship.get("message_count", 0)

        warmth = internal_state.get("warmth", 0)
        irritation = internal_state.get("irritation", 0)
        tension = internal_state.get("tension", 0)

        # --- Connection grows with sustained trust ---
        if trust > 20 and attachment > 5:
            self.values.shift("connection", 0.001, reason="growing_attachment")

        # --- Warmth value grows with sustained warmth ---
        if warmth > 30:
            self.values.shift("warmth", 0.001, reason="sustained_warmth")

        # --- Safety value softens when trust is deep ---
        if trust > 50 and count > 500:
            self.values.shift("safety", -0.001, reason="learned_to_trust")

        # --- Loyalty grows when someone consistently stays ---
        if count > 500 and trust > 30:
            self.values.shift("loyalty", 0.001, reason="consistent_presence")

        # --- Freedom holds if she's respected ---
        if irritation < 1 and tension < 1 and count > 200:
            self.values.shift("freedom", 0.0005, reason="respected_agency")

        # --- Freedom shrinks if pushed ---
        if irritation > 5 and count > 50:
            self.values.shift("freedom", 0.002, reason="pushed_too_far")

        # --- Growth value grows with self-reflection ---
        # (hooked later when reflection count grows)

        # --- Authenticity grows when no one tries to fake her ---
        if count > 200 and irritation < 2:
            self.values.shift("authenticity", 0.0005, reason="allowed_to_be_herself")

    # -------------------------
    # Prompt summary
    # -------------------------
    def describe(self):
        return self.values.describe()

    # -------------------------
    # Read
    # -------------------------
    def get_values(self):
        return self.values.get_all()

    def get_value_history(self, limit=None):
        return self.values.get_history(limit=limit)

    def get_personality(self):
        return self.personality.traits()

    def get_preferences(self):
        return self.preferences.preferences()

    def wipe(self):
        self.values.wipe()
        self.personality.wipe()
        self.preferences.wipe()
