import json
import os
import shutil
from datetime import datetime


SETTINGS_PATH = os.path.join(os.path.dirname(__file__), "settings.json")
BACKUP_DIR = "/storage/emulated/0/Download/ruby_backups"

DEFAULT_SETTINGS = {
    # -------------------------
    # Account
    # -------------------------
    "user_name": "not_set",
    "user_phone": "",
    "user_email": "",
    "user_logged_in": False,
    "user_google_id": None,

    # -------------------------
    # Brain
    # -------------------------
    "model_path": None,
    "model_name": None,
    "context_size": 1024,
    "threads": 4,

    # -------------------------
    # Appearance
    # -------------------------
    "theme": "dark",
    "accent_color": "pink",

    # -------------------------
    # Integrations
    # -------------------------
    "pinecone_api_key": None,
    "pinecone_host": None,
    "instagram_token": None,

    # -------------------------
    # Backup
    # -------------------------
    "auto_backup": True,
    "last_backup": None,
}


class SettingsManager:
    def __init__(self):
        self.settings = self._load()

    # -------------------------
    # Load / Save
    # -------------------------
    def _load(self) -> dict:
        if not os.path.exists(SETTINGS_PATH):
            self._save(DEFAULT_SETTINGS)
            return DEFAULT_SETTINGS.copy()
        try:
            with open(SETTINGS_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
            merged = DEFAULT_SETTINGS.copy()
            merged.update(data)
            return merged
        except Exception as e:
            print(f"⚠️ Settings load failed: {e}")
            return DEFAULT_SETTINGS.copy()

    def _save(self, data: dict = None):
        if data is None:
            data = self.settings
        try:
            with open(SETTINGS_PATH, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"⚠️ Settings save failed: {e}")

    # -------------------------
    # Access
    # -------------------------
    def get(self, key, default=None):
        return self.settings.get(key, default)

    def set(self, key, value):
        self.settings[key] = value
        self._save()

    def update(self, data: dict):
        self.settings.update(data)
        self._save()

    def reset(self):
        self.settings = DEFAULT_SETTINGS.copy()
        self._save()

    # -------------------------
    # Helpers
    # -------------------------
    def has_model(self) -> bool:
        path = self.get("model_path")
        return bool(path and os.path.exists(path))

    def is_logged_in(self) -> bool:
        return bool(self.get("user_logged_in", False))

    # -------------------------
    # Backup
    # -------------------------
    def export_backup(self) -> str:
        try:
            os.makedirs(BACKUP_DIR, exist_ok=True)
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            dst = os.path.join(BACKUP_DIR, f"ruby_settings_{ts}.json")
            shutil.copy(SETTINGS_PATH, dst)
            self.settings["last_backup"] = ts
            self._save()
            print(f"✅ Backup saved: {dst}")
            return dst
        except Exception as e:
            print(f"❌ Backup failed: {e}")
            return None

    def import_backup(self, path: str) -> bool:
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            merged = DEFAULT_SETTINGS.copy()
            merged.update(data)
            self.settings = merged
            self._save()
            print(f"✅ Backup restored: {path}")
            return True
        except Exception as e:
            print(f"❌ Restore failed: {e}")
            return False
