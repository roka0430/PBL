import time
import threading
from datetime import datetime
from pathlib import Path

import cv2
import board
import adafruit_ahtx0
import spidev
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
    IMAGE_WIDTH = 1280
    IMAGE_HEIGHT = 720

    def __init__(self):
        self._image: Image | None = None
        self._captured_at = 0.0
        self._lock = threading.Lock()

    def capture_image(self) -> Image:
        camera = cv2.VideoCapture(0, cv2.CAP_V4L2)

        try:
            if not camera.isOpened():
                raise RuntimeError("Failed to open USB camera")

            camera.set(cv2.CAP_PROP_FRAME_WIDTH, self.IMAGE_WIDTH)
            camera.set(cv2.CAP_PROP_FRAME_HEIGHT, self.IMAGE_HEIGHT)

            success, frame = camera.read()
            if not success:
                raise RuntimeError("Failed to capture image")

            success, encoded = cv2.imencode(".jpg", frame)
            if not success:
                raise RuntimeError("Failed to encode image to JPEG")

            image = Image(
                data=encoded.tobytes(),
                captured_at=datetime.now(),
            )

            self._image = image
            self._captured_at = time.monotonic()

            return image

        finally:
            camera.release()

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

        self._spi = spidev.SpiDev()
        self._spi.open(0, 0)
        self._spi.max_speed_hz = 1_000_000
        self._spi.mode = 0

    def read(self) -> float:
        raw_value = self._read_raw()

        dry = self.settings.get("soil_moisture_dry")
        wet = self.settings.get("soil_moisture_wet")

        moisture = (raw_value - dry) / (wet - dry) * 100
        return max(0.0, min(100.0, moisture)), raw_value

    def _read_raw(self) -> int:
        response = self._spi.xfer2([0x68, 0x00])  # TODO CH0でなければ修正
        return ((response[0] & 0x03) << 8) | response[1]

    def close(self):
        self._spi.close()


class TemperatureAndHumiditySensor:
    def __init__(self):
        self._sensor = adafruit_ahtx0.AHTx0(board.I2C())

    def read(self) -> tuple[float, float]:
        temperature = self._sensor.temperature
        humidity = self._sensor.relative_humidity

        return temperature, humidity
