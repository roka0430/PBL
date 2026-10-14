import json

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
            "min": 60.0,
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
        self._setting_definitions = self._load(SETTING_DEFINITIONS_PATH)

        self._settings = {
            key: value["default"] for key, value in self._setting_definitions.items()
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
        settings = self._setting_definitions[key]

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

    def get_definitions(self):
        return {
            key: {**config, "value": self._settings.get(key, config["default"])}
            for key, config in self._setting_definitions.items()
        }

    def update(self, settings):
        for key, value in settings.items():
            if key not in self._setting_definitions:
                raise KeyError(key)

            self._settings[key] = self._clamp(key, value)
        self._save()
