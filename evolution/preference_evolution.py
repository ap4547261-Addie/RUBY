from learning.preference_learning import PreferenceLearning


class PreferenceEvolution:
    """
    Deepens the V1.3 preference learning into stable, permanent likes/dislikes.
    Extracts patterns from accumulated preferences.
    """

    def __init__(self, user_name="not_set"):
        self.user_name = user_name
        self.preference = PreferenceLearning(user_name=user_name)

    def process(self):
        """Look at accumulated preferences. Promote strong ones to core identity."""
        prefs = self.preference.get_all()

        for topic, feeling, seen in prefs:
            # strong positive preference, seen many times → becomes belief
            if feeling > 10 and seen > 20:
                from identity.identity_core import IdentityCore
                ident = IdentityCore(user_name=self.user_name)
                ident.add_belief(
                    category="likes",
                    statement=f"I've grown to love {topic}.",
                    confidence=0.1,
                    silent=True,
                    reason="accumulated_preference",
                )

            # strong negative preference → becomes dislike belief
            if feeling < -10 and seen > 20:
                from identity.identity_core import IdentityCore
                ident = IdentityCore(user_name=self.user_name)
                ident.add_belief(
                    category="dislikes",
                    statement=f"I've come to dislike {topic}.",
                    confidence=0.1,
                    silent=True,
                    reason="accumulated_preference",
                )

    def preferences(self):
        return self.preference.get_all()

    def wipe(self):
        self.preference.wipe()
