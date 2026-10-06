import time
import json
import threading
from datetime import datetime

from .paths import SETTINGS_PATH
from .enums import SystemStatus, ManualWateringResult, WateringType
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


class SystemController:
    def __init__(self):
        self.settings = Settings()
        self.settings.load()

        self.status = SystemStatus.IDLE
        self._status_lock = threading.Lock()

        self.watering_database = WateringDatabase()

        self.sensor_values = SensorValues()

        self.watering_stop_event = threading.Event()

        self.pump = Pump()
        self.camera = Camera()
        self.soil_moisture_sensor = SoilMoistureSensor(self.settings)
        self.temperature_and_humidity_sensor = TemperatureAndHumiditySensor()

    # ========== 外部から呼び出し ==========

    def manual_watering(self, amount_ml) -> ManualWateringResult:
        try:
            amount_ml = int(amount_ml)
        except (TypeError, ValueError):
            return ManualWateringResult.INVALID_AMOUNT, None

        if not MIN_WATER_AMOUNT_ML <= amount_ml <= MAX_WATER_AMOUNT_ML:
            return ManualWateringResult.INVALID_AMOUNT, None

        last_watered_at = self.watering_database.get_last_watered_at()
        if last_watered_at is not None:
            elapsed = (datetime.now() - last_watered_at).total_seconds()
            if elapsed < MIN_WATERING_INTERVAL_SEC:
                return ManualWateringResult.TOO_SOON, None

        with self._status_lock:
            if self.status != SystemStatus.IDLE:
                return ManualWateringResult.NOT_IDLE, None
            self.status = SystemStatus.WATERING

        self.watering_stop_event.clear()

        threading.Thread(
            target=self._watering, args=(WateringType.MANUAL, amount_ml), daemon=False
        ).start()

        duration_sec = amount_ml / self.settings.pump_flow_ml_per_sec
        return (ManualWateringResult.ACCEPTED, duration_sec)
        # TODO 後で何とかもっときれいに給水時間を返せるように

    def stop_watering(self):
        print("ok")
        self.watering_stop_event.set()
        self.pump.stop()

    def get_sensor_values(self) -> SensorValues:
        return self.sensor_values

    def get_image(self) -> Image:
        return self.camera.get_image()

    def get_history_count(self) -> int:
        return self.watering_database.get_count()

    def get_watering_history(self, before_id, limit) -> list[dict]:
        return self.watering_database.get(before_id=before_id, limit=limit)

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

            self.pump.start()

            stopped = self.watering_stop_event.wait(duration_sec)

            self.pump.stop()

            if stopped:
                return

            # self.watering_database.add(
            #     watered_at=datetime.now(),
            #     watering_type=watering_type,
            #     amount_ml=amount_ml,
            # )
        finally:
            self.pump.stop()

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
