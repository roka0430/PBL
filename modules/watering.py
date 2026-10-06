import time
import json
import threading
from datetime import datetime

from .paths import SETTINGS_PATH
from .enums import SystemStatus, WateringRequestResult
from .dataclasses import SensorValue, SensorValues, Image
from .database import WateringDatabase
from .hardware import Pump, Camera, SoilMoistureSensor, TemperatureAndHumiditySensor

SENSOR_STARTUP_DELAY_SEC = 10  # センサー起動待ち時間
SENSOR_CHECK_INTERVAL_SEC = 3  # センシング間隔

MIN_WATER_AMOUNT_ML = 10  # 1回給水量下限
MAX_WATER_AMOUNT_ML = 200  # 1回給水量上限
MIN_WATERING_INTERVAL_SEC = 10  # 給水間隔制限


class Settings:
    DEFAULTS = {
        "watering_amount_ml": 100,
        "soil_moisture_dry": 1000,
        "soil_moisture_wet": 100,
        "pump_flow_ml_per_sec": 20.0,
    }

    def __init__(self):
        self.watering_amount_ml = self.DEFAULTS["watering_amount_ml"]
        self.soil_moisture_dry = self.DEFAULTS["soil_moisture_dry"]
        self.soil_moisture_wet = self.DEFAULTS["soil_moisture_wet"]
        self.pump_flow_ml_per_sec = self.DEFAULTS["pump_flow_ml_per_sec"]

    def load(self):
        if not SETTINGS_PATH.exists():
            return

        try:
            data = json.loads(SETTINGS_PATH.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return

        for name in self.DEFAULTS:
            if name in data:
                setattr(self, name, data[name])

    def save(self):
        SETTINGS_PATH.parent.mkdir(parents=True, exist_ok=True)

        data = {name: getattr(self, name) for name in self.DEFAULTS}

        SETTINGS_PATH.write_text(
            json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
        )

    def update(self, **kwargs):
        for name, value in kwargs.items():
            if name not in self.DEFAULTS:
                raise ValueError(f"Unknown setting: {name}")

            setattr(self, name, value)

        self.save()


class WateringHistory:  # TODO: LiteSQLで保存・読出し
    def __init__(self):
        self._watering_database = WateringDatabase()
        self._history = []

    def add(self, watered_at, watering_type, amount_ml):
        self._history.append(
            {
                "watered_at": watered_at,
                "watering_type": watering_type,
                "amount_ml": amount_ml,
            }
        )
        self._watering_database.add(watered_at, watering_type, amount_ml)

    def get_last(self):
        if not self._history:
            return None
        return self._history[-1]

    def elapsed_sec_since_last(self) -> float | None:
        last = self.get_last()

        if last is None:
            return None

        return (datetime.now() - last["watered_at"]).total_seconds()


# ------------------------------ Hardware ------------------------------

# ------------------------------ Controller ------------------------------


class SystemController:
    def __init__(self):
        self.settings = Settings()
        self.settings.load()

        self.history = WateringHistory()

        self.status = SystemStatus.IDLE
        self._status_lock = threading.Lock()

        self.sensor_values = SensorValues()

        self.pump = Pump()
        self.camera = Camera()
        self.soil_moisture_sensor = SoilMoistureSensor(self.settings)
        self.temperature_and_humidity_sensor = TemperatureAndHumiditySensor()

    # ========== 外部から呼び出し ==========

    def request_watering(self, amount_ml) -> WateringRequestResult:
        try:
            amount_ml = int(amount_ml)
        except (TypeError, ValueError):
            return WateringRequestResult.INVALID_AMOUNT, None

        # TODO: さらに水やり条件を追加
        if not MIN_WATER_AMOUNT_ML <= amount_ml <= MAX_WATER_AMOUNT_ML:
            return WateringRequestResult.INVALID_AMOUNT, None

        elapsed = self.history.elapsed_sec_since_last()
        if elapsed is not None and elapsed < MIN_WATERING_INTERVAL_SEC:
            return WateringRequestResult.TOO_SOON, None

        with self._status_lock:
            if self.status != SystemStatus.IDLE:
                return WateringRequestResult.NOT_IDLE, None
            self.status = SystemStatus.WATERING

        threading.Thread(
            target=self._watering, args=("manual", amount_ml), daemon=False
        ).start()  # TODO manualを定数化

        duration_sec = amount_ml / self.settings.pump_flow_ml_per_sec
        return WateringRequestResult.ACCEPTED, duration_sec

    def get_sensor_values(self) -> SensorValues:
        return self.sensor_values

    def get_image(self) -> Image:
        return self.camera.get_image()

    # ========== メインループ ==========

    def mainloop(self):
        time.sleep(SENSOR_STARTUP_DELAY_SEC)

        while True:
            self._check_sensors()
            time.sleep(SENSOR_CHECK_INTERVAL_SEC)

    # ========== 内部処理 ==========

    def _watering(self, watering_type, amount_ml):
        try:
            flow_rate = self.settings.pump_flow_ml_per_sec
            duration_sec = amount_ml / flow_rate

            self.pump.run(duration_sec)
            self.history.add(datetime.now(), watering_type, amount_ml)
        finally:
            with self._status_lock:
                self.status = SystemStatus.IDLE

    def _check_sensors(self):
        with self._status_lock:
            if self.status == SystemStatus.IDLE:
                self._check_soil_moisture()
        self._check_temperature_and_humidity()

    def _check_soil_moisture(self):
        soil_moisture = self.soil_moisture_sensor.read()

        self.sensor_values.soil_moisture = SensorValue(
            value=soil_moisture, measured_at=datetime.now()
        )

    def _check_temperature_and_humidity(self):
        temperature, humidity = self.temperature_and_humidity_sensor.read()
        measured_at = datetime.now()

        self.sensor_values.temperature = SensorValue(
            value=temperature, measured_at=measured_at
        )

        self.sensor_values.humidity = SensorValue(
            value=humidity, measured_at=measured_at
        )
