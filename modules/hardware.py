import time
import threading
from datetime import datetime
from pathlib import Path

from gpiozero import PWMOutputDevice

from .dataclasses import Image


class Pump:
    MOTOR_PIN = 26
    PWM_FREQUENCY = 500
    DUTY_CYCLE = 0.6

    def __init__(self):
        self._motor = PWMOutputDevice(
            self.MOTOR_PIN, frequency=self.PWM_FREQUENCY, initial_value=0
        )

    def start(self):
        self._motor.value = self.DUTY_CYCLE

    def stop(self):
        self._motor.off()

    def close(self):
        self._motor.off()
        self._motor.close()


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

        dry = self.settings.get("soil_moisture_dry")
        wet = self.settings.get("soil_moisture_wet")

        moisture = (raw_value - dry) / (wet - dry) * 100
        return max(0.0, min(100.0, moisture)), raw_value

    def _read_raw(self) -> int:
        # TODO: MCP3002から取得
        return 1000


class TemperatureAndHumiditySensor:
    def read(self) -> tuple[float, float]:
        # TODO DHT20から取得
        return 20, 30
