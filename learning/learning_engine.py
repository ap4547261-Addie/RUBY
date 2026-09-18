from learning.experience_learning import ExperienceLearning
from learning.preference_learning import PreferenceLearning
from learning.behavior_learning import BehaviorLearning


class LearningEngine:
    """
    Ties the three learning subsystems together.
    Runs at the START of each message (evaluate last prediction)
    and AFTER generation (store prediction, learn preferences).
    """

    def __init__(self, user_name="not_set"):
        self.user_name = user_name
        self.experience = ExperienceLearning(user_name=user_name)
        self.preference = PreferenceLearning(user_name=user_name)
        self.behavior = BehaviorLearning(user_name=user_name)

    # -------------------------
    # Called at the START of each turn
    # -------------------------
    def pre_turn(self, user_message: str):
        """
        Evaluate the previous prediction against the current message.
        """
        try:
            err = self.experience.evaluate_last(user_message)
            if err:
                # feed back into behavior learning
                # we don't have the exact intent here — a future version can
                # store the previous intent and use it properly
                direction = "good" if err["direction"] == "too_negative" else "bad"
                # (behavior update handled in post_turn with real intent)
        except Exception as e:
            print(f"⚠️ learning.pre_turn failed: {e}")

    # -------------------------
    # Called AFTER generation
    # -------------------------
    def post_turn(self, trace: dict, user_message: str, reply: str, emotions: dict):
        """
        Store the prediction, attach the reply, learn preferences,
        update behavior weights.
        """
        try:
            self.experience.store_prediction(trace, user_message)
            self.experience.store_reply(reply)
        except Exception as e:
            print(f"⚠️ experience storage failed: {e}")

        try:
            self.preference.learn_from(user_message, emotions)
        except Exception as e:
            print(f"⚠️ preference learning failed: {e}")

        # behavior: use the last error direction + current intent
        try:
            decision = trace.get("decision", {})
            intent = decision.get("intent", "")
            tone = decision.get("tone", "")
            if intent and tone:
                # check the last error for this user (rough heuristic)
                errors = self.experience.get_errors(limit=1)
                if errors:
                    _, _, _, _, direction = errors[0]
                    outcome = "good" if direction == "too_negative" else "bad" if direction == "confirmed" else "neutral"
                    self.behavior.record_outcome(intent, tone, outcome)
        except Exception as e:
            print(f"⚠️ behavior learning failed: {e}")

    # -------------------------
    # Read helpers
    # -------------------------
    def describe(self):
        parts = []
        pref = self.preference.describe()
        if pref:
            parts.append(pref)
        beh = self.behavior.describe()
        if beh:
            parts.append(beh)
        errs = self.experience.error_summary()
        if errs:
            parts.append("Prediction errors: " + ", ".join(f"{k} x{v}" for k, v in errs.items()))
        return " ".join(parts) if parts else ""

    def error_summary(self):
        return self.experience.error_summary()

    def recent_errors(self, limit=10):
        return self.experience.get_errors(limit=limit)

    def preferences(self):
        return self.preference.get_all()

    def best_behaviors(self, limit=5):
        return self.behavior.best_intents(limit=limit)

    def worst_behaviors(self, limit=5):
        return self.behavior.worst_intents(limit=limit)

    def wipe(self):
        self.experience.wipe()
        self.preference.wipe()
        self.behavior.wipe()
