import time
import random  # TODO: デモ用
import threading
from datetime import datetime
from pathlib import Path

from .dataclasses import Image


class Pump:
    # TODO ポンプ制御を追加
    def start(self):
        print("pump start")

    def stop(self):
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

        dry = self.settings.get("soil_moisture_dry")
        wet = self.settings.get("soil_moisture_wet")

        moisture = (raw_value - dry) / (wet - dry) * 100
        return max(0.0, min(100.0, moisture))

    def _read_raw(self) -> int:
        # TODO: MCP3002から取得
        return random.randint(0, 1023)


class TemperatureAndHumiditySensor:
    def read(self) -> tuple[float, float]:
        return random.randint(100, 400) / 10, random.randint(0, 1000) / 10  # 温度, 湿度
