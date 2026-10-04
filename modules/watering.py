import time
import json
import random  # TODO: デモ用
import threading
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass, fields

from .enums import SystemStatus, WateringRequestResult

SENSOR_STARTUP_DELAY_SEC = 10  # センサー起動待ち時間
SENSOR_CHECK_INTERVAL_SEC = 3  # センシング間隔

MIN_WATER_AMOUNT_ML = 10  # 1回給水量下限
MAX_WATER_AMOUNT_ML = 200  # 1回給水量上限
MIN_WATERING_INTERVAL_SEC = 10  # 給水間隔制限


class Settings:
    PATH = Path("config/settings.json")

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
        if not self.PATH.exists():
            return

        try:
            data = json.loads(self.PATH.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return

        for name in self.DEFAULTS:
            if name in data:
                setattr(self, name, data[name])

    def save(self):
        self.PATH.parent.mkdir(parents=True, exist_ok=True)

        data = {name: getattr(self, name) for name in self.DEFAULTS}

        self.PATH.write_text(
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
        self._history = []

    def add(self, amount_ml, watered_at):
        self._history.append({"amount_ml": amount_ml, "watered_at": watered_at})

    def get_last(self):
        if not self._history:
            return None
        return self._history[-1]

    def elapsed_sec_since_last(self) -> float | None:
        last = self.get_last()

        if last is None:
            return None

        return (datetime.now() - last["watered_at"]).total_seconds()


@dataclass
class SensorValue:
    value: float
    measured_at: datetime

    def to_dict(self) -> dict:
        return {
            "value": self.value,
            "measured_at": self.measured_at.isoformat(),
        }


@dataclass
class SensorValues:
    soil_moisture: SensorValue | None = None
    temperature: SensorValue | None = None
    humidity: SensorValue | None = None

    @property
    def ready(self) -> bool:
        return (
            self.soil_moisture is not None
            and self.temperature is not None
            and self.humidity is not None
        )

    def to_dict(self) -> dict:
        result = {"ready": self.ready}

        for field in fields(self):
            value = getattr(self, field.name)
            result[field.name] = value.to_dict() if value is not None else None

        return result


@dataclass
class Image:
    data: bytes
    captured_at: datetime


# ------------------------------ Hardware ------------------------------


class Pump:
    def run(self, duration_sec):
        # TODO: ポンプ制御を追加
        print("pump start")
        print(f"duration: {duration_sec}s")
        time.sleep(duration_sec)
        print("pump stop")


class Camera:
    CACHE_SECONDS = 10

    def __init__(self):
        self._image: Image | None = None
        self._captured_at = 0.0
        self._lock = threading.Lock()

    def capture_image(self) -> Image:
        path = Path("demo/sample.jpg")  # TODO: ここに撮影処理を追加

        image = Image(data=path.read_bytes(), captured_at=datetime.now())

        self._image = image
        self._captured_at = time.monotonic()

        return image

    def get_image(self) -> Image:
        with self._lock:
            if (
                self._image is None
                or time.monotonic() - self._captured_at >= self.CACHE_SECONDS
            ):
                return self.capture_image()
            return self._image


class SoilMoistureSensor:
    def __init__(self, settings):
        self.settings = settings

    def read(self) -> float:
        raw_value = self._read_raw()

        dry = self.settings.soil_moisture_dry
        wet = self.settings.soil_moisture_wet

        moisture = (raw_value - dry) / (wet - dry) * 100
        return max(0.0, min(100.0, moisture))

    def _read_raw(self) -> int:
        # TODO: MCP3002から取得
        return random.randint(0, 1023)


class TemperatureAndHumiditySensor:
    def read(self) -> tuple[float, float]:
        return random.randint(100, 400) / 10, random.randint(0, 1000) / 10  # 温度, 湿度


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

        threading.Thread(target=self._watering, args=(amount_ml,), daemon=False).start()

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

    def _watering(self, amount_ml):
        try:
            flow_rate = self.settings.pump_flow_ml_per_sec
            duration_sec = amount_ml / flow_rate

            self.pump.run(duration_sec)
            self.history.add(amount_ml, datetime.now())
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
