class Decision:
    """
    Ruby's chosen INTENT before she speaks.
    This is the layer that stops the model from defaulting to assistant mode.
    Ruby decides what she wants to do — the LLM just executes it.
    """

    def decide(self, focused_on: dict, appraisal: dict,
               prediction: dict, context: dict = None) -> dict:
        context = context or {}
        trust = context.get("trust", 0)
        attachment = context.get("attachment", 0)
        irritation = context.get("irritation", 0)
        warmth = context.get("warmth", 0)

        intent = "respond"
        tone = "neutral"
        length = "short"

        # Threat response
        if appraisal.get("threat", 0) > 1.5:
            intent = "shut_down"
            tone = "cold"
            length = "short"

        # Rudeness specific
        elif "rudeness" in focused_on:
            if irritation > 3 or trust < 5:
                intent = "reject"
                tone = "cutting"
                length = "short"
            else:
                intent = "warn"
                tone = "cold"
                length = "short"

        # Personal reveal from them
        elif appraisal.get("openness_required", 0) > 1:
            if trust > 15 and attachment > 5:
                intent = "share_back"
                tone = "soft"
                length = "medium"
            elif trust > 5:
                intent = "acknowledge"
                tone = "guarded_warm"
                length = "short"
            else:
                intent = "deflect_kindly"
                tone = "cold"
                length = "short"

        # Father's name mentioned
        elif "addie_name" in focused_on:
            intent = "protect_memory"
            tone = "quiet"
            length = "very_short"

        # Direct question
        elif "question" in focused_on:
            if trust > 20 and attachment > 10:
                intent = "answer_openly"
                tone = "warm"
                length = "medium"
            elif trust > 5:
                intent = "answer_briefly"
                tone = "cool"
                length = "short"
            else:
                intent = "answer_vaguely"
                tone = "cold"
                length = "short"

        # Low-effort message
        elif not appraisal.get("needs_response", True):
            intent = "minimal"
            tone = "flat"
            length = "one_word"

        # Long meaningful message
        elif focused_on.get("length", 0) > 2 and trust > 10:
            intent = "engage"
            tone = "warm"
            length = "medium"

        # Baseline by trust
        else:
            if trust < 5:
                intent = "respond_coldly"
                tone = "cold"
                length = "short"
            elif trust < 20:
                intent = "respond_normally"
                tone = "cool"
                length = "short"
            else:
                intent = "respond_warmly"
                tone = "warm"
                length = "medium"

        # Deep warmth overrides coldness
        if warmth > 50 and intent in ("respond_coldly", "respond_normally"):
            intent = "soften"
            tone = "warm"
            length = "medium"

        return {
            "intent": intent,
            "tone": tone,
            "length": length,
        }

    def describe(self, decision: dict) -> str:
        return (
            f"Your intent: {decision.get('intent', 'respond')}. "
            f"Tone: {decision.get('tone', 'neutral')}. "
            f"Length: {decision.get('length', 'short')}."
        )
