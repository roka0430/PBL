import json
import copy

from .paths import SETTINGS_PATH

DEFINITIONS = {
    "sys": {
        "sensing_interval_sec": {
            "label": "センシング間隔",
            "unit": "秒",
            "default": 10.0,
            "min": 1.0,
            "max": None,
        },
        "startup_waiting_sec": {
            "label": "起動待機時間",
            "unit": "秒",
            "default": 10.0,
            "min": 0.0,
            "max": None,
        },
        "soil_moisture_dry": {
            "label": "乾燥時の土壌水分センサ値",
            "unit": "",
            "default": 800.0,
            "min": 0.0,
            "max": 1023.0,
        },
        "soil_moisture_wet": {
            "label": "湿潤時の土壌水分センサ値",
            "unit": "",
            "default": 300.0,
            "min": 0.0,
            "max": 1023.0,
        },
        "pump_flow_rate_ml_sec": {
            "label": "ポンプ流量",
            "unit": "mL/s",
            "default": 10.0,
            "min": 1.0,
            "max": None,
        },
    },
    "thr": {
        "determination_interval_sec": {
            "label": "給水判定間隔",
            "unit": "秒",
            "default": 60.0,
            "min": 1.0,
            "max": None,
        },
        "start_soil_moisture_percent": {
            "label": "給水開始しきい値",
            "unit": "%",
            "default": 30.0,
            "min": 0.0,
            "max": 100.0,
        },
        "stop_soil_moisture_percent": {
            "label": "給水終了しきい値",
            "unit": "%",
            "default": 50.0,
            "min": 0.0,
            "max": 100.0,
        },
    },
    "fix": {
        "determination_interval_sec": {
            "label": "給水判定間隔",
            "unit": "秒",
            "default": 60.0,
            "min": 1.0,
            "max": None,
        },
        "start_soil_moisture_percent": {
            "label": "給水開始しきい値",
            "unit": "%",
            "default": 30.0,
            "min": 0.0,
            "max": 100.0,
        },
        "amount_ml": {
            "label": "給水量",
            "unit": "mL",
            "default": 50.0,
            "min": 10.0,
            "max": None,
        },
    },
    "sch": {
        "interval_sec": {
            "label": "給水間隔",
            "unit": "秒",
            "default": 21600.0,
            "min": 0.0,
            "max": None,
        },
        "amount_ml": {
            "label": "給水量",
            "unit": "mL",
            "default": 50.0,
            "min": 10.0,
            "max": None,
        },
    },
}


class Settings:
    def __init__(self):
        self._settings = copy.deepcopy(DEFINITIONS)

        settings = self._load()
        for group, group_settings in settings.items():
            if group not in self._settings:
                continue

            for setting_id, value in group_settings.items():
                if setting_id not in self._settings[group]:
                    continue

                clamped = self._clamp(f"{group}.{setting_id}", value)
                self._settings[group][setting_id]["value"] = clamped

        for group, group_definitions in self._settings.items():
            for setting_id, definition in group_definitions.items():
                if "value" in definition:
                    continue

                definition["value"] = definition["default"]

    def get_settings(self):
        return {
            group: {
                setting_id: definition["value"]
                for setting_id, definition in settings.items()
            }
            for group, settings in self._settings.items()
        }

    def get_definitions(self):
        return self._settings

    def get(self, key):
        return self._get(key)

    def update(self, key, value):
        if not self._set(key, value):
            return False
        self._save()
        return True

    def _load(self):
        with open(SETTINGS_PATH, "r", encoding="utf-8") as f:
            return json.load(f)

    def _save(self):
        with open(SETTINGS_PATH, "w", encoding="utf-8") as f:
            json.dump(self._settings, f, indent=2)

    def _exists(self, key):
        try:
            group, setting_id = key.split(".")
            return setting_id in self._settings[group]
        except (ValueError, KeyError):
            return False

    def _get_definition(self, key):
        try:
            group, setting_id = key.split(".")
            return self._settings[group][setting_id]
        except (ValueError, KeyError, TypeError):
            return None

    def _set(self, key, value):
        definition = self._get_definition(key)
        if definition is None:
            return False
        definition["value"] = value
        return True

    def _get(self, key):
        definition = self._get_definition(key)
        if definition is None:
            return None
        return definition.get("value")

    def _clamp(self, key, value):
        definition = self._get_definition(key)

        if value is None:
            value = definition["default"]

        if definition["min"] is not None and value < definition["min"]:
            return definition["min"]

        if definition["max"] is not None and value > definition["max"]:
            return definition["max"]

        return value
