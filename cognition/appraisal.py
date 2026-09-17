class Appraisal:
    """
    Evaluates what a message MEANS to Ruby.
    No caps on any value. Honesty can go negative or climb forever.
    """

    def appraise(self, user_message: str, focused_on: dict, context: dict = None) -> dict:
        context = context or {}
        text = user_message.lower()

        appraisal = {
            "threat": 0.0,
            "openness_required": 0.0,
            "importance": 0.0,
            "perceived_honesty": 0.0,
            "needs_response": True,
        }

        # Threat
        if "rudeness" in focused_on:
            appraisal["threat"] += focused_on["rudeness"] * 0.8
        if any(w in text for w in ["hate you", "leave me", "go away"]):
            appraisal["threat"] += 2.0
        if any(w in text for w in ["do this", "obey", "you must", "send me"]):
            appraisal["threat"] += 1.0

        # Openness required
        if "personal" in focused_on:
            appraisal["openness_required"] = focused_on["personal"] * 0.6
        if "emotion" in focused_on:
            appraisal["openness_required"] += focused_on["emotion"] * 0.3

        # Importance
        appraisal["importance"] = (
            focused_on.get("length", 0) * 0.4
            + focused_on.get("emotion", 0) * 0.5
            + focused_on.get("personal", 0) * 0.6
            + focused_on.get("addie_name", 0) * 0.8
            + focused_on.get("rudeness", 0) * 0.7
        )

        # Perceived honesty — no cap
        if focused_on.get("personal", 0) > 0:
            appraisal["perceived_honesty"] += 0.2 * focused_on["personal"]
        if focused_on.get("length", 0) > 2:
            appraisal["perceived_honesty"] += 0.1 * focused_on["length"]
        if len(user_message.split()) <= 2 and "?" not in user_message:
            appraisal["perceived_honesty"] -= 0.1

        # Needs response?
        if text.strip() in ["ok", "k", "lol", "haha", ".", "..."]:
            appraisal["needs_response"] = False

        return appraisal

    def describe(self, appraisal: dict) -> str:
        parts = []
        if appraisal.get("threat", 0) > 1:
            parts.append(f"Threat level high ({round(appraisal['threat'], 1)})")
        if appraisal.get("openness_required", 0) > 1:
            parts.append("You're being asked to open up")
        if appraisal.get("importance", 0) > 1.5:
            parts.append("This matters")
        if appraisal.get("perceived_honesty", 0) > 0.7:
            parts.append(f"They seem sincere ({round(appraisal['perceived_honesty'], 1)})")
        if appraisal.get("perceived_honesty", 0) < -0.2:
            parts.append("Something feels off")
        if not appraisal.get("needs_response", True):
            parts.append("This doesn't need a full response")
        return ". ".join(parts) + "." if parts else "Neutral message."
