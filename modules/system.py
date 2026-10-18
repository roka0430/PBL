import os
import time
import threading
from datetime import datetime, timedelta

from .enums import SystemStatus, AutoWateringMode, WateringResult, WateringType
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
MAX_WATER_AMOUNT_ML = 1000  # 1回給水量上限 # TODO 量を減らす

MIN_WATERING_INTERVAL_SEC = 10  # 給水間隔制限


class SystemController:
    def __init__(self):
        self.settings = Settings()

        self.status = SystemStatus.IDLE
        self._status_lock = threading.Lock()
        self.auto_watering_mode = AutoWateringMode.OFF

        self.system_stop_event = threading.Event()
        self.watering_stop_event = threading.Event()
        self.task_changed_event = threading.Event()

        self.sensor_values = SensorValues()
        self.watering_database = WateringDatabase()

        self.pump = Pump()
        self.camera = Camera()
        self.soil_moisture_sensor = SoilMoistureSensor()
        self.temperature_and_humidity_sensor = TemperatureAndHumiditySensor()

        self._tasks = {
            "sensors": Task(
                callback=self._check_sensors,
                interval_key="sys.sensing_interval_sec",
            ),
            "threshold_control": Task(
                callback=self._process_auto_watering,
                interval_key="thr.determination_interval_sec",
                enabled=False,
            ),
            "fixed_amount": Task(
                callback=self._process_auto_watering,
                interval_key="fix.determination_interval_sec",
                enabled=False,
            ),
            "scheduled": Task(
                callback=self._process_auto_watering,
                interval_key="sch.interval_sec",
                enabled=False,
            ),
        }

    #

    def mainloop(self):
        time.sleep(self.settings.get("sys.startup_waiting_sec"))

        now = time.monotonic()
        for task in self._tasks.values():
            task.next_run = now

        while not self.system_stop_event.is_set():
            self.task_changed_event.clear()
            now = time.monotonic()

            due_tasks = [
                task
                for task in self._tasks.values()
                if task.enabled and task.next_run <= now
            ]

            if due_tasks:
                for task in due_tasks:
                    interval = self.settings.get(task.interval_key)
                    task.next_run = time.monotonic() + interval

                    try:
                        task.callback()
                    except Exception as e:
                        print(f"定期タスクの実行に失敗しました: {e}")
                continue

            enabled_tasks = [task for task in self._tasks.values() if task.enabled]

            if enabled_tasks:
                next_run = min(task.next_run for task in enabled_tasks)
                timeout = max(0.0, next_run - time.monotonic())
            else:
                timeout = None

            self.task_changed_event.wait(timeout)

    # -------------------- 外部 --------------------

    def stop_system(self):
        self.system_stop_event.set()
        self.stop_watering()

    def close(self):
        self.pump.close()
        self.soil_moisture_sensor.close()

    #

    def get_status(self) -> SystemStatus:
        return self.status

    def emergency_stop(self):
        self.stop_watering()
        self.auto_watering_mode = AutoWateringMode.OFF

    def set_auto_watering_mode(self, mode):
        if mode not in {mode.value for mode in AutoWateringMode}:
            return
        self.auto_watering_mode = AutoWateringMode(mode)
        self._sync_tasks_with_mode()

    def get_auto_watering_mode(self):
        return self.auto_watering_mode.value

    #

    def manual_watering(self, amount_ml) -> WateringResult:
        try:
            amount_ml = int(amount_ml)
        except (TypeError, ValueError):
            return WateringResult.INVALID_AMOUNT

        if not MIN_WATER_AMOUNT_ML <= amount_ml <= MAX_WATER_AMOUNT_ML:
            return WateringResult.INVALID_AMOUNT

        last_watered_at = self.watering_database.get_last_watered_at()
        if last_watered_at is not None:
            elapsed = (datetime.now() - last_watered_at).total_seconds()
            if elapsed < MIN_WATERING_INTERVAL_SEC:
                return WateringResult.TOO_SOON

        return self._start_watering_once(WateringType.MANUAL, amount_ml)

    def stop_watering(self):
        self.watering_stop_event.set()
        self.pump.stop()

    #

    def get_sensor_values(self) -> SensorValues:
        return self.sensor_values

    def get_image(self) -> Image:
        return self.camera.get_image()

    #

    def get_settings(self) -> list[dict]:
        return self.settings.get_settings()

    def get_setting_definitions(self) -> list[dict]:
        return self.settings.get_definitions()

    def set_setting(self, key, value):
        success, value = self.settings.update(key, value)

        if not success:
            return {"success": False, "key": key}

        self._sync_tasks_with_setting(key)
        return {"success": True, "key": key, "value": value}

    #

    def get_history_count(self) -> int:
        return self.watering_database.get_count()

    def get_watering_history(self, before_id, after_id, limit) -> list[dict]:
        return self.watering_database.get(
            before_id=before_id, after_id=after_id, limit=limit
        )

    # -------------------- タスク管理 --------------------

    def _sync_tasks_with_mode(self):
        for mode in AutoWateringMode:
            if mode == AutoWateringMode.OFF:
                continue

            task = self._tasks[mode.value]

            if mode == self.auto_watering_mode:
                interval = self.settings.get(task.interval_key)
                task.enabled = True
                task.next_run = time.monotonic() + interval
            else:
                task.enabled = False
                task.next_run = None

        self.task_changed_event.set()

    def _sync_tasks_with_setting(self, updated_key):
        changed = False

        for task in self._tasks.values():
            if task.interval_key != updated_key:
                continue

            interval = self.settings.get(task.interval_key)
            task.next_run = time.monotonic() + interval
            changed = True

        if changed:
            self.task_changed_event.set()

    # -------------------- 自動給水 --------------------

    def _process_auto_watering(self):
        with self._status_lock:
            if self.status != SystemStatus.IDLE:
                return

        if self.auto_watering_mode == AutoWateringMode.OFF:
            return

        if self.auto_watering_mode == AutoWateringMode.THRESHOLD_CONTROL:
            self._process_threshold_control()

        if self.auto_watering_mode == AutoWateringMode.FIXED_AMOUNT:
            self._process_fixed_amount()

        if self.auto_watering_mode == AutoWateringMode.SCHEDULED:
            self._process_scheduled()

    def _process_threshold_control(self):
        if self._is_soil_dry("thr.start_soil_moisture_percent") is not True:
            return

        self._start_watering_loop(WateringType.AUTO)

    def _process_fixed_amount(self):
        if self._is_soil_dry("fix.start_soil_moisture_percent") is not True:
            return

        amount_ml = self.settings.get("fix.amount_ml")
        self._start_watering_once(WateringType.AUTO, amount_ml)

    def _process_scheduled(self):
        amount_ml = self.settings.get("sch.amount_ml")
        self._start_watering_once(WateringType.AUTO, amount_ml)

    #

    def _is_soil_dry(self, key) -> bool | None:
        value = self._get_valid_soil_moisture()

        if value is None:
            return None

        return value < self.settings.get(key)

    def _is_soil_wet(self, key) -> bool | None:
        value = self._get_valid_soil_moisture()

        if value is None:
            return None

        return value > self.settings.get(key)

    def _get_valid_soil_moisture(self) -> float | None:
        soil_moisture = self.sensor_values.soil_moisture
        max_age = timedelta(seconds=self.settings.get("sys.sensing_interval_sec") * 2)

        if datetime.now() - soil_moisture.measured_at > max_age:
            print("too old sensor value")
            return None

        return soil_moisture.value

    # -------------------- 給水処理 --------------------

    def _start_watering_once(self, watering_type, amount_ml) -> WateringResult:
        with self._status_lock:
            if self.status != SystemStatus.IDLE:
                return WateringResult.NOT_IDLE
            self.status = SystemStatus.WATERING

        self.watering_stop_event.clear()

        try:
            thread = threading.Thread(
                target=self._run_watering_once,
                args=(watering_type, amount_ml),
                daemon=False,
            )
            thread.start()
        except Exception:
            with self._status_lock:
                self.status = SystemStatus.IDLE

            return WateringResult.THREAD_START_FAILED

        return WateringResult.ACCEPTED

    def _run_watering_once(self, watering_type, amount_ml):
        try:
            self._watering(amount_ml)
        finally:
            with self._status_lock:
                self.status = SystemStatus.IDLE

            success = not self.watering_stop_event.is_set()
            self._record_watering_history(success, watering_type, amount_ml)

    #

    def _start_watering_loop(self, watering_type) -> WateringResult:
        with self._status_lock:
            if self.status != SystemStatus.IDLE:
                return WateringResult.NOT_IDLE
            self.status = SystemStatus.WATERING

        self.watering_stop_event.clear()

        try:
            thread = threading.Thread(
                target=self._run_watering_loop,
                args=(watering_type,),
                daemon=False,
            )
            thread.start()
        except Exception:
            with self._status_lock:
                self.status = SystemStatus.IDLE

            return WateringResult.THREAD_START_FAILED

        return WateringResult.ACCEPTED

    def _run_watering_loop(self, watering_type):
        total_amount_ml = 0

        try:
            while not self.watering_stop_event.is_set():
                amount_ml = 50
                self._watering(amount_ml)
                total_amount_ml += amount_ml

                if self.watering_stop_event.wait(2):
                    break

                self._check_soil_moisture()

                if self._is_soil_wet("thr.stop_soil_moisture_percent"):
                    break
        finally:
            with self._status_lock:
                self.status = SystemStatus.IDLE

            success = not self.watering_stop_event.is_set()
            self._record_watering_history(success, watering_type, total_amount_ml)

    #

    def _watering(self, amount_ml):
        try:
            duration_sec = amount_ml / self.settings.get("sys.pump_flow_rate_ml_sec")

            self.pump.start()

            stopped = self.watering_stop_event.wait(duration_sec)

            self.pump.stop()

            if stopped:
                return

        finally:
            self.pump.stop()

    def _record_watering_history(self, success, watering_type, amount_ml):
        self.watering_database.add(
            success=success,
            watered_at=datetime.now(),
            watering_type=watering_type,
            amount_ml=amount_ml,
        )

    # -------------------- センサ処理 --------------------

    def _check_sensors(self):
        with self._status_lock:
            if self.status == SystemStatus.IDLE:
                self._check_soil_moisture()
        self._check_temperature_and_humidity()

    def _check_soil_moisture(self):
        soil_moisture_raw = self.soil_moisture_sensor.read()

        dry = self.settings.get("sys.soil_moisture_dry")
        wet = self.settings.get("sys.soil_moisture_wet")
        soil_moisture = (soil_moisture_raw - dry) / (wet - dry) * 100
        soil_moisture = max(0.0, min(100.0, soil_moisture))

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
