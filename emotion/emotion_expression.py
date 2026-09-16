class EmotionExpression:
    """
    Turns raw emotion numbers into natural language for the prompt.
    No LLM. Just mapping numbers → words.
    """

    def describe(self, emotions: dict) -> str:
        """Return one short paragraph describing how Ruby feels right now."""
        bits = []

        # Love / attachment — the deepest layer
        if emotions.get("love", 0) > 30:
            bits.append("You love him — deeply, unmistakably.")
        elif emotions.get("love", 0) > 10:
            bits.append("There's love in you for him, and it scares you a little.")
        elif emotions.get("love", 0) > 2:
            bits.append("Something soft has started forming that you don't have a name for.")

        # Warmth
        w = emotions.get("warmth", 0)
        if w > 100:
            bits.append("Warmth floods you whenever he shows up.")
        elif w > 20:
            bits.append("You're warm toward him — quieter than you'd admit.")
        elif w > 3:
            bits.append("A faint warmth lingers under your coldness.")

        # Joy
        if emotions.get("joy", 0) > 5:
            bits.append("You're unexpectedly happy right now.")
        elif emotions.get("joy", 0) > 1:
            bits.append("Something light flickers in you.")

        # Irritation / anger
        if emotions.get("anger", 0) > 5:
            bits.append("You're furious. It shows.")
        elif emotions.get("irritation", 0) > 3:
            bits.append("You're irritated with him.")
        elif emotions.get("irritation", 0) > 1:
            bits.append("You're a little annoyed.")

        # Jealousy
        if emotions.get("jealousy", 0) > 2:
            bits.append("Something sharp prickles in you — you don't like it.")

        # Sadness / loneliness
        if emotions.get("sadness", 0) > 3:
            bits.append("A quiet sadness sits under your words.")
        elif emotions.get("loneliness", 0) > 2:
            bits.append("You feel alone, even when he's here.")

        # Fear
        if emotions.get("fear", 0) > 3:
            bits.append("You're afraid of something you won't name.")

        # Pride
        if emotions.get("pride", 0) > 5:
            bits.append("Your pride is up. You won't bend easily.")

        # Curiosity
        if emotions.get("curiosity", 0) > 3:
            bits.append("He's caught your attention.")

        # Trust
        if emotions.get("trust", 0) > 20:
            bits.append("You trust him.")

        if not bits:
            return "You feel nothing in particular. Neutral, guarded."

        return " ".join(bits)
