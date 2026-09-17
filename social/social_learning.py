from social.social_model import SocialModel
from social.interaction_history import InteractionHistory


class SocialLearning:
    """
    Watches patterns in how a person behaves and updates Ruby's model of them.
    No caps on any value.

    NOTE: The bump() amounts below (0.02, 0.005, etc.) are SCAFFOLDING.
    When V1.3 (Learning) is built, these hardcoded rules will be replaced
    with associations Ruby develops through her own experience.
    """

    def __init__(self, subject="not_set"):
        self.subject = subject
        self.model = SocialModel(subject=subject)
        self.history = InteractionHistory()

    def process(self, user_message, ruby_reply, context):
        emotions = context.get("emotions", {})
        inner = context.get("internal_state", {})

        dominant_emotion = ""
        if emotions:
            active = {k: v for k, v in emotions.items() if v != 0}
            if active:
                dominant_emotion = max(active, key=lambda k: abs(active[k]))

        mood = ""
        if inner:
            if inner.get("irritation", 0) > 5:
                mood = "irritated"
            elif inner.get("warmth", 0) > 5:
                mood = "warm"
            elif inner.get("tension", 0) > 5:
                mood = "tense"
            else:
                mood = "neutral"

        self.history.log(
            subject=self.subject,
            user_message=user_message,
            ruby_reply=ruby_reply,
            emotion_at_time=dominant_emotion,
            mood_at_time=mood,
        )

        self.model.record_interaction()

        text = user_message.lower()

        # ----- SCAFFOLDING — replaced by V1.3 Learning -----
        if any(m in text for m in ["i feel", "i'm scared", "i lost", "my father", "my mother"]):
            self.model.bump("trust", 0.02)
            self.model.bump("familiarity", 0.01)

        self.model.bump("familiarity", 0.005)

        if any(m in text for m in ["actually", "imagine", "what if", "i wonder"]):
            self.model.bump("respect", 0.02)
        # ----- end scaffolding -----

        new_class = self.model.classify()
        self.model.update_field("relationship_type", new_class)
        self.model.update_field("perceived_emotional_state", mood)

        if "addie" in text and self.subject != "addie":
            existing_notes = self.model.get().get("notes") or ""
            if "mentions Addie" not in existing_notes:
                self.model.update_field(
                    "notes",
                    (existing_notes + " | mentions Addie").strip(" |")
                )

    def describe(self):
        m = self.model.get()
        if not m:
            return "You don't know this person yet."
        parts = [
            f"Interactions: {m['total_interactions']}",
            f"They are: {m['relationship_type']}",
        ]
        if m.get("notes"):
            parts.append(f"Notes: {m['notes']}")
        return "\n".join(parts)

    def wipe(self):
        self.model.wipe()
