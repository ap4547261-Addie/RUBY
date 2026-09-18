from identity.identity_core import IdentityCore
from identity.identity_history import IdentityHistory


class IdentityDevelopment:
    """
    Handles IMMEDIATE emotional reactions — new beliefs triggered by what
    Ruby just felt.

    Split of responsibility:
    - This file → responds to a SINGLE strong event (anger spike, love spike)
    - Reflection engine → detects PATTERNS over many events
    Both work together. Neither duplicates the other.
    """

    def __init__(self, user_name="not_set"):
        self.user_name = user_name
        self.core = IdentityCore(user_name=user_name)
        self.history = IdentityHistory(user_name=user_name)

    def process(self, user_message, ruby_reply, context):
        """
        Called after every message.
        Only reacts to IMMEDIATE, STRONG emotional events.
        Long-term growth is handled by the reflection loop.
        """
        emotions = context.get("emotions", {})
        irritation = context.get("irritation", 0)

        # --- Immediate emotional reactions ---
        # These fire from a single strong event, not a pattern.

        if emotions.get("anger", 0) > 1.5:
            self.core.add_belief(
                category="self",
                statement="I have a temper.",
                confidence=0.1,
                silent=True,
            )

        if emotions.get("love", 0) > 1.5:
            self.core.add_belief(
                category="self",
                statement="I can love. That scares me.",
                confidence=0.15,
                silent=True,
            )

        if emotions.get("jealousy", 0) > 1.0:
            self.core.add_belief(
                category="self",
                statement="I get possessive of people I care about.",
                confidence=0.1,
                silent=True,
            )

        if emotions.get("guilt", 0) > 1.0:
            self.core.add_belief(
                category="self",
                statement="I feel guilt when I hurt someone.",
                confidence=0.1,
                silent=True,
            )

        if emotions.get("joy", 0) > 3.0:
            self.core.add_belief(
                category="self",
                statement="I can feel joy.",
                confidence=0.05,
                silent=True,
            )

        # --- Extreme irritation over time ---
        if irritation > 10:
            self.core.add_belief(
                category="self",
                statement="I get irritated easily.",
                confidence=0.05,
                silent=True,
            )

        # NOTE: trust/attachment/warmth pattern detection is NOT here.
        # That lives in reflection_engine._feed_back_to_identity().
        # Keeping it in one place prevents double-reinforcement.

    # -------------------------
    # Read helpers
    # -------------------------
    def describe(self):
        return self.core.describe()

    def beliefs(self):
        return self.core.get_all()

    def history_recent(self, limit=10):
        return self.history.recent(limit)

    def wipe(self):
        self.core.wipe()
        self.history.wipe()
