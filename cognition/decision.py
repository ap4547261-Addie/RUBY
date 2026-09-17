class Decision:
    """
    Ruby's chosen INTENT before she speaks.
    Tracks recent intents so she doesn't get stuck in one mode.
    """

    def __init__(self):
        self._recent_intents = []   # last 10 intents

    def _remember(self, intent):
        self._recent_intents.append(intent)
        if len(self._recent_intents) > 10:
            self._recent_intents.pop(0)

    def _was_recent(self, intent, lookback=4):
        return intent in self._recent_intents[-lookback:]

    def decide(self, focused_on, appraisal, prediction, context=None):
        context = context or {}
        trust = context.get("trust", 0)
        attachment = context.get("attachment", 0)
        irritation = context.get("irritation", 0)
        warmth = context.get("warmth", 0)

        intent = "respond_coldly"
        tone = "cold"
        length = "short"

        # ---- Threat response ----
        if appraisal.get("threat", 0) > 1.5:
            intent = "shut_down"
            tone = "cold"
            length = "short"

        # ---- Rudeness ----
        elif "rudeness" in focused_on:
            if irritation > 3 or trust < 5:
                intent = "reject"
                tone = "cutting"
                length = "short"
            else:
                intent = "warn"
                tone = "cold"
                length = "short"

        # ---- Father's name mentioned ----
        elif "addie_name" in focused_on:
            intent = "protect_memory"
            tone = "quiet"
            length = "very_short"

        # ---- Personal reveal ----
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

        # ---- Direct question ----
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

        # ---- Low-effort message ----
        elif not appraisal.get("needs_response", True):
            intent = "minimal"
            tone = "flat"
            length = "one_word"

        # ---- Long meaningful message ----
        elif focused_on.get("length", 0) > 2 and trust > 10:
            intent = "engage"
            tone = "warm"
            length = "medium"

        # ---- Baseline by trust ----
        else:
            if trust < 5:
                # COLD VARIETY ROTATION
                cold_intents = [
                    ("probe",            "cold"),
                    ("test",             "cold"),
                    ("dismiss",          "cold"),
                    ("question_back",    "cold"),
                    ("tease",            "cold"),
                    ("reluctant_engage", "cool"),
                ]
                chosen = None
                for cand_intent, cand_tone in cold_intents:
                    if not self._was_recent(cand_intent):
                        chosen = (cand_intent, cand_tone)
                        break
                if chosen is None:
                    chosen = ("respond_coldly", "cold")
                intent, tone = chosen
                length = "short"
            elif trust < 20:
                intent = "respond_normally"
                tone = "cool"
                length = "short"
            else:
                intent = "respond_warmly"
                tone = "warm"
                length = "medium"

        # ---- Warmth override ----
        if warmth > 50 and intent in ("respond_coldly", "dismiss"):
            intent = "soften"
            tone = "warm"
            length = "medium"

        self._remember(intent)

        return {
            "intent": intent,
            "tone": tone,
            "length": length,
        }

    def describe(self, decision):
        return (
            f"Your intent: {decision.get('intent', 'respond')}. "
            f"Tone: {decision.get('tone', 'neutral')}. "
            f"Length: {decision.get('length', 'short')}."
        )

    def wipe(self):
        self._recent_intents = []
