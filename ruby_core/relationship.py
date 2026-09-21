# ruby_core/relationship.py
# Ruby's relationship state with the user.

import os
import json
from datetime import datetime


def _rel_path(user_name: str) -> str:
    storage = os.getenv("FLET_APP_STORAGE_DATA", ".")
    return os.path.join(storage, f"rel_{user_name}.json")


class Relationship:
    def __init__(self, user_name: str = "not_set"):
        self.user_name = user_name
        self.path = _rel_path(user_name)
        self._data = {
            "trust": 0.5,
            "familiarity": 0.0,
            "respect": 0.5,
            "attachment": 0.0,
            "message_count": 0,
            "first_seen": datetime.now().isoformat(timespec="seconds"),
            "last_seen": datetime.now().isoformat(timespec="seconds"),
        }
        self._load()

    def _load(self):
        try:
            if os.path.exists(self.path):
                with open(self.path, "r", encoding="utf-8") as f:
                    self._data.update(json.load(f))
        except Exception as e:
            print(f"⚠️ Relationship load failed: {e}")

    def _save(self):
        try:
            with open(self.path, "w", encoding="utf-8") as f:
                json.dump(self._data, f, indent=2)
        except Exception as e:
            print(f"⚠️ Relationship save failed: {e}")

    def get_state(self) -> dict:
        return dict(self._data)

    def bump_message(self):
        self._data["message_count"] += 1
        self._data["last_seen"] = datetime.now().isoformat(timespec="seconds")
        # familiarity grows with messages
        self._data["familiarity"] = min(1.0, self._data["familiarity"] + 0.01)
        self._save()

    def adjust_trust(self, delta: float):
        self._data["trust"] = max(0.0, min(1.0, self._data["trust"] + delta))
        self._save()

    def adjust_attachment(self, delta: float):
        self._data["attachment"] = max(0.0, min(1.0, self._data["attachment"] + delta))
        self._save()

    def describe(self) -> str:
        d = self._data
        return (
            f"You've exchanged {d['message_count']} messages. "
            f"Trust: {d['trust']:.2f}, Familiarity: {d['familiarity']:.2f}, "
            f"Attachment: {d['attachment']:.2f}."
        )

    def wipe(self):
        self._data.update({
            "trust": 0.5, "familiarity": 0.0, "respect": 0.5,
            "attachment": 0.0, "message_count": 0,
        })
        self._save()
