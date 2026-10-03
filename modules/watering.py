import time
import base64
import threading
from enum import Enum
from pathlib import Path  # デモ用
from datetime import datetime
from dataclasses import dataclass, fields

SENSOR_STARTUP_DELAY_SEC = 0  # センサー起動待ち時間
SENSOR_CHECK_INTERVAL_SEC = 3  # センシング間隔

MIN_WATER_AMOUNT_ML = 10  # 1回給水量下限
MAX_WATER_AMOUNT_ML = 200  # 1回給水量上限


# ------------------------------ Status ------------------------------


class SystemStatus(Enum):
    IDLE = "idle"  # 待機中
    WATERING = "watering"  # 給水中
    CALIBRATING = "calibrating"  # 校正中
    ERROR = "error"  # 異常


# ------------------------------ Value ------------------------------


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

    def to_dict(self) -> dict:
        result = {}

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
    pass


class Camera:
    CACHE_SECONDS = 10

    def __init__(self):
        self._image: Image | None = None
        self._captured_at = 0.0
        self._lock = threading.Lock()

    def capture_image(self) -> Image:
        path = Path("demo/sample.jpg")  # ここに撮影処理を追加

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
    def read(self) -> float:
        return 50.0


class TemperatureAndHumiditySensor:
    def read(self) -> tuple[float, float]:
        return 25.0, 60.0  # 温度, 湿度


# ------------------------------ Controller ------------------------------


class SystemController:
    def __init__(self):
        self.status = SystemStatus.IDLE
        self._status_lock = threading.Lock()

        self.sensor_values = SensorValues()

        self.pump = Pump()
        self.camera = Camera()
        self.soil_moisture_sensor = SoilMoistureSensor()
        self.temperature_and_humidity_sensor = TemperatureAndHumiditySensor()

    # ========== 外部から呼び出し ==========

    def request_watering(self, amount_ml) -> bool:
        try:
            amount_ml = int(amount_ml)
        except (TypeError, ValueError):
            return False

        # さらに水やり条件を追加
        if not MIN_WATER_AMOUNT_ML <= amount_ml <= MAX_WATER_AMOUNT_ML:
            return False

        with self._status_lock:
            if self.status != SystemStatus.IDLE:
                return False
            self.status = SystemStatus.WATERING

        threading.Thread(target=self._watering, args=(amount_ml,), daemon=False).start()

        return True

    def get_sensor_values(self) -> SensorValues:
        return self.sensor_values

    def get_image(self) -> Image:
        return self.camera.get_image()

    # ========== メインループ ==========

    def mainloop(self):
        next_sensor_check = time.monotonic() + SENSOR_STARTUP_DELAY_SEC

        while True:
            now = time.monotonic()

            if now >= next_sensor_check:
                self._check_sensors()
                next_sensor_check = now + SENSOR_CHECK_INTERVAL_SEC

            time.sleep(1)

    # ========== 内部処理 ==========

    def _watering(self, amount_ml):
        try:
            print("watering start")
            time.sleep(5)
            print("watering stop")
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
