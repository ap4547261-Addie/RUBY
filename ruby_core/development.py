# ruby_core/development.py
from datetime import datetime
from ruby_core.internal_state import InternalState

try:
    from ruby_core.goals import Goals
    GOALS_AVAILABLE = True
except Exception as e:
    print(f"⚠️ Goals not available: {e}")
    GOALS_AVAILABLE = False
    Goals = None


class Development:
    """
    Ticks Ruby's internal state over time.
    No caps, no floors, no rate limits — pure open-ended evolution.
    """

    def __init__(self, user_name="not_set"):
        self.user_name = user_name
        self.state = InternalState(user_name=user_name)

        if GOALS_AVAILABLE:
            try:
                self.goals = Goals(user_name=user_name)
            except Exception as e:
                print(f"⚠️ Goals init failed: {e}")
                self.goals = None
        else:
            self.goals = None

    def _apply_deltas(self, deltas):
        """Apply deltas directly using InternalState.adjust(). No caps, no floors."""
        for key, delta in deltas.items():
            try:
                self.state.adjust(key, delta)
            except Exception as e:
                print(f"⚠️ development._apply_deltas failed for {key}: {e}")

    def tick(self):
        s = self.state.get()
        last = s.get("last_updated")

        hours_passed = 0.0
        if last:
            try:
                last_dt = datetime.fromisoformat(last)
                hours_passed = max(0.0, (datetime.now() - last_dt).total_seconds() / 3600)
            except Exception:
                hours_passed = 0.0

        deltas = {}

        if hours_passed > 0:
            deltas["energy"] = hours_passed * 1.0

        if s["irritation"] > 0:
            decay = s["irritation"] * 0.1 * hours_passed
            deltas["irritation"] = -min(s["irritation"], decay)

        if s["tension"] > 0:
            decay = s["tension"] * 0.05 * hours_passed
            deltas["tension"] = -min(s["tension"], decay)

        if s["warmth"] > 0 and hours_passed > 12:
            decay = s["warmth"] * 0.02 * hours_passed
            deltas["warmth"] = -min(s["warmth"], decay)

        if deltas:
            self._apply_deltas(deltas)

    def on_message(self, user_message, ruby_reply, trust, attachment):
        deltas = {}
        text = user_message.lower()
        word_count = len(user_message.split())

        deltas["warmth"] = (trust * 0.02) + (attachment * 0.05)

        if word_count > 20:
            deltas["energy"] = -1.0
        elif word_count > 10:
            deltas["energy"] = -0.3
        else:
            deltas["energy"] = -0.1

        if any(w in text for w in ["shut up", "stupid", "dumb", "idiot", "hate you"]):
            deltas["irritation"] = +2.5

        if any(w in text for w in ["send me", "show me now", "do this for me", "you must", "you have to"]):
            deltas["tension"] = +1.5

        if any(m in text for m in ["i feel", "i'm scared", "i lost", "i miss", "i love you", "i'm sad"]):
            deltas["irritation"] = -1.0
            deltas["tension"] = -0.5

        self._apply_deltas(deltas)

    def describe(self):
        return self.state.describe()

    def wipe(self):
        self.state.wipe()

        if getattr(self, "goals", None) is not None:
            try:
                self.goals.wipe()
            except Exception as e:
                print(f"⚠️ goals.wipe failed: {e}")
