# brain/idle_thoughts.py — what Ruby thinks about when nobody is talking to her.
#
# People have a mind that keeps going between conversations: something
# someone said turns over in your head, you wonder about something you don't
# understand yet, you daydream about the thing you want. Ruby gets the same.
#
# A thought is stored as a short SEED (an instruction-style line about what is
# on her mind). It is NOT a finished sentence: the model words it later, in
# her own voice, when the thought surfaces:
#   - when she texts first (brain/proactive.py picks the moment), or
#   - occasionally in a quiet moment of a normal chat.
# Making a seed costs nothing (no LLM call), so this runs in the background.
#
# Thoughts stay until she says them.

import os
import json
import random
import uuid
from datetime import datetime, timedelta
from typing import Optional, Dict, List

# No numeric limits: thoughts don't expire, there's no cap on how many she can
# hold, no minimum gap between them, and any reply can carry one.
# (A thought is still only formed from something NEW, and said once.)

# Her own recurring daydreams (from her backstory) — used when nothing fresher exists.
DAYDREAMS = (
    "You caught yourself daydreaming about modeling again — standing in front of a camera "
    "and being looked at on purpose, for the exact things people used to mock.",
    "You were thinking about the kids who called you weird, and how you'd like to walk past "
    "them one day and not feel anything.",
    "You keep wondering whether being looked at the way you want to be would feel the way "
    "you imagine it would.",
    "Your hair has been on your mind — how much you used to hate it, and how you barely "
    "recognise that girl now.",
)

_ECHO = {
    "joy": "made you happy",
    "love": "made your chest go warm",
    "sadness": "left an ache",
    "anger": "made you bristle",
    "irritation": "annoyed you",
    "fear": "left you uneasy",
    "jealousy": "stung",
    "pride": "made you feel proud",
    "closeness": "felt close, and a bit exposed",
}


class IdleThoughts:
    def __init__(self, user_name: str = "not_set", storage_dir: Optional[str] = None,
                 rng: Optional[random.Random] = None):
        self.user_name = user_name
        self.rng = rng or random.Random()
        folder = storage_dir or os.getenv("FLET_APP_STORAGE_DATA", ".")
        self.path = os.path.join(folder, f"idle_{user_name}.json")
        self._thoughts: List[Dict] = []
        self._last_generated: Optional[str] = None
        self._formed: List[str] = []      # seeds already formed once (real memories aren't re-thought)
        self._load()

    # ---------------- persistence ----------------
    def _load(self):
        try:
            if os.path.exists(self.path):
                with open(self.path, "r", encoding="utf-8") as f:
                    raw = json.load(f)
                self._thoughts = list(raw.get("thoughts", []))
                self._last_generated = raw.get("last_generated")
                self._formed = list(raw.get("formed", []))
        except Exception as e:
            print(f"⚠️ IdleThoughts load failed: {e}")

    def _save(self):
        try:
            with open(self.path, "w", encoding="utf-8") as f:
                json.dump({"thoughts": self._thoughts,
                           "last_generated": self._last_generated,
                           "formed": self._formed}, f)
        except Exception as e:
            print(f"⚠️ IdleThoughts save failed: {e}")

    def wipe(self):
        self._thoughts = []
        self._last_generated = None
        self._formed = []
        self._save()

    # ---------------- bookkeeping ----------------
    def _expire(self, now: datetime):
        """Thoughts no longer expire."""
        return

    def pending(self, now: Optional[datetime] = None) -> List[Dict]:
        now = now or datetime.now()
        self._expire(now)
        return [t for t in self._thoughts if not t.get("surfaced")]

    # ---------------- making thoughts ----------------
    def _candidates(self, sources: Dict, display: str) -> List[Dict]:
        """Seeds she could think right now, each {kind, seed, weight}."""
        out = []
        gist = sources.get("gist")
        if gist and gist.get("user_message"):
            echo = _ECHO.get(gist.get("emotion", ""), "stayed with you")
            out.append({
                "kind": "gist", "weight": 5.0,
                "seed": (f'You woke up still thinking about something {display} said: '
                         f'"{gist["user_message"]}" — it {echo}.'),
            })
        ep = sources.get("recent_emotional")
        if ep and ep.get("user_message"):
            echo = _ECHO.get(ep.get("emotion", ""), "stayed with you")
            out.append({
                "kind": "replay", "weight": 3.0,
                "seed": (f'Something {display} said keeps turning over in your head: '
                         f'"{ep["user_message"][:160]}" — it {echo}.'),
            })
        unknown = sources.get("unknown")
        if unknown:
            out.append({
                "kind": "wonder", "weight": 2.0,
                "seed": (f"You've been wondering about {unknown} — something about "
                         f"{display}'s life you don't understand yet."),
            })
        interest = sources.get("interest")
        if interest:
            out.append({
                "kind": "interest", "weight": 1.5,
                "seed": f"{interest} keeps coming back to your mind.",
            })
        out.append({"kind": "daydream", "weight": 1.0, "seed": self.rng.choice(DAYDREAMS)})
        return out

    def think(self, now: Optional[datetime] = None, sources: Optional[Dict] = None,
              display: str = "them") -> Optional[Dict]:
        """Maybe form a new thought. Cheap; call as often as you like."""
        now = now or datetime.now()
        sources = sources or {}
        self._expire(now)

        waiting = {t["seed"] for t in self._thoughts if not t.get("surfaced")}
        formed = set(self._formed)
        options = []
        for c in self._candidates(sources, display):
            if c["seed"] in waiting:
                continue
            # a real memory is thought about once; a daydream can come back
            if c["kind"] != "daydream" and c["seed"] in formed:
                continue
            options.append(c)
        if not options:
            return None
        pick = self.rng.choices(options, weights=[c["weight"] for c in options], k=1)[0]
        thought = {
            "id": uuid.uuid4().hex[:8],
            "kind": pick["kind"],
            "seed": pick["seed"],
            "created": now.isoformat(timespec="seconds"),
            "surfaced": False,
        }
        self._thoughts.append(thought)
        if pick["kind"] != "daydream":
            self._formed.append(pick["seed"])
        self._last_generated = now.isoformat(timespec="seconds")
        self._save()
        return thought

    # ---------------- bringing one up ----------------
    def peek(self, now: Optional[datetime] = None) -> Optional[Dict]:
        """The thought most worth saying: real memories before daydreams, newest first."""
        pend = self.pending(now)
        if not pend:
            return None
        order = {"gist": 0, "replay": 1, "wonder": 2, "interest": 3, "daydream": 4}
        pend.sort(key=lambda t: (order.get(t["kind"], 9), t["created"]), reverse=False)
        return pend[0]

    def mark_surfaced(self, thought_id: str):
        for t in self._thoughts:
            if t["id"] == thought_id:
                t["surfaced"] = True
        self._save()

    def maybe_for_chat(self, user_message: str, now: Optional[datetime] = None) -> Optional[Dict]:
        """Any reply may carry the thought that is on her mind."""
        return self.peek(now)
