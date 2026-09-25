import time
import queue
from enum import Enum
from dataclasses import dataclass

SENSOR_CHECK_INTERVAL_SEC = 180  # 土壌水分量を測定する間隔(秒)


# ------------------------------ Status ------------------------------


class WateringStatus(Enum):
    IDLE = "idle"  # 待機中
    WATERING = "watering"  # 給水中
    CALIBRATING = "calibrating"  # 校正中
    ERROR = "error"  # エラー


# ------------------------------ Command ------------------------------


class WateringCommandType(Enum):
    WATERING = "watering"  # 給水命令


@dataclass
class WateringCommand:
    type: WateringCommandType
    amount_ml: int


# ------------------------------ Controller ------------------------------


class WateringController:
    def __init__(self):
        self.status = WateringStatus.IDLE
        self.command_queue = queue.Queue()

    def mainloop(self):

        next_sensor_check = time.monotonic()

        while True:
            try:
                command = self.command_queue.get(
                    timeout=max(0, next_sensor_check - time.monotonic())
                )
                self._process_command(command)

            except queue.Empty:
                self._check_sensor()
                next_sensor_check = time.monotonic() + SENSOR_CHECK_INTERVAL_SEC

    def _process_command(self, command):
        print("-----------------------------")
        print("command:", command.type.value)
        print("amount:", command.amount_ml)
        print("-----------------------------")

    def _check_sensor(self):
        print("check sensor")

    def request_watering(self, amount_ml):
        try:
            amount_ml = int(amount_ml)
        except (TypeError, ValueError):
            return False

        if not 10 <= amount_ml <= 500:
            return False

        self.command_queue.put(
            WateringCommand(type=WateringCommandType.WATERING, amount_ml=amount_ml)
        )

        return True
