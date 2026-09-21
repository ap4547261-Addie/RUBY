from datetime import datetime
from memory import database


# ============================================================
# RUBY CURIOSITY ENGINE
# ============================================================
#
# IMPORTANT:
#
# This module NEVER contains questions Ruby must ask.
#
# It only tracks:
#
#   - what Ruby noticed
#   - what Ruby knows
#   - what Ruby does not know
#   - what Ruby is interested in
#   - what Ruby does not understand
#   - why something is worth exploring
#
# Ruby's language model creates the actual question.
#
# Example:
#
# User:
#   "I went to Delhi yesterday."
#
# Curiosity:
#
#   subject: Delhi trip
#   unknowns:
#       reason
#       activity
#       companions
#       experience
#
# Ruby's LLM may then naturally ask:
#
#   "Why'd you go to Delhi?"
#
# That sentence does NOT exist in this file.
# ============================================================


class Curiosity:

    MAX_INTERESTS = 30
    MAX_UNKNOWN = 40
    MAX_UNCERTAINTIES = 20
    MAX_HISTORY = 30

    INTEREST_THRESHOLD = 0.55
    ASK_THRESHOLD = 0.70

    def __init__(self):

        self._ensure_table()

        # Things Ruby noticed and may want to explore.
        self._interests = []

        # Information Ruby knows is missing.
        self._unknowns = []

        # Things Ruby genuinely does not understand.
        self._uncertainties = []

        # Things recently explored.
        self._history = []

    # ========================================================
    # DATABASE
    # ========================================================

    def _ensure_table(self):

        try:
            database.execute("""
                CREATE TABLE IF NOT EXISTS ruby_curiosity (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    category TEXT,
                    subject TEXT,
                    detail TEXT,
                    strength REAL,
                    reason TEXT,
                    status TEXT,
                    created_at TEXT
                )
            """)
        except Exception:
            pass

    # ========================================================
    # NOTICE
    # ========================================================
    #
    # Called after Ruby receives a message.
    #
    # It does NOT decide what Ruby should say.
    #
    # It only notices potentially meaningful information.
    # ========================================================

    def notice(self, message):

        if not message:
            return

        text = str(message).strip()

        if not text:
            return

        lower = text.lower()

        # ----------------------------------------------------
        # PERSONAL INFORMATION
        # ----------------------------------------------------

        self._notice_person_information(text, lower)

        # ----------------------------------------------------
        # PEOPLE
        # ----------------------------------------------------

        self._notice_people(text, lower)

        # ----------------------------------------------------
        # PLACES / MOVEMENT
        # ----------------------------------------------------

        self._notice_places(text, lower)

        # ----------------------------------------------------
        # ACTIVITIES / EVENTS
        # ----------------------------------------------------

        self._notice_events(text, lower)

        # ----------------------------------------------------
        # FUTURE PLANS
        # ----------------------------------------------------

        self._notice_plans(text, lower)

        # ----------------------------------------------------
        # EMOTIONAL INFORMATION
        # ----------------------------------------------------

        self._notice_emotion(text, lower)

        # ----------------------------------------------------
        # STORIES / EXPERIENCES
        # ----------------------------------------------------

        self._notice_experience(text, lower)

        # ----------------------------------------------------
        # BELIEFS / OPINIONS
        # ----------------------------------------------------

        self._notice_beliefs(text, lower)

    # ========================================================
    # PERSONAL INFORMATION
    # ========================================================

    def _notice_person_information(self, text, lower):

        if (
            "my name is " in lower
            or "call me " in lower
            or lower.startswith("i'm ")
        ):
            self._resolve_unknown(
                category="person",
                subject="identity",
            )

        if any(
            phrase in lower
            for phrase in (
                "i study",
                "i'm studying",
                "i am studying",
                "i work",
                "my job",
                "my college",
                "my school",
            )
        ):
            self._resolve_unknown(
                category="person",
                subject="what they do",
            )

        if any(
            phrase in lower
            for phrase in (
                "my family",
                "my mother",
                "my mom",
                "my father",
                "my dad",
                "my brother",
                "my sister",
                "my parents",
            )
        ):
            self._resolve_unknown(
                category="person",
                subject="family",
            )

            self._add_interest(
                category="person",
                subject="family",
                reason="The person mentioned someone important in their family.",
                strength=0.62,
            )

        if any(
            phrase in lower
            for phrase in (
                "my friend",
                "my friends",
                "my best friend",
            )
        ):
            self._resolve_unknown(
                category="person",
                subject="friends",
            )

            self._add_interest(
                category="person",
                subject="friendship",
                reason="The person mentioned someone they know.",
                strength=0.62,
            )

    # ========================================================
    # PEOPLE
    # ========================================================

    def _notice_people(self, text, lower):

        relationship_words = (
            "friend",
            "brother",
            "sister",
            "mother",
            "mom",
            "father",
            "dad",
            "cousin",
            "uncle",
            "aunt",
            "classmate",
            "teacher",
            "colleague",
            "girlfriend",
            "boyfriend",
        )

        if any(word in lower for word in relationship_words):

            self._add_interest(
                category="people",
                subject="person mentioned",
                reason="Someone connected to the person appeared in the conversation.",
                strength=0.65,
            )

            self._add_unknown(
                category="people",
                subject="the relationship or context",
                reason="Ruby noticed a person but does not know the full context.",
                strength=0.58,
            )

    # ========================================================
    # PLACES
    # ========================================================

    def _notice_places(self, text, lower):

        movement_words = (
            "i went to",
            "i'm going to",
            "i am going to",
            "i visited",
            "i've been to",
            "i was at",
            "i came from",
            "i traveled to",
            "i travelled to",
        )

        if any(phrase in lower for phrase in movement_words):

            self._add_interest(
                category="event",
                subject="place",
                reason="The person mentioned going somewhere.",
                strength=0.72,
            )

            self._add_unknown(
                category="event",
                subject="why they went there",
                reason="Ruby knows the destination but not the reason.",
                strength=0.65,
            )

            self._add_unknown(
                category="event",
                subject="what happened there",
                reason="Ruby knows about the trip but not the experience.",
                strength=0.60,
            )

            self._add_unknown(
                category="event",
                subject="who was there",
                reason="Ruby does not know who accompanied them.",
                strength=0.48,
            )

    # ========================================================
    # EVENTS
    # ========================================================

    def _notice_events(self, text, lower):

        event_markers = (
            "yesterday",
            "today",
            "last night",
            "last week",
            "this morning",
            "this evening",
            "one time",
            "recently",
            "then",
            "after that",
        )

        if any(marker in lower for marker in event_markers):

            self._add_interest(
                category="event",
                subject="recent experience",
                reason="The person appears to be describing something that happened.",
                strength=0.60,
            )

            self._add_unknown(
                category="event",
                subject="what happened",
                reason="Ruby does not have the complete event yet.",
                strength=0.55,
            )

    # ========================================================
    # PLANS
    # ========================================================

    def _notice_plans(self, text, lower):

        future_markers = (
            "i want to",
            "i'm planning to",
            "i am planning to",
            "i'm going to",
            "i am going to",
            "i hope to",
            "i'd like to",
            "i would like to",
            "someday",
            "in the future",
        )

        if any(marker in lower for marker in future_markers):

            self._add_interest(
                category="future",
                subject="their plan",
                reason="The person revealed something they want to do.",
                strength=0.70,
            )

            self._add_unknown(
                category="future",
                subject="why they want it",
                reason="Ruby knows the plan but not what motivates it.",
                strength=0.55,
            )

    # ========================================================
    # EMOTION
    # ========================================================

    def _notice_emotion(self, text, lower):

        emotion_markers = (
            "i'm happy",
            "i am happy",
            "i'm sad",
            "i am sad",
            "i'm angry",
            "i am angry",
            "i'm scared",
            "i am scared",
            "i'm worried",
            "i am worried",
            "i feel",
            "i felt",
        )

        if any(marker in lower for marker in emotion_markers):

            self._add_interest(
                category="emotion",
                subject="their emotional experience",
                reason="The person revealed a feeling.",
                strength=0.68,
            )

    # ========================================================
    # EXPERIENCE
    # ========================================================

    def _notice_experience(self, text, lower):

        experience_markers = (
            "when i was",
            "when i used to",
            "growing up",
            "as a child",
            "my childhood",
            "years ago",
            "back then",
            "i remember",
        )

        if any(marker in lower for marker in experience_markers):

            self._add_interest(
                category="experience",
                subject="past experience",
                reason="The person revealed something from their past.",
                strength=0.66,
            )

            self._add_unknown(
                category="experience",
                subject="what the experience meant to them",
                reason="Ruby noticed a past experience but does not yet know its meaning.",
                strength=0.55,
            )

    # ========================================================
    # BELIEFS
    # ========================================================

    def _notice_beliefs(self, text, lower):

        belief_markers = (
            "i believe",
            "i think",
            "in my opinion",
            "i feel like people",
            "i don't believe",
            "i dont believe",
        )

        if any(marker in lower for marker in belief_markers):

            self._add_interest(
                category="belief",
                subject="their perspective",
                reason="The person expressed a belief or opinion.",
                strength=0.62,
            )

    # ========================================================
    # ADD INTEREST
    # ========================================================

    def _add_interest(
        self,
        category,
        subject,
        reason,
        strength=0.5,
    ):

        strength = self._clamp(strength)

        for item in self._interests:

            if (
                item["category"] == category
                and item["subject"].lower() == subject.lower()
            ):
                item["strength"] = max(
                    item["strength"],
                    strength,
                )
                item["reason"] = reason
                return

        self._interests.append({
            "category": category,
            "subject": subject,
            "reason": reason,
            "strength": strength,
            "created_at": datetime.utcnow().isoformat(),
        })

        self._trim(self._interests, self.MAX_INTERESTS)

    # ========================================================
    # ADD UNKNOWN
    # ========================================================

    def _add_unknown(
        self,
        category,
        subject,
        reason,
        strength=0.5,
    ):

        strength = self._clamp(strength)

        for item in self._unknowns:

            if (
                item["category"] == category
                and item["subject"].lower() == subject.lower()
            ):
                item["strength"] = max(
                    item["strength"],
                    strength,
                )
                item["reason"] = reason
                return

        self._unknowns.append({
            "category": category,
            "subject": subject,
            "reason": reason,
            "strength": strength,
            "created_at": datetime.utcnow().isoformat(),
        })

        self._trim(self._unknowns, self.MAX_UNKNOWN)

    # ========================================================
    # UNCERTAINTY
    # ========================================================
    #
    # Used when Ruby genuinely does not understand something.
    #
    # Example:
    #
    # User:
    #   "I finally talked to Zayn."
    #
    # Ruby does not know who Zayn is.
    #
    # Another layer can call:
    #
    # curiosity.notice_uncertainty(
    #     "Zayn",
    #     "Ruby does not know who Zayn is."
    # )
    #
    # The LLM then generates the clarification naturally.
    # ========================================================

    def notice_uncertainty(
        self,
        subject,
        reason="Ruby does not understand this yet.",
        strength=0.80,
    ):

        if not subject:
            return

        subject = str(subject).strip()

        if not subject:
            return

        strength = self._clamp(strength)

        for item in self._uncertainties:

            if item["subject"].lower() == subject.lower():

                item["strength"] = max(
                    item["strength"],
                    strength,
                )

                item["reason"] = reason

                return

        self._uncertainties.append({
            "subject": subject,
            "reason": reason,
            "strength": strength,
            "created_at": datetime.utcnow().isoformat(),
        })

        self._trim(
            self._uncertainties,
            self.MAX_UNCERTAINTIES,
        )

    # ========================================================
    # STRONGEST CURIOSITY
    # ========================================================

    def strongest(self):

        candidates = []

        # Uncertainty gets priority because pretending to
        # understand is worse than asking for clarification.

        for item in self._uncertainties:

            if item["strength"] >= self.INTEREST_THRESHOLD:

                candidates.append({
                    "type": "uncertainty",
                    "category": "clarification",
                    "subject": item["subject"],
                    "reason": item["reason"],
                    "strength": item["strength"],
                })

        # Missing information.

        for item in self._unknowns:

            if item["strength"] >= self.INTEREST_THRESHOLD:

                candidates.append({
                    "type": "unknown",
                    "category": item["category"],
                    "subject": item["subject"],
                    "reason": item["reason"],
                    "strength": item["strength"],
                })

        # General interests.

        for item in self._interests:

            if item["strength"] >= self.INTEREST_THRESHOLD:

                candidates.append({
                    "type": "interest",
                    "category": item["category"],
                    "subject": item["subject"],
                    "reason": item["reason"],
                    "strength": item["strength"],
                })

        if not candidates:
            return None

        candidates.sort(
            key=lambda item: item["strength"],
            reverse=True,
        )

        return candidates[0]

    # ========================================================
    # SHOULD ASK
    # ========================================================

    def should_ask(self):

        strongest = self.strongest()

        if not strongest:
            return False

        return strongest["strength"] >= self.ASK_THRESHOLD

    # ========================================================
    # GET ASK CONTEXT
    # ========================================================
    #
    # This is what gets passed toward the decision/LLM layer.
    #
    # Notice that there is NO question here.
    # ========================================================

    def get_ask_context(self):

        strongest = self.strongest()

        if not strongest:
            return None

        return {
            "type": strongest["type"],
            "category": strongest["category"],
            "subject": strongest["subject"],
            "reason": strongest["reason"],
            "strength": strongest["strength"],
            "instruction": (
                "Ruby wants to understand this naturally. "
                "Generate a conversational question from the "
                "current conversation. Do not use a predefined "
                "question."
            ),
        }

    # ========================================================
    # RESOLVE UNKNOWN
    # ========================================================

    def _resolve_unknown(
        self,
        category,
        subject,
    ):

        remaining = []

        for item in self._unknowns:

            same_category = (
                item["category"] == category
            )

            same_subject = (
                item["subject"].lower()
                == subject.lower()
            )

            if same_category and same_subject:
                continue

            remaining.append(item)

        self._unknowns = remaining

    # ========================================================
    # MARK UNDERSTOOD
    # ========================================================

    def mark_understood(self, subject):

        if not subject:
            return

        subject = str(subject).lower()

        self._uncertainties = [
            item
            for item in self._uncertainties
            if item["subject"].lower() != subject
        ]

    # ========================================================
    # MARK EXPLORED
    # ========================================================

    def mark_explored(
        self,
        subject,
        category=None,
    ):

        if not subject:
            return

        subject = str(subject).strip()

        self._history.append({
            "subject": subject,
            "category": category,
            "created_at": datetime.utcnow().isoformat(),
        })

        self._trim(
            self._history,
            self.MAX_HISTORY,
        )

        # Lower curiosity rather than instantly deleting it.
        # Ruby can become curious again later if new context
        # makes the subject relevant.

        for item in self._interests:

            if item["subject"].lower() == subject.lower():

                item["strength"] *= 0.35

        for item in self._unknowns:

            if item["subject"].lower() == subject.lower():

                item["strength"] *= 0.25

    # ========================================================
    # INCREASE
    # ========================================================

    def increase(
        self,
        subject,
        amount=0.15,
        reason="",
        category="general",
    ):

        if not subject:
            return

        for item in self._interests:

            if item["subject"].lower() == str(subject).lower():

                item["strength"] = self._clamp(
                    item["strength"] + amount
                )

                return

        self._add_interest(
            category=category,
            subject=str(subject),
            reason=reason,
            strength=amount,
        )

    # ========================================================
    # RECENT HISTORY
    # ========================================================

    def recent_history(self):

        return list(self._history)

    # ========================================================
    # DESCRIBE
    # ========================================================

    def describe(self):

        strongest = self.strongest()

        return {
            "strongest": strongest,
            "interests": list(self._interests),
            "unknowns": list(self._unknowns),
            "uncertainties": list(self._uncertainties),
            "history": list(self._history),
        }

    # ========================================================
    # PEEK
    # ========================================================

    def peek_interests(self):
        return list(self._interests)

    def peek_unknowns(self):
        return list(self._unknowns)

    def peek_uncertainties(self):
        return list(self._uncertainties)

    # ========================================================
    # CLEAR
    # ========================================================

    def clear_live(self):

        self._interests.clear()

    # ========================================================
    # WIPE
    # ========================================================

    def wipe(self):

        self._interests.clear()
        self._unknowns.clear()
        self._uncertainties.clear()
        self._history.clear()

    # ========================================================
    # HELPERS
    # ========================================================

    @staticmethod
    def _clamp(value):

        return max(
            0.0,
            min(1.0, float(value)),
        )

    @staticmethod
    def _trim(items, maximum):

        while len(items) > maximum:
            items.pop(0)
