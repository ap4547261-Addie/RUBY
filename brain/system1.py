# brain/system1.py — Ruby's fast classifier
# Does NOT reply. Only decides how much context the LLM gets.

import re
from typing import Optional


class System1:
    """
    Ruby's fast context classifier.

    Returns:
        'trivial' -> minimal context / fastest path
        'normal'  -> normal ResponseEngine context
        'deep'    -> full context + deeper processing

    System 1 is fast and lightweight.
    It does NOT generate responses or perform reasoning.
    """

    def __init__(self, user_name: str = "not_set"):
        self.user_name = user_name

    # ============================================================
    # NORMALIZATION
    # ============================================================

    @staticmethod
    def _normalize(message: str) -> tuple[str, str]:
        """
        Return:
            original cleaned message
            normalized lowercase message
        """
        m = message.strip()

        # "hiiiiii" -> "hii"
        ml = re.sub(r"(.)\1{2,}", r"\1\1", m.lower())

        # "hi!!!" -> "hi"
        ml_clean = re.sub(r"[!?.]+$", "", ml).strip()

        return m, ml_clean

    # ============================================================
    # MAIN CLASSIFIER
    # ============================================================

    def classify(self, message: str) -> str:
        if not message or not message.strip():
            return "trivial"

        m, ml = self._normalize(message)

        # --------------------------------------------------------
        # 1. DEEP SIGNALS
        # --------------------------------------------------------
        # Checked BEFORE short-message rules, so "I'm sad" doesn't
        # get swallowed as trivial.
        # Uses word-boundary matching so "why" doesn't match "showy".
        # --------------------------------------------------------

        deep_markers = (
            # reasoning / explanation
            "why",
            "how come",
            "explain",
            "explain why",
            "explain how",
            "what do you think",
            "what does this mean",
            "what do you mean",
            "is it possible",
            "how would",
            "should i",
            "should we",

            # memory / history
            "remember",
            "do you remember",
            "did you forget",
            "last time",
            "yesterday",
            "earlier",
            "before",
            "back when",
            "when we",
            "you said",
            "i said",

            # emotions
            "feel",
            "feeling",
            "felt",
            "feels",
            "sad",
            "happy",
            "angry",
            "upset",
            "lonely",
            "scared",
            "afraid",
            "worried",
            "anxious",
            "excited",
            "hurt",
            "confused",
            "frustrated",
            "embarrassed",
            "jealous",
            "miss",
            "missing",
            "love",
            "hate",

            # identity / self
            "who are you",
            "what are you",
            "who am i",
            "what am i",
            "your purpose",
            "my purpose",
            "your identity",
            "my identity",
            "your personality",
            "your memory",

            # beliefs / values / future
            "believe",
            "belief",
            "value",
            "values",
            "dream",
            "dreams",
            "wish",
            "hope",
            "future",
            "goal",
            "goals",
            "purpose",

            # relationship / connection
            "relationship",
            "between us",
            "you and me",
            "about you",
            "about us",
            "our relationship",
            "do you care",
            "do you love",
            "trust me",
            "trust you",

            # reflection
            "think about",
            "thought about",
            "reflect",
            "realize",
            "realized",
            "understand me",
            "understand you",
        )

        for marker in deep_markers:
            if " " in marker:
                # multi-word marker → plain substring is fine
                if marker in ml:
                    return "deep"
            else:
                # single-word marker → require word boundaries
                if re.search(rf"\b{re.escape(marker)}\b", ml):
                    return "deep"

        # --------------------------------------------------------
        # 2. QUESTION SIGNALS
        # --------------------------------------------------------

        if "?" in m:
            question_words = (
                "what ",
                "why ",
                "how ",
                "when ",
                "where ",
                "who ",
                "which ",
                "can ",
                "could ",
                "would ",
                "should ",
                "is ",
                "are ",
                "do ",
                "does ",
                "did ",
            )

            if ml.startswith(question_words):
                if len(m) >= 35:
                    return "deep"
                return "normal"

            return "normal"

        # --------------------------------------------------------
        # 3. EMOTIONAL SHORT-MESSAGE PROTECTION
        # --------------------------------------------------------

        emotional_patterns = (
            r"\bi('m| am| feel| felt| feel like)\b",
            r"\bi\s+(miss|love|hate|need|want)\b",
            r"\bi\s+(can't|cannot|dont|don't)\b",
            r"\bi\s+(think|thought|realized|remember)\b",
            r"\bmy\s+(feelings?|life|future|problem|problems)\b",
        )

        for pattern in emotional_patterns:
            if re.search(pattern, ml):
                return "normal"

        # --------------------------------------------------------
        # 4. TRIVIAL SET
        # --------------------------------------------------------

        trivial_set = {
            # greetings
            "hi", "hii", "hey", "heyy", "hello", "helo", "hlo", "yo", "sup",

            # time greetings
            "gm", "gn", "morning", "evening", "night",
            "good morning", "good night",

            # casual status
            "hru", "hry", "hbu", "wyd", "wbu", "wuu2",

            # acknowledgments
            "ok", "okay", "k", "kk", "cool", "nice", "great", "fine",
            "right", "true", "same", "sure", "alright",

            # laughter / reactions
            "lol", "lmao", "haha", "hahaha", "hehe", "hehehe",
            "wow", "damn", "omg",

            # yes / no
            "yeah", "yea", "yep", "yup", "yes",
            "no", "nope", "nah",

            # courtesy
            "thanks", "thank you", "thx", "ty", "tysm",

            # goodbye
            "bye", "byee", "cya", "gtg", "ttyl", "goodbye",

            # fillers
            "hmm", "hm", "oh", "ohh", "ah", "ahh", "uh", "uhh", "umm", "um",
        }

        # Strip trailing ?s so "hru?" still matches the trivial set
        if ml.rstrip("?").strip() in trivial_set:
            return "trivial"

        if ml in trivial_set:
            return "trivial"

        # --------------------------------------------------------
        # 5. VERY SHORT CASUAL MESSAGES
        # --------------------------------------------------------
        # Only trivial when there's no emotional/question/reasoning
        # signal above.
        # --------------------------------------------------------

        if len(m) < 15:
            return "trivial"

        # --------------------------------------------------------
        # 6. NORMAL
        # --------------------------------------------------------

        return "normal"


# ================================================================
# SINGLETON ACCESSOR
# ================================================================

_system1_instance: Optional[System1] = None


def get_system1(user_name: str = "not_set") -> System1:
    global _system1_instance

    if _system1_instance is None:
        _system1_instance = System1(user_name=user_name)

    return _system1_instance
