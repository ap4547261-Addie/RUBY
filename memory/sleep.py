# memory/sleep.py — Ruby's sleep: memory consolidation overnight.
#
# While a person sleeps the brain replays the day: emotionally important
# moments are strengthened, ordinary details fade, and you wake up with a
# gist rather than a transcript. Ruby does the same, once per night:
#
#   - every older memory loses a little strength (ordinary ones fast, emotional
#     ones slowly) -> small talk fades, big moments last
#   - the most emotional recent moments are "replayed" and strengthened
#   - a memory that has faded below EpisodicMemory.FADED_BELOW is no longer
#     recalled. NOTHING is deleted — forgetting is not erasing.
#   - she wakes up with a "gist": the moment that stayed with her most. It can
#     become an idle thought (see brain/idle_thoughts.py).
#
# It runs lazily and catches up: if the app was closed for three nights, three
# nights of consolidation are applied the next time it is opened (no cap). A "night"
# ends at 06:00 local time. No LLM, no network.

import os
import json
from datetime import datetime, timedelta, date
from typing import Optional, Dict

from memory import database

NIGHT_ENDS_HOUR = 6

PROTECT_RECENT_HOURS = 20       # the last day is never touched: it's still "today"
DECAY_ORDINARY = 0.93           # per night, intensity < 1
DECAY_EMOTIONAL = 0.985         # per night, intensity >= 1
REPLAY_BOOST = 0.25
REPLAY_MIN_INTENSITY = 1.0


class SleepCycle:
    def __init__(self, user_name: str = "not_set", storage_dir: Optional[str] = None):
        self.user_name = user_name
        folder = storage_dir or os.getenv("FLET_APP_STORAGE_DATA", ".")
        self.path = os.path.join(folder, f"sleep_{user_name}.json")
        self._data: Dict = {"last_night": None, "gist": None, "nights": 0}
        self._load()

    # ---------------- persistence ----------------
    def _load(self):
        try:
            if os.path.exists(self.path):
                with open(self.path, "r", encoding="utf-8") as f:
                    self._data.update(json.load(f))
        except Exception as e:
            print(f"⚠️ Sleep load failed: {e}")

    def _save(self):
        try:
            with open(self.path, "w", encoding="utf-8") as f:
                json.dump(self._data, f)
        except Exception as e:
            print(f"⚠️ Sleep save failed: {e}")

    def wipe(self):
        self._data = {"last_night": None, "gist": None, "nights": 0}
        self._save()

    # ---------------- the night ----------------
    @staticmethod
    def _night_date(now: datetime) -> date:
        """The date of the most recent night that has ENDED (06:00 passed)."""
        if now.hour >= NIGHT_ENDS_HOUR:
            return now.date()
        return now.date() - timedelta(days=1)

    def nights_pending(self, now: Optional[datetime] = None) -> int:
        now = now or datetime.now()
        latest = self._night_date(now)
        last = self._data.get("last_night")
        if not last:
            return 1
        try:
            return max(0, (latest - date.fromisoformat(last)).days)
        except Exception:
            return 1

    def maybe_sleep(self, now: Optional[datetime] = None) -> Optional[Dict]:
        """Consolidate any nights that have passed. Cheap when there's nothing to do.
        Returns a summary dict when a sleep happened, else None."""
        now = now or datetime.now()
        pending = self.nights_pending(now)
        if pending <= 0:
            return None
        nights = pending
        try:
            summary = self._consolidate(now, nights)
        except Exception as e:
            print(f"⚠️ Sleep consolidation failed: {e}")
            return None
        self._data["last_night"] = self._night_date(now).isoformat()
        self._data["nights"] = int(self._data.get("nights", 0)) + nights
        self._data["gist"] = summary.get("gist")
        self._save()
        print(f"😴 Ruby slept ({nights} night(s)): {summary['faded']} faded, "
              f"{summary['replayed']} replayed")
        return summary

    def _consolidate(self, now: datetime, nights: int) -> Dict:
        cutoff = (now - timedelta(hours=PROTECT_RECENT_HOURS)).isoformat(timespec="seconds")
        conn = database.get_connection()
        c = conn.cursor()

        # 1. replay: the strongest emotional moments from the last few days get stronger.
        #    (Done before fading so a vivid moment isn't eroded by the night that replays it.)
        window = (now - timedelta(days=3)).isoformat(timespec="seconds")
        c.execute(
            """
            SELECT id, user_message, ruby_reply, emotion, intensity, timestamp
            FROM episodes
            WHERE intensity >= ? AND timestamp >= ? AND COALESCE(strength, 1.0) >= 0.25
            ORDER BY intensity DESC, id DESC
            """,
            (REPLAY_MIN_INTENSITY, window),
        )
        replay = c.fetchall()
        for rid, *_ in replay:
            c.execute(
                "UPDATE episodes SET strength = COALESCE(strength, 1.0) + ? WHERE id = ?",
                (REPLAY_BOOST * nights, rid),
            )

        # 2. fade: everything older than a day weakens, ordinary memories faster.
        replay_ids = {r[0] for r in replay}
        before = c.execute(
            "SELECT COUNT(*) FROM episodes WHERE COALESCE(strength,1.0) >= 0.25"
        ).fetchone()[0]
        c.execute(
            "UPDATE episodes SET strength = COALESCE(strength, 1.0) * ? "
            "WHERE timestamp < ? AND COALESCE(intensity, 0) < 1.0 AND strength > 0.0",
            (DECAY_ORDINARY ** nights, cutoff),
        )
        c.execute(
            "UPDATE episodes SET strength = COALESCE(strength, 1.0) * ? "
            "WHERE timestamp < ? AND COALESCE(intensity, 0) >= 1.0 AND strength > 0.0",
            (DECAY_EMOTIONAL ** nights, cutoff),
        )
        after = c.execute(
            "SELECT COUNT(*) FROM episodes WHERE COALESCE(strength,1.0) >= 0.25"
        ).fetchone()[0]
        conn.commit()
        conn.close()

        # 3. waking gist: the replayed moment that hit hardest
        gist = None
        if replay:
            rid, u, r, emotion, intensity, ts = replay[0]
            gist = {
                "user_message": (u or "")[:160],
                "ruby_reply": (r or "")[:160],
                "emotion": emotion or "",
                "intensity": intensity,
                "timestamp": ts,
                "night": self._night_date(now).isoformat(),
            }
        return {"faded": max(0, before - after), "replayed": len(replay_ids), "gist": gist}

    # ---------------- reading ----------------
    def gist(self) -> Optional[Dict]:
        return self._data.get("gist")

    def clear_gist(self):
        self._data["gist"] = None
        self._save()
