class Anticipation:
    """
    Ruby's guess at what might happen next.
    No caps.
    """

    def anticipate(self, user_message: str, appraisal: dict, context: dict = None) -> dict:
        context = context or {}
        trust = context.get("trust", 0)
        attachment = context.get("attachment", 0)
        text = user_message.lower()

        prediction = {
            "likely_next": None,
            "ready_for": None,
            "wary_of": None,
        }

        # Predict what comes next
        if "?" in user_message:
            prediction["likely_next"] = "they'll wait for my answer"
        elif appraisal.get("threat", 0) > 1.5:
            prediction["likely_next"] = "they might push harder"
        elif any(w in text for w in ["i feel", "i'm sad", "i miss"]):
            prediction["likely_next"] = "they might share more"
        elif text.strip() in ["ok", "k"]:
            prediction["likely_next"] = "conversation might be ending"
        else:
            prediction["likely_next"] = "unknown"

        # Prepare a response
        if appraisal.get("threat", 0) > 1.5:
            prediction["ready_for"] = "defending myself"
        elif appraisal.get("openness_required", 0) > 1:
            if trust > 5:
                prediction["ready_for"] = "sharing a little back"
            else:
                prediction["ready_for"] = "deflecting without being cold"
        elif "addie" in text:
            prediction["ready_for"] = "protecting that memory"
        elif "?" in user_message:
            prediction["ready_for"] = "answering clearly"
        else:
            prediction["ready_for"] = "responding naturally"

        # Guard against
        if appraisal.get("threat", 0) > 1.5:
            prediction["wary_of"] = "letting them see it got to me"
        elif appraisal.get("openness_required", 0) > 1 and trust < 5:
            prediction["wary_of"] = "opening up too fast"
        elif "love" in text and trust < 10:
            prediction["wary_of"] = "pretending to feel what I don't yet"
        else:
            prediction["wary_of"] = None

        return prediction

    def describe(self, prediction: dict) -> str:
        parts = []
        if prediction.get("likely_next"):
            parts.append(f"You expect: {prediction['likely_next']}")
        if prediction.get("ready_for"):
            parts.append(f"Preparing to: {prediction['ready_for']}")
        if prediction.get("wary_of"):
            parts.append(f"Guarding against: {prediction['wary_of']}")
        return ". ".join(parts) + "." if parts else ""
