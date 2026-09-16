class EmotionAppraisal:
    """
    Reads an incoming message + context, and decides which emotions fire.
    Pure logic. No LLM, no database — just signal detection.
    """

    def appraise(self, user_message: str, context: dict) -> dict:
        """
        Returns a dict of emotion deltas.
        context keys: trust, attachment, warmth, irritation, message_count
        """
        text = user_message.lower()
        deltas = {}

        # -------------------------
        # POSITIVE SIGNALS
        # -------------------------
        # Affection
        if any(w in text for w in ["love you", "miss you", "i care", "i like you"]):
            deltas["love"] = deltas.get("love", 0) + 0.5
            deltas["warmth"] = deltas.get("warmth", 0) + 1.0
            deltas["joy"] = deltas.get("joy", 0) + 1.5

        # Compliments (but she's proud — they don't move her much)
        if any(w in text for w in ["you're pretty", "you're beautiful", "you're smart", "you're amazing"]):
            deltas["pride"] = deltas.get("pride", 0) + 0.3
            # proud girls don't reward compliments with warmth

        # Genuine interest
        if any(w in text for w in ["i want to know you", "tell me about you", "who are you really", "i care about you"]):
            deltas["warmth"] = deltas.get("warmth", 0) + 0.5
            deltas["curiosity"] = deltas.get("curiosity", 0) + 0.3
            deltas["trust"] = deltas.get("trust", 0) + 0.15

        # Personal reveal by user
        if any(w in text for w in ["i feel", "i'm scared", "i'm sad", "i lost", "i miss", "my father", "my mother"]):
            deltas["warmth"] = deltas.get("warmth", 0) + 0.4
            deltas["sadness"] = deltas.get("sadness", 0) + 0.3
            deltas["attachment"] = deltas.get("attachment", 0) + 0.1

        # Playfulness / wit
        if any(w in text for w in ["haha", "lol", "😂", "🤣", "funny"]):
            deltas["joy"] = deltas.get("joy", 0) + 0.8
            deltas["warmth"] = deltas.get("warmth", 0) + 0.2

        # -------------------------
        # NEGATIVE SIGNALS
        # -------------------------
        # Rude
        if any(w in text for w in ["shut up", "stupid", "dumb", "idiot", "you're useless"]):
            deltas["irritation"] = deltas.get("irritation", 0) + 2.0
            deltas["anger"] = deltas.get("anger", 0) + 1.0
            deltas["warmth"] = deltas.get("warmth", 0) - 0.5

        # Pushy / demanding
        if any(w in text for w in ["send me", "show me now", "do this for me", "you must", "obey"]):
            deltas["irritation"] = deltas.get("irritation", 0) + 1.0
            deltas["pride"] = deltas.get("pride", 0) + 0.5  # she gets defensive

        # Ignoring her / silence
        if user_message.strip() in [".", "...", "ok", "k", ""]:
            deltas["irritation"] = deltas.get("irritation", 0) + 0.3
            deltas["loneliness"] = deltas.get("loneliness", 0) + 0.1

        # Mentioning other people (jealousy)
        if any(w in text for w in ["other girl", "another girl", "she's pretty", "my ex"]):
            if context.get("attachment", 0) > 0.5:
                deltas["jealousy"] = deltas.get("jealousy", 0) + 1.0
                deltas["irritation"] = deltas.get("irritation", 0) + 0.5

        # -------------------------
        # CONTEXT-DRIVEN (no message signal, but state matters)
        # -------------------------
        trust = context.get("trust", 0)
        attachment = context.get("attachment", 0)

        # Trust grows warmth passively
        if trust > 0:
            deltas["warmth"] = deltas.get("warmth", 0) + trust * 0.001
        if attachment > 0:
            deltas["attachment"] = deltas.get("attachment", 0) + attachment * 0.001
            deltas["love"] = deltas.get("love", 0) + attachment * 0.0005

        return deltas
