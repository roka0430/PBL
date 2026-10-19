import json
import copy

from .paths import SETTINGS_PATH

DEFINITIONS = {
    "sys": {
        "sensing_interval_sec": {
            "label": "センシング間隔",
            "description": "土壌水分などのセンサ値を取得する間隔を設定します。",
            "unit": "秒",
            "default": 10,
            "min": 1,
            "max": None,
        },
        "startup_waiting_sec": {
            "label": "起動待機時間",
            "description": "システム起動後、センシングを始めるまでの待機時間を設定します。",
            "unit": "秒",
            "default": 10,
            "min": 0,
            "max": None,
        },
        "soil_moisture_dry": {
            "label": "乾燥時の土壌水分センサ値",
            "description": "土壌が乾燥しているときのセンサ値を設定します。土壌水分量の算出に使用します。",
            "unit": "",
            "default": 800,
            "min": 0,
            "max": 1023,
        },
        "soil_moisture_wet": {
            "label": "湿潤時の土壌水分センサ値",
            "description": "土壌が十分に湿っているときのセンサ値を設定します。土壌水分量の算出に使用します。",
            "unit": "",
            "default": 300,
            "min": 0,
            "max": 1023,
        },
        "pump_flow_rate_ml_sec": {
            "label": "ポンプ流量",
            "description": "ポンプが1秒間に排出する水量を設定します。給水量の算出に使用します。",
            "unit": "mL/s",
            "default": 10,
            "min": 1,
            "max": None,
        },
        "high_temperature_threshold": {
            "label": "高温警告しきい値",
            "description": "気温がこの値以上になると、高温警告を行います。",
            "unit": "℃",
            "default": 40,
            "min": -40,
            "max": 80,
        },
        "low_temperature_threshold": {
            "label": "低温警告しきい値",
            "description": "気温がこの値以下になると、低温警告を行います。",
            "unit": "℃",
            "default": 0,
            "min": -40,
            "max": 80,
        },
        "sensor_saving_interval_sec": {
            "label": "センサ値保存間隔",
            "description": "センサ値を保存する間隔を設定します。",
            "unit": "秒",
            "default": 600,
            "min": 60,
            "max": None,
        },
    },
    "thr": {
        "determination_interval_sec": {
            "label": "給水判定間隔",
            "description": "土壌水分量を確認し、給水の開始を判定する間隔を設定します。",
            "unit": "秒",
            "default": 60,
            "min": 60,
            "max": None,
        },
        "start_soil_moisture_percent": {
            "label": "給水開始しきい値",
            "description": "土壌水分量がこの値を下回ると、自動給水を開始します。",
            "unit": "%",
            "default": 30,
            "min": 0,
            "max": 100,
        },
        "stop_soil_moisture_percent": {
            "label": "給水終了しきい値",
            "description": "土壌水分量がこの値を上回ると、自動給水を終了します。",
            "unit": "%",
            "default": 50,
            "min": 0,
            "max": 100,
        },
    },
    "fix": {
        "determination_interval_sec": {
            "label": "給水判定間隔",
            "description": "土壌水分率を確認し、給水するかどうかを判定する間隔を設定します。",
            "unit": "秒",
            "default": 60,
            "min": 1,
            "max": None,
        },
        "start_soil_moisture_percent": {
            "label": "給水開始しきい値",
            "description": "土壌水分率がこの値を下回ると、設定した量の給水を行います。",
            "unit": "%",
            "default": 30,
            "min": 0,
            "max": 100,
        },
        "amount_ml": {
            "label": "給水量",
            "description": "1回の給水でポンプから排出する水量を設定します。",
            "unit": "mL",
            "default": 50,
            "min": 10,
            "max": None,
        },
    },
    "sch": {
        "interval_sec": {
            "label": "給水間隔",
            "description": "定期給水を実行する間隔を設定します。",
            "unit": "秒",
            "default": 21600,
            "min": 10,  # TODO 適切な時間に再設定
            "max": None,
        },
        "amount_ml": {
            "label": "給水量",
            "description": "1回の定期給水でポンプから排出する水量を設定します。",
            "unit": "mL",
            "default": 50,
            "min": 10,
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
        if not isinstance(value, int) and not isinstance(value, float):
            return False, None

        if not self._set(key, value):
            return False, None

        self._save()
        return True, self._get(key)

    def _load(self):
        with open(SETTINGS_PATH, "r", encoding="utf-8") as f:
            return json.load(f)

    def _save(self):
        with open(SETTINGS_PATH, "w", encoding="utf-8") as f:
            json.dump(self.get_settings(), f, indent=2, ensure_ascii=False)

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

        definition["value"] = self._clamp(key, value)
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
