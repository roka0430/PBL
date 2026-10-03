import time
import queue
from enum import Enum
from dataclasses import dataclass

SENSOR_STARTUP_DELAY_SEC = 10  # センサー起動待ち時間
SENSOR_CHECK_INTERVAL_SEC = 3  # センシング間隔

MIN_WATER_AMOUNT_ML = 10  # 1回給水量下限
MAX_WATER_AMOUNT_ML = 200  # 1回給水量上限


# ------------------------------ Status ------------------------------


class SystemStatus(Enum):
    IDLE = "idle"  # 待機中
    WATERING = "watering"  # 給水中
    CALIBRATING = "calibrating"  # 校正中
    ERROR = "error"  # 異常


# ------------------------------ Controller ------------------------------


class SystemController:
    def __init__(self):
        self.status = SystemStatus.IDLE

    def request_watering(self, amount_ml):
        try:
            amount_ml = int(amount_ml)
        except (TypeError, ValueError):
            return False

        # さらに水やり条件を追加
        if not MIN_WATER_AMOUNT_ML <= amount_ml <= MAX_WATER_AMOUNT_ML:
            return False

        # ここで水やりスレッド生成 daemon=False

        return True

    def mainloop(self):
        next_sensor_check = time.monotonic() + SENSOR_STARTUP_DELAY_SEC

        while True:
            now = time.monotonic()

            if now >= next_sensor_check:
                self._check_sensor()
                next_sensor_check = now + SENSOR_CHECK_INTERVAL_SEC

            time.sleep(1)

    def _check_sensor(self):
        if self.status == SystemStatus.IDLE:
            self._check_soil_moisture()

        self._check_temperature_and_humidity()

    def _check_soil_moisture(self):
        print("[sensor] soil moisture")

    def _check_temperature_and_humidity(self):
        print("[sensor] temperature and humidity")


# ------------------------------ Hardware ------------------------------


class Pump:
    pass


class Camera:
    pass


class SoilMoistureSensor:
    pass


class TemperatureAndHumiditySensor:
    pass
