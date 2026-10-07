import json

from .paths import SETTINGS_PATH, DEFAULT_SETTINGS_PATH


class Settings:
    def __init__(self):
        self._default_settings = self._load(DEFAULT_SETTINGS_PATH)

        self._settings = {
            key: value["default"] for key, value in self._default_settings.items()
        }

        need_save = False

        if SETTINGS_PATH.exists():
            settings = self._load(SETTINGS_PATH)
            for key, value in settings.items():
                if key in self._settings:
                    self._settings[key] = value
                    need_save = True
        else:
            need_save = True

        if need_save:
            self._save()

    def _load(self, path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    def _save(self):
        with open(SETTINGS_PATH, "w", encoding="utf-8") as f:
            json.dump(self._settings, f, indent=2)

    def _clamp(self, key, value):
        settings = self._default_settings[key]

        min_value = settings["min"]
        max_value = settings["max"]

        if min_value is not None and value < min_value:
            return min_value

        if max_value is not None and value > max_value:
            return max_value

        return value

    def get(self, key):
        return self._clamp(key, self._settings[key])

    def get_all(self):
        return self._settings
