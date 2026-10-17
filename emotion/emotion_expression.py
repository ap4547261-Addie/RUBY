class EmotionExpression:
    """
    Rich, unbounded emotional language. No tiers, no caps.
    Each emotion gets many intensity words — not just 3.
    """

    NAMES = {
        "joy":        "joy",
        "warmth":     "warmth",
        "love":       "love",
        "attachment": "attachment",
        "trust":      "trust",
        "irritation": "irritation",
        "anger":      "anger",
        "jealousy":   "jealousy",
        "sadness":    "sadness",
        "loneliness": "loneliness",
        "fear":       "fear",
        "curiosity":  "curiosity",
        "pride":      "pride",
        "guilt":      "guilt",
    }

    def describe(self, emotions: dict) -> str:
        if not emotions:
            return "You feel nothing in particular. Neutral, guarded."

        active = sorted(
            [(k, v) for k, v in emotions.items() if v != 0],
            key=lambda x: -abs(x[1])
        )
        if not active:
            return "You feel nothing in particular. Neutral, guarded."

        # Only fully describe the top 3 — most intense feelings first.
        # Others are mentioned briefly so the prompt doesn't overwhelm.
        primary = active[:3]
        secondary = active[3:6]

        parts = [self._phrase(k, v) for k, v in primary]

        if secondary:
            # words only — raw numbers like "joy (0.45)" were leaking into the prompt
            tail = ", ".join(self.NAMES.get(k, k) for k, v in secondary)
            parts.append(f"Quieter underneath: {tail}.")

        return " ".join(parts)

    def _phrase(self, name, value):
        subject = self.NAMES.get(name, name)
        mag = abs(value)

        # --- Continuous tiers, 10 levels per emotion ---
        if mag < 0.05:
            return f"A whisper of {subject} — nothing you'd name."
        elif mag < 0.3:
            return f"A faint flicker of {subject} passes through you."
        elif mag < 1:
            return f"There's a quiet {subject} under the surface."
        elif mag < 3:
            return f"{subject.capitalize()} sits in you, steady and real."
        elif mag < 8:
            return f"{subject.capitalize()} is strong in you — hard to ignore."
        elif mag < 20:
            return f"{subject.capitalize()} is overwhelming. It fills you."
        else:
            # Values are unbounded, but a person's inner life isn't narrated at
            # 5 more levels of "consumes you / is the air you breathe" — past
            # this point the wording stays here so replies don't turn melodramatic.
            return f"{subject.capitalize()} consumes you. You can barely think around it."
