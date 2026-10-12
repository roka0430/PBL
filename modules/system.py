import os
import time
import threading
from datetime import datetime, timedelta

from .enums import SystemStatus, AutoWateringMode, ManualWateringResult, WateringType
from .dataclasses import Task, SensorValue, SensorValues, Image
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

        self.auto_watering_mode = AutoWateringMode.FIXED_AMOUNT  # TODO OFFにする

        self.watering_database = WateringDatabase()

        self.sensor_values = SensorValues()

        self.watering_stop_event = threading.Event()

        self.pump = Pump()
        self.camera = Camera()
        self.soil_moisture_sensor = SoilMoistureSensor(self.settings)
        self.temperature_and_humidity_sensor = TemperatureAndHumiditySensor()

        self._tasks = [
            Task(self._check_sensors, interval_key="sensor_check_interval_sec"),
            Task(
                self._process_auto_watering,
                interval_key="auto_watering_check_interval_sec",
            ),
        ]

    # ========== 外部から呼び出し ==========

    def manual_watering(self, amount_ml) -> ManualWateringResult:
        try:
            amount_ml = int(amount_ml)
        except (TypeError, ValueError):
            return ManualWateringResult.INVALID_AMOUNT

        if not MIN_WATER_AMOUNT_ML <= amount_ml <= MAX_WATER_AMOUNT_ML:
            return ManualWateringResult.INVALID_AMOUNT

        last_watered_at = self.watering_database.get_last_watered_at()
        if last_watered_at is not None:
            elapsed = (datetime.now() - last_watered_at).total_seconds()
            if elapsed < MIN_WATERING_INTERVAL_SEC:
                return ManualWateringResult.TOO_SOON

        with self._status_lock:
            if self.status != SystemStatus.IDLE:
                return ManualWateringResult.NOT_IDLE
            self.status = SystemStatus.WATERING

        self.watering_stop_event.clear()

        threading.Thread(  # TODO スレッド生成に失敗したときidleに戻す
            target=self._run_watering_once,
            args=(WateringType.MANUAL, amount_ml),
            daemon=False,
        ).start()

        return ManualWateringResult.ACCEPTED

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
        time.sleep(self.settings.get("senso_startup_delay_sec"))

        now = time.monotonic()

        for task in self._tasks:
            task.next_run = now

        while True:
            now = time.monotonic()

            due_tasks = [task for task in self._tasks if task.next_run <= now]

            if due_tasks:
                for task in due_tasks:
                    interval = self.settings.get(task.interval_key)
                    task.next_run = time.monotonic() + interval

                    try:
                        task.callback()
                    except Exception:
                        print("定期タスクの実行に失敗しました")

                continue

            next_run = min(task.next_run for task in self._tasks)
            timeout = max(0.0, next_run - time.monotonic())

            time.sleep(timeout)

    # ========== 内部処理 ==========

    def _watering(self, watering_type, amount_ml):
        try:
            duration_sec = amount_ml / self.settings.get("pump_flow_ml_per_sec")

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

    def _run_watering_once(self, watering_type, amount_ml):
        try:
            self._watering(watering_type, amount_ml)
        finally:
            with self._status_lock:
                self.status = SystemStatus.IDLE

    def _run_watering_loop(self, watering_type):
        amount_ml = 50

        try:
            self._watering(watering_type, amount_ml)
        finally:
            with self._status_lock:
                self.status = SystemStatus.IDLE

    def _thread_watering_once(self, watering_type, amount_ml):
        pass

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

    def _process_auto_watering(self):  # TODO 給水中などの早期returnを追加
        if self.auto_watering_mode == AutoWateringMode.OFF:
            return

        if self.auto_watering_mode == AutoWateringMode.THRESHOLD_CONTROL:
            self._process_threshold_control()

        if self.auto_watering_mode == AutoWateringMode.FIXED_AMOUNT:
            self._process_fixed_amount()

        if self.auto_watering_mode == AutoWateringMode.SCHEDULED:
            self._process_scheduled()

    def _process_threshold_control(self):
        if not self._is_soil_dry():
            return

    def _process_fixed_amount(self):
        if self._is_soil_dry() is not True:
            return

        with self._status_lock:
            if self.status != SystemStatus.IDLE:
                return
            self.status = SystemStatus.WATERING

        amount_ml = self.settings.get("watering_amount_ml")

        self._run_watering_once(WateringType.AUTO, amount_ml)

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
