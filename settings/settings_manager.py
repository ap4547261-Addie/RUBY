import json
import os


SETTINGS_PATH = os.path.join(
    os.path.dirname(__file__),
    "settings.json",
)

DEFAULT_SETTINGS = {
    # Account
    "user_name": "Addie",
    "user_phone": "",
    "user_email": "",
    "user_logged_in": False,

    # Brain
    "model_path": None,
    "model_name": None,
    "context_size": 1024,
    "threads": 4,

    # Appearance
    "theme": "dark",

    # Integrations (for later)
    "pinecone_api_key": None,
    "pinecone_host": None,
    "instagram_token": None,
}


class SettingsManager:
    def __init__(self):
        self.settings = self._load()

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

    def get(self, key, default=None):
        return self.settings.get(key, default)

    def set(self, key, value):
        self.settings[key] = value
        self._save()

    def update(self, data: dict):
        self.settings.update(data)
        self._save()

    def has_model(self) -> bool:
        path = self.get("model_path")
        return bool(path and os.path.exists(path))
