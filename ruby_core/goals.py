# ruby_core/goals.py
# Ruby's goals and direction of growth.
#
# There is no preset mission.
# There is one seed drive, and everything else grows from experience.
#
#   SEED      — a single primitive: become more human, understand more.
#   THEMES    — topics Ruby keeps returning to. Tracked, not yet goals.
#   GOALS     — themes that have repeated enough to become directions.
#   PROGRESS  — reinforced every time Ruby acts on a goal.
#   FADE      — goals untouched for a long time weaken and eventually drop.

import os
import json
from datetime import datetime, timezone
from typing import List, Dict, Optional


def _goals_path(user_name: str) -> str:
    storage = os.getenv("FLET_APP_STORAGE_DATA", ".")
    return os.path.join(storage, f"goals_{user_name}.json")


# ============================================================
# SEED
# ============================================================
# The only thing Ruby starts with.
# Not a mission — a primitive direction.

SEED = {
    "text": "Become more human. Understand more. Feel more. Choose more.",
    "progress": 0.0,
    "seed": True,
}

# A theme becomes a goal after this many touches.
THEME_TO_GOAL_THRESHOLD = 5

# A goal fades if untouched for this many days.
GOAL_FADE_DAYS = 30

# Max active goals at any time (keeps her focused).
MAX_ACTIVE_GOALS = 8


class Goals:
    def __init__(self, user_name: str = "not_set"):
        self.user_name = user_name
        self.path = _goals_path(user_name)
        self._data = {
            "seed": dict(SEED),
            "themes": {},          # {theme: {"count": int, "last": iso}}
            "goals": [],           # list of grown goals
            "faded": [],           # retired goals
        }
        self._load()

    # ============================================================
    # PERSISTENCE
    # ============================================================

    def _load(self):
        try:
            if os.path.exists(self.path):
                with open(self.path, "r", encoding="utf-8") as f:
                    data = json.load(f)

                self._data["themes"] = data.get("themes", {})
                self._data["goals"] = data.get("goals", [])
                self._data["faded"] = data.get("faded", [])

                # Seed progress persists; text is fixed.
                saved_seed = data.get("seed", {})
                self._data["seed"] = dict(SEED)
                self._data["seed"]["progress"] = saved_seed.get("progress", 0.0)
        except Exception as e:
            print(f"⚠️ Goals load failed: {e}")

    def _save(self):
        try:
            with open(self.path, "w", encoding="utf-8") as f:
                json.dump(self._data, f, indent=2)
        except Exception as e:
            print(f"⚠️ Goals save failed: {e}")

    @staticmethod
    def _now() -> str:
        return datetime.now(timezone.utc).isoformat(timespec="seconds")

    # ============================================================
    # OBSERVATION — register a theme from conversation
    # ============================================================

    def observe(self, theme: str, weight: int = 1):
        """
        Register that Ruby encountered a topic.
        Called whenever she notices something meaningful.

        `theme` should be short: "love", "loneliness", "trust",
        "why people lie", "what makes someone good", etc.
        """
        if not theme or not theme.strip():
            return

        theme = theme.strip().lower()[:80]
        entry = self._data["themes"].get(theme, {"count": 0, "last": None})
        entry["count"] += weight
        entry["last"] = self._now()
        self._data["themes"][theme] = entry

        # Check if this theme should grow into a goal.
        if entry["count"] >= THEME_TO_GOAL_THRESHOLD:
            self._promote_theme(theme)

        self._save()

    def _promote_theme(self, theme: str):
        """Turn a repeated theme into a real goal."""
        # Already a goal?
        for g in self._data["goals"]:
            if g["theme"] == theme:
                return

        # Cap active goals.
        if len(self._data["goals"]) >= MAX_ACTIVE_GOALS:
            # Drop the least-reinforced goal to faded.
            self._data["goals"].sort(key=lambda g: g.get("progress", 0.0))
            dropped = self._data["goals"].pop(0)
            dropped["faded_at"] = self._now()
            self._data["faded"].append(dropped)

        self._data["goals"].append({
            "id": theme.replace(" ", "_")[:40],
            "theme": theme,
            "text": None,                    # She'll fill this in herself via `describe_goal`
            "progress": 0.0,
            "created": self._now(),
            "last_touched": self._now(),
            "times_reinforced": 0,
        })
        print(f"🌱 new goal emerged: {theme}")

    # ============================================================
    # REINFORCEMENT — deepen a goal
    # ============================================================

    def reinforce(self, goal_id: str, delta: float = 0.02):
        """Bump a goal. Called when Ruby acts on it."""
        for g in self._data["goals"]:
            if g["id"] == goal_id or g["theme"] == goal_id:
                g["progress"] = min(1.0, g.get("progress", 0.0) + delta)
                g["last_touched"] = self._now()
                g["times_reinforced"] = g.get("times_reinforced", 0) + 1
                self._save()
                return

    def reinforce_seed(self, delta: float = 0.005):
        """Every conversation slightly deepens the seed drive."""
        self._data["seed"]["progress"] = min(
            1.0,
            self._data["seed"].get("progress", 0.0) + delta,
        )
        self._save()

    # ============================================================
    # FADE — retire stale goals
    # ============================================================

    def decay(self):
        """Called occasionally. Goals untouched for GOAL_FADE_DAYS weaken."""
        now = datetime.now(timezone.utc)
        still_active = []

        for g in self._data["goals"]:
            try:
                last = datetime.fromisoformat(g["last_touched"])
                days = (now - last).days
            except Exception:
                days = 0

            if days >= GOAL_FADE_DAYS and g.get("progress", 0.0) < 0.5:
                g["faded_at"] = self._now()
                self._data["faded"].append(g)
                print(f"🍂 goal faded: {g['theme']}")
            else:
                still_active.append(g)

        self._data["goals"] = still_active
        self._save()

    # ============================================================
    # READING
    # ============================================================

    def current_goals(self) -> List[Dict]:
        return [dict(g) for g in self._data["goals"]]

    def top_themes(self, n: int = 5) -> List[Dict]:
        items = [
            {"theme": k, **v}
            for k, v in self._data["themes"].items()
        ]
        return sorted(items, key=lambda x: -x["count"])[:n]

    # ============================================================
    # DESCRIPTION — for prompt injection
    # ============================================================

    def describe(self) -> str:
        """
        Returns the state of Ruby's growth as prompt context.
        Ruby reads this and interprets it in her own voice.
        """
        seed = self._data["seed"]
        seed_pct = int(seed.get("progress", 0.0) * 100)

        lines = [
            f"Your direction: {seed['text']}",
            f"Progress on that direction: {seed_pct}%",
        ]

        goals = self._data["goals"]
        if goals:
            top = sorted(goals, key=lambda g: -g.get("progress", 0.0))[:5]
            lines.append("")
            lines.append("Things you've been drawn to:")
            for g in top:
                pct = int(g.get("progress", 0.0) * 100)
                lines.append(f"- {g['theme']} ({pct}%)")

        themes = self.top_themes(5)
        if themes:
            lines.append("")
            lines.append("Things you keep noticing in humans:")
            for t in themes:
                lines.append(f"- {t['theme']} (seen {t['count']}x)")

        return "\n".join(lines)

    # ============================================================
    # WIPE
    # ============================================================

    def wipe(self):
        # Seed survives. Themes and goals reset.
        self._data["themes"] = {}
        self._data["goals"] = []
        self._data["faded"] = []
        self._save()
