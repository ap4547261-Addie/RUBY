from cognition.attention import Attention
from cognition.appraisal import Appraisal
from cognition.anticipation import Anticipation
from cognition.decision import Decision


class CognitionEngine:
    """
    Pipeline that runs BEFORE the LLM generates a reply:

    message → attention → appraisal → anticipation → decision → LLM

    No caps. Every stage produces unbounded values.
    """

    def __init__(self, user_name="not_set"):
        self.user_name = user_name
        self.attention = Attention()
        self.appraisal = Appraisal()
        self.anticipation = Anticipation()
        self.decision = Decision()
        self._last_trace = None

    def process(self, user_message, context=None):
        context = context or {}

        focused_on = self.attention.attend(user_message, context)
        appraisal = self.appraisal.appraise(user_message, focused_on, context)
        prediction = self.anticipation.anticipate(user_message, appraisal, context)
        decision = self.decision.decide(focused_on, appraisal, prediction, context)

        trace = {
            "focused_on": focused_on,
            "appraisal": appraisal,
            "prediction": prediction,
            "decision": decision,
        }
        self._last_trace = trace
        return trace

    def describe(self, trace=None):
        trace = trace or self._last_trace
        if not trace:
            return ""

        lines = []
        lines.append(self.attention.describe(trace.get("focused_on", {})))
        lines.append(self.appraisal.describe(trace.get("appraisal", {})))
        ant = self.anticipation.describe(trace.get("prediction", {}))
        if ant:
            lines.append(ant)
        lines.append(self.decision.describe(trace.get("decision", {})))

        return " ".join(l for l in lines if l)

    def last_trace(self):
        return self._last_trace

    def wipe(self):
        self._last_trace = None
