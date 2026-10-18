# ruby_core/circadian.py — Ruby's daily energy rhythm.
#
# A person is not equally sharp at every hour, whatever happened in the chat.
# This gives Ruby a body clock: low in the small hours, groggy on waking,
# sharpest in the afternoon/evening (she is a bit of a night owl), winding
# down late. It is a pure function of the clock — no storage, no LLM.
#
# The result is blended with her message-driven energy (InternalState) so a
# long draining chat still tires her, but 3 AM is always a bad time to be bright.

import math
from datetime import datetime
from typing import Optional

PEAK_HOUR = 17.0      # most alert around 5 PM
TROUGH_HOUR = 4.5     # least alert in the small hours
FLOOR = 0.2           # even at the worst hour she keeps this share of her energy


def circadian_level(now: Optional[datetime] = None) -> float:
    """0.0 (dead tired) .. 1.0 (sharpest) from the hour of day."""
    now = now or datetime.now()
    h = now.hour + now.minute / 60.0
    # cosine with its top at PEAK_HOUR; trough ends up ~12h later (05:00), close to TROUGH_HOUR
    x = math.cos((h - PEAK_HOUR) / 24.0 * 2 * math.pi)
    level = 0.5 + 0.5 * x
    # small post-lunch dip around 14:30
    level -= 0.08 * math.exp(-((h - 14.5) ** 2) / 1.5)
    return max(0.0, min(1.0, level))


def effective_energy(base_energy: float, now: Optional[datetime] = None) -> float:
    """Message-driven energy (0..1) scaled by the body clock: a drained Ruby is
    tired at any hour, and even a rested Ruby is not bright at 3 AM."""
    base = max(0.0, min(1.0, float(base_energy)))
    return base * (FLOOR + (1 - FLOOR) * circadian_level(now))


def phase(now: Optional[datetime] = None) -> str:
    """A short plain description of where she is in her day (for her prompt)."""
    now = now or datetime.now()
    h = now.hour + now.minute / 60.0
    if h < 5:
        return ("it's the dead of night — your body wants to be asleep; you're foggy, "
                "slow, and a little softer and more honest than usual")
    if h < 7:
        return "it's barely morning — you're half asleep and not a morning person"
    if h < 10:
        return "it's early — you're groggy and need time to wake up; short answers, low patience"
    if h < 13:
        return "the morning has warmed you up — you're getting clearer and more yourself"
    if h < 15.5:
        return "it's the sleepy part of the afternoon — a bit slow, easily distracted"
    if h < 20:
        return "you're at your sharpest and liveliest right now"
    if h < 23:
        return "it's evening — you're relaxed and a little more open"
    return "it's late — you're getting tired and quieter, your guard slipping a little"


def label(base_energy: float, now: Optional[datetime] = None) -> str:
    """tired / ok / bright — used to bucket her mood."""
    e = effective_energy(base_energy, now)
    if e < 0.33:
        return "tired"
    if e > 0.75:
        return "bright"
    return "ok"
