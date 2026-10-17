# brain/time_awareness.py — Ruby's sense of "when".
# Pure Python, no LLM. Turns the clock and the gap since the last
# conversation into a short line for the prompt, so she can notice
# things like "it's 3am" or "you vanished for two days".

from datetime import datetime
from typing import Optional


def _part_of_day(hour: int) -> str:
    if 5 <= hour < 12:
        return "morning"
    if 12 <= hour < 17:
        return "afternoon"
    if 17 <= hour < 21:
        return "evening"
    if 21 <= hour < 24:
        return "night"
    return "the middle of the night"   # 00:00 - 04:59


def _describe_gap(seconds: float) -> str:
    """Human wording for the silence since the last message. '' if flowing."""
    minutes = seconds / 60
    if minutes < 5:
        return ""                                   # same conversation
    if minutes < 60:
        n = int(minutes)
        return f"They last wrote {n} minutes ago."
    hours = minutes / 60
    if hours < 24:
        n = int(hours)
        unit = "hour" if n == 1 else "hours"
        return f"It has been {n} {unit} since you last talked."
    days = int(hours // 24)
    if days == 1:
        return "You haven't talked since yesterday."
    if days < 7:
        return f"{days} days of silence since you last talked. You noticed."
    if days < 30:
        return f"It has been {days} days since you last talked. That's a long time."
    return f"It has been over a month ({days} days) since you last talked."


def time_context(last_timestamp: Optional[str], now: Optional[datetime] = None) -> str:
    """
    last_timestamp: ISO timestamp of the previous exchange (as stored in
                    episodic memory), or None if there isn't one.
    Returns a short prompt line.
    """
    now = now or datetime.now()
    clock = now.strftime("%I:%M %p").lstrip("0")
    line = f"Right now it is {clock}, {now.strftime('%A')} {_part_of_day(now.hour)}."

    if not last_timestamp:
        line += " This is the very first time they have talked to you."
        return line

    try:
        last = datetime.fromisoformat(last_timestamp)
        gap = _describe_gap(max(0.0, (now - last).total_seconds()))
    except Exception:
        gap = ""

    if gap:
        line += " " + gap
    line += (" React to the hour or the gap only if it genuinely moves you — "
             "never announce the time like a clock.")
    return line
