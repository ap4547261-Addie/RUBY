# ruby_core/internal_state.py
# Ruby's body / mood state. Energy, warmth, tension, irritation.

import os
import json
from datetime import datetime
from ruby_core.circadian import effective_energy


def _state_path(user_name: str) -> str:
    storage = os.getenv("FLET_APP_STORAGE_DATA", ".")
    return os.path.join(storage, f"state_{user_name}.json")


class InternalState:
    def __init__(self, user_name: str = "not_set"):
        self.user_name = user_name
        self.path = _state_path(user_name)
        self._data = {
            "energy": 1.0,
            "warmth": 0.5,
            "tension": 0.0,
            "irritation": 0.0,
        }
        # When the state was last written. Kept OUT of _data so get() only
        # ever returns the four numeric mood values other modules expect.
        self._last_updated = None
        self._load()

    def _load(self):
        try:
            if os.path.exists(self.path):
                with open(self.path, "r", encoding="utf-8") as f:
                    loaded = json.load(f)
                self._last_updated = loaded.pop("last_updated", None)
                self._data.update(
                    {k: v for k, v in loaded.items() if k in self._data}
                )
        except Exception as e:
            print(f"⚠️ InternalState load failed: {e}")

    def _save(self):
        try:
            self._last_updated = datetime.now().isoformat(timespec="seconds")
            payload = dict(self._data)
            payload["last_updated"] = self._last_updated
            with open(self.path, "w", encoding="utf-8") as f:
                json.dump(payload, f)
        except Exception as e:
            print(f"⚠️ InternalState save failed: {e}")

    def hours_since_update(self) -> float:
        """Hours since the state was last saved (0.0 if never saved)."""
        if not self._last_updated:
            return 0.0
        try:
            last = datetime.fromisoformat(self._last_updated)
            return max(0.0, (datetime.now() - last).total_seconds() / 3600)
        except Exception:
            return 0.0

    def get(self) -> dict:
        return dict(self._data)

    def set(self, key: str, value: float):
        if key in self._data:
            self._data[key] = max(0.0, min(1.0, float(value)))
            self._save()

    def adjust(self, key: str, delta: float):
        if key in self._data:
            self._data[key] = max(0.0, min(1.0, self._data[key] + float(delta)))
            self._save()

    def tick(self):
        # slow drift back toward baseline
        self._data["energy"] = self._clamp(self._data["energy"] + 0.02)
        self._data["tension"] = self._clamp(self._data["tension"] - 0.03)
        self._data["irritation"] = self._clamp(self._data["irritation"] - 0.03)
        self._save()

    @staticmethod
    def _clamp(v: float) -> float:
        return max(0.0, min(1.0, v))

    def describe(self, now=None) -> str:
        d = self._data
        parts = []
        # energy = what the conversation has cost her, scaled by the body clock
        e = effective_energy(d["energy"], now)
        if e > 0.7:
            parts.append("energetic")
        elif e < 0.33:
            parts.append("tired")
        if d["warmth"] > 0.7:
            parts.append("warm")
        elif d["warmth"] < 0.3:
            parts.append("distant")
        if d["tension"] > 0.5:
            parts.append("tense")
        if d["irritation"] > 0.5:
            parts.append("irritated")
        return ", ".join(parts) if parts else "calm"

    def wipe(self):
        self._data = {"energy": 1.0, "warmth": 0.5, "tension": 0.0, "irritation": 0.0}
        self._save()
