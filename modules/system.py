import os
import time
import threading
from datetime import datetime, timedelta

from .enums import SystemStatus, AutoWateringMode, ManualWateringResult, WateringType
from .dataclasses import SensorValue, SensorValues, Image
from .settings import Settings
from .database import WateringDatabase

hardware_mode = os.environ["HARDWARE_MODE"]

if hardware_mode == "real":
    from .hardware import (
        Pump,
        Camera,
        SoilMoistureSensor,
        TemperatureAndHumiditySensor,
    )
elif hardware_mode == "mock":
    from .hardware_mock import (
        Pump,
        Camera,
        SoilMoistureSensor,
        TemperatureAndHumiditySensor,
    )


MIN_WATER_AMOUNT_ML = 10  # 1回給水量下限
MAX_WATER_AMOUNT_ML = 200  # 1回給水量上限

MIN_WATERING_INTERVAL_SEC = 10  # 給水間隔制限


class SystemController:
    def __init__(self):
        self.settings = Settings()

        self.status = SystemStatus.IDLE
        self._status_lock = threading.Lock()

        self.auto_watering_mode = AutoWateringMode.THRESHOLD_CONTROL  # TODO OFFにする

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

        duration_sec = amount_ml / self.settings.get("pump_flow_ml_per_sec")

        threading.Thread(
            target=self._watering,
            args=(WateringType.MANUAL, amount_ml, duration_sec),
            daemon=False,
        ).start()

        return (ManualWateringResult.ACCEPTED, duration_sec)

    def stop_watering(self):
        self.watering_stop_event.set()
        self.pump.stop()

    def get_sensor_values(self) -> SensorValues:
        return self.sensor_values

    def get_image(self) -> Image:
        return self.camera.get_image()

    def get_status(self) -> SystemStatus:
        return self.status

    def get_settings(self) -> list[dict]:
        return self.settings.get_all()

    def get_setting_definitions(self) -> list[dict]:
        return self.settings.get_definitions()

    def get_history_count(self) -> int:
        return self.watering_database.get_count()

    def get_watering_history(self, before_id, after_id, limit) -> list[dict]:
        return self.watering_database.get(
            before_id=before_id, after_id=after_id, limit=limit
        )

    def close(self):
        self.pump.close()
        self.soil_moisture_sensor.close()

    # ========== メインループ ==========

    def mainloop(self):
        time.sleep(self.settings.get("sensor_startup_delay_sec"))

        next_watering_check = time.monotonic() + self.settings.get(
            "auto_watering_check_interval_sec"
        )

        while True:
            self._check_sensors()

            if (
                self.auto_watering_mode != AutoWateringMode.OFF
                and time.monotonic() >= next_watering_check
            ):
                self._process_auto_watering()
                next_watering_check = time.monotonic() + self.settings.get(
                    "auto_watering_check_interval_sec"
                )

            time.sleep(self.settings.get("sensor_check_interval_sec"))

    # ========== 内部処理 ==========

    def _watering(self, watering_type, amount_ml, duration_sec):
        try:
            self.pump.start()

            stopped = self.watering_stop_event.wait(duration_sec)

            self.pump.stop()

            if stopped:
                return

            self.watering_database.add(
                watered_at=datetime.now(),
                watering_type=watering_type,
                amount_ml=amount_ml,
            )
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
        soil_moisture, soil_moisture_raw = self.soil_moisture_sensor.read()
        measured_at = datetime.now()

        self.sensor_values.soil_moisture = SensorValue(
            value=soil_moisture, measured_at=measured_at
        )

        self.sensor_values.soil_moisture_raw = SensorValue(
            value=soil_moisture_raw, measured_at=measured_at
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

    def _process_auto_watering(self):
        if self.auto_watering_mode == AutoWateringMode.OFF:
            return

        if self.auto_watering_mode == AutoWateringMode.THRESHOLD_CONTROL:
            self._process_threshold_control()

        if self.auto_watering_mode == AutoWateringMode.FIXED_AMOUNT:
            self._process_fixed_amount()

        if self.auto_watering_mode == AutoWateringMode.SCHEDULED:
            self._process_scheduled()

    def _process_threshold_control(self):
        if not self._is_soil_dry:
            return

    def _process_fixed_amount(self):
        if not self._is_soil_dry:
            return

        amount_ml = self.settings.get("watering_amount_ml")
        duration_sec = amount_ml / self.settings.get("pump_flow_ml_per_sec")
        self._watering(WateringType.AUTO, amount_ml, duration_sec)

    def _process_scheduled(self):
        pass

    def _is_soil_dry(self) -> bool | None:
        value = self._get_valid_soil_moisture()

        if value is None:
            return None

        return value < self.settings.get("watering_start_threshold")

    def _is_soil_wet(self) -> bool | None:
        value = self._get_valid_soil_moisture()

        if value is None:
            return None

        return value > self.settings.get("watering_stop_threshold")

    def _get_valid_soil_moisture(self) -> float | None:
        soil_moisture = self.sensor_values.soil_moisture
        max_age = timedelta(seconds=self.settings.get("sensor_check_interval_sec"))

        if datetime.now() - soil_moisture.measured_at > max_age:
            print("too old sensor value")
            return None

        return soil_moisture.value
