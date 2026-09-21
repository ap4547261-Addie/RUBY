# ruby_core/reflection.py
# Ruby's self-reflection at the ruby_core level.

import os
import json
from datetime import datetime


def _refl_path(user_name: str) -> str:
    storage = os.getenv("FLET_APP_STORAGE_DATA", ".")
    return os.path.join(storage, f"core_reflection_{user_name}.json")


class Reflection:
    def __init__(self, user_name: str = "not_set"):
        self.user_name = user_name
        self.path = _refl_path(user_name)
        self._data = {"entries": []}
        self._load()

    def _load(self):
        try:
            if os.path.exists(self.path):
                with open(self.path, "r", encoding="utf-8") as f:
                    self._data.update(json.load(f))
        except Exception as e:
            print(f"⚠️ Reflection load failed: {e}")

    def _save(self):
        try:
            with open(self.path, "w", encoding="utf-8") as f:
                json.dump(self._data, f, indent=2)
        except Exception as e:
            print(f"⚠️ Reflection save failed: {e}")

    def add(self, text: str, kind: str = "general"):
        self._data["entries"].append({
            "text": text[:500],
            "kind": kind,
            "ts": datetime.now().isoformat(timespec="seconds"),
        })
        self._data["entries"] = self._data["entries"][-100:]
        self._save()

    def recent(self, limit: int = 5) -> list:
        return self._data["entries"][-limit:]

    def describe(self) -> str:
        entries = self.recent(3)
        if not entries:
            return "No recent self-reflection."
        lines = ["Recent self-reflection:"]
        for e in entries:
            lines.append(f"- [{e['kind']}] {e['text']}")
        return "\n".join(lines)

    def wipe(self):
        self._data["entries"] = []
        self._save()
