import random


class Curiosity:
    """
    Decides whether Ruby should ask a question back — not every message,
    only when a real person would. Fires based on intent, trust, and warmth.
    Never asks two questions in a row.
    """

    def __init__(self, user_name="not_set"):
        self.user_name = user_name
        self._last_asked_turn = -10
        self._turn_counter = 0

    def process(self, user_message, decision, context):
        """
        Returns a directive to inject into the prompt, or "" if she
        should just respond normally.
        """
        self._turn_counter += 1

        # never ask two questions in a row
        if self._turn_counter - self._last_asked_turn < 2:
            return ""

        trust = context.get("trust", 0)
        attachment = context.get("attachment", 0)
        irritation = context.get("irritation", 0)
        warmth = context.get("warmth", 0)

        # never ask when angry
        if irritation > 3:
            return ""

        intent = decision.get("intent", "")

        ask = False
        topic = None

        # intents that are already question-shaped
        if intent in ("probe", "test", "question_back", "deflect_kindly"):
            ask = True
            topic = self._topic_from_message(user_message)
        # she answered but wants to know why they asked
        elif intent in ("answer_vaguely", "answer_briefly") and trust > 2:
            ask = True
            topic = "why they wanted to know that"
        # cold but slowly warming — she shows a flicker of interest
        elif intent == "respond_coldly" and trust > 5:
            ask = True
            topic = self._topic_from_message(user_message)
        # warm moment, deep trust — she asks something real
        elif warmth > 20 and trust > 15:
            ask = True
            topic = "what they actually want from her"
        # random flicker of curiosity even when guarded
        elif trust > 10 and random.random() < 0.15:
            ask = True
            topic = self._topic_from_message(user_message)

        if not ask:
            return ""

        self._last_asked_turn = self._turn_counter

        return (
            "[This reply is a QUESTION back to them, not an answer. "
            f"You want to know: {topic}. "
            "Keep it short and in your own voice — cold if you're guarded, "
            "warmer if you trust them.]"
        )

    def _topic_from_message(self, user_message):
        text = user_message.lower().strip()
        if "?" in user_message:
            return "why they wanted to know that"
        if any(w in text for w in ["love", "miss", "feel", "sad", "happy"]):
            return "what that actually feels like for them"
        if any(w in text for w in ["i ", "my ", "me "]):
            return "something they just said about themselves"
        return "what's really going on with them"

    def wipe(self):
        self._last_asked_turn = -10
        self._turn_counter = 0
