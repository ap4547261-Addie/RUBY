# ruby_core/self_model.py
# Ruby's self-concept: who she thinks she is.

import os
import json


def _self_path(user_name: str) -> str:
    storage = os.getenv("FLET_APP_STORAGE_DATA", ".")
    return os.path.join(storage, f"self_{user_name}.json")


class SelfModel:
    def __init__(self, user_name: str = "not_set"):
        self.user_name = user_name
        self.path = _self_path(user_name)
        self._data = {
            "name": "Ruby",
            "role": "companion",
            "traits": {},
            "recent_self_observations": [],
        }
        self._load()

    def _load(self):
        try:
            if os.path.exists(self.path):
                with open(self.path, "r", encoding="utf-8") as f:
                    self._data.update(json.load(f))
        except Exception as e:
            print(f"⚠️ SelfModel load failed: {e}")

    def _save(self):
        try:
            with open(self.path, "w", encoding="utf-8") as f:
                json.dump(self._data, f, indent=2)
        except Exception as e:
            print(f"⚠️ SelfModel save failed: {e}")

    def observe(self, statement: str, importance: int = 2):
        self._data["recent_self_observations"].append({
            "text": statement[:300],
            "importance": importance,
        })
        self._data["recent_self_observations"] = self._data["recent_self_observations"][-50:]
        self._save()

    def observations(self, limit: int = 5) -> list:
        return self._data["recent_self_observations"][-limit:]

    def describe(self) -> str:
        obs = self.observations(3)
        lines = [f"I am {self._data['name']}, a {self._data['role']}."]
        for o in obs:
            lines.append(f"- {o['text']}")
        return "\n".join(lines)

    def wipe(self):
        self._data["recent_self_observations"] = []
        self._save()
