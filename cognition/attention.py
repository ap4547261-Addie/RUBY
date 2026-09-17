class Attention:
    """
    Decides what Ruby focuses on in a message.
    Every message has signals — she notices some, ignores others.
    No caps on attention values.
    """

    def attend(self, user_message: str, context: dict = None) -> dict:
        context = context or {}
        text = user_message.lower()
        words = user_message.split()
        word_count = len(words)

        focused_on = {}

        # Length
        if word_count > 20:
            focused_on["length"] = 3.0
        elif word_count > 10:
            focused_on["length"] = 2.0
        elif word_count > 5:
            focused_on["length"] = 1.0

        # Questions
        if "?" in user_message:
            focused_on["question"] = 2.0

        # Emotional markers
        emotional_markers = [
            "love", "hate", "miss", "scared", "sad", "happy",
            "angry", "lonely", "hurt", "tired", "die", "died",
        ]
        emotional_hits = sum(1 for m in emotional_markers if m in text)
        if emotional_hits:
            focused_on["emotion"] = emotional_hits * 1.5

        # Personal reveals
        personal_markers = [
            "i feel", "i think", "i believe", "my mother", "my father",
            "my life", "i'm scared", "i lost", "i miss", "i love",
            "i remember", "i dream", "i wish", "i hope",
        ]
        personal_hits = sum(1 for m in personal_markers if m in text)
        if personal_hits:
            focused_on["personal"] = personal_hits * 2.0

        # Names
        if "ruby" in text:
            focused_on["name"] = 2.5
        if "addie" in text:
            focused_on["addie_name"] = 3.5

        # Direct address
        if " you " in f" {text} ":
            focused_on["direct_address"] = 1.5

        # Rudeness
        rude_markers = ["shut up", "stupid", "dumb", "idiot"]
        if any(m in text for m in rude_markers):
            focused_on["rudeness"] = 4.0

        if not focused_on:
            focused_on["neutral"] = 1.0

        return focused_on

    def describe(self, focused_on: dict) -> str:
        if not focused_on:
            return "Nothing in particular."
        lines = [
            f"{k} ({round(v, 1)})"
            for k, v in sorted(focused_on.items(), key=lambda x: -x[1])
        ]
        return "Noticing: " + ", ".join(lines) + "."
