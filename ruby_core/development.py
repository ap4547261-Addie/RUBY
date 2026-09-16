from datetime import datetime
from ruby_core.internal_state import InternalState


class Development:
    """
    Ticks Ruby's internal state over time.
    No caps, no floors, no rate limits — pure open-ended evolution.
    """

    def __init__(self, user_name="not_set"):
        self.user_name = user_name
        self.state = InternalState(user_name=user_name)

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

        # energy regenerates proportionally to time passed — no cap
        if hours_passed > 0:
            deltas["energy"] = hours_passed * 1.0

        # irritation decays proportionally — no floor except reaching 0
        if s["irritation"] > 0:
            decay = s["irritation"] * 0.1 * hours_passed
            deltas["irritation"] = -min(s["irritation"], decay)

        # tension decays slower
        if s["tension"] > 0:
            decay = s["tension"] * 0.05 * hours_passed
            deltas["tension"] = -min(s["tension"], decay)

        # warmth cools only during long absence — no floor
        if s["warmth"] > 0 and hours_passed > 12:
            decay = s["warmth"] * 0.02 * hours_passed
            deltas["warmth"] = -min(s["warmth"], decay)

        if deltas:
            self.state.change(**deltas)

    def on_message(self, user_message, ruby_reply, trust, attachment):
        deltas = {}
        text = user_message.lower()
        word_count = len(user_message.split())

        # --- warmth grows continuously from trust + attachment, no cap ---
        deltas["warmth"] = (trust * 0.02) + (attachment * 0.05)

        # --- energy cost per message ---
        if word_count > 20:
            deltas["energy"] = -1.0
        elif word_count > 10:
            deltas["energy"] = -0.3
        else:
            deltas["energy"] = -0.1

        # --- irritation from rudeness ---
        if any(w in text for w in ["shut up", "stupid", "dumb", "idiot", "hate you"]):
            deltas["irritation"] = +2.5

        # --- tension from pushy behavior ---
        if any(w in text for w in ["send me", "show me now", "do this for me", "you must", "you have to"]):
            deltas["tension"] = +1.5

        # --- calm from honesty ---
        if any(m in text for m in ["i feel", "i'm scared", "i lost", "i miss", "i love you", "i'm sad"]):
            deltas["irritation"] = -1.0
            deltas["tension"] = -0.5

        self.state.change(**deltas)

    def describe(self):
        return self.state.describe()

    def wipe(self):
        self.state.wipe()
