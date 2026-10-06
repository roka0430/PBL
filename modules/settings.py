import json

from .paths import SETTINGS_PATH, DEFAULT_SETTINGS_PATH


class Settings:
    def __init__(self):
        self._default_settings = self._load(DEFAULT_SETTINGS_PATH)

        if SETTINGS_PATH.exists():
            self._settings = self._load(SETTINGS_PATH)
            print(self._settings)
        else:
            self._settings = {
                key: value["default"] for key, value in self._default_settings.items()
            }
            self._save()

    def _load(self, path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    def _save(self):
        with open(SETTINGS_PATH, "w", encoding="utf-8") as f:
            json.dump(self._settings, f, indent=2)

    def get(self, key):
        return self._settings[key]
