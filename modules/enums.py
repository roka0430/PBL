from enum import Enum


class SystemStatus(Enum):
    IDLE = "idle"  # 待機中
    WATERING = "watering"  # 給水中
    CALIBRATING = "calibrating"  # 校正中
    ERROR = "error"  # 異常


class WateringRequestResult(Enum):
    ACCEPTED = "accepted"  # 受理
    INVALID_AMOUNT = "invalid_amount"  # 無効な給水量
    NOT_IDLE = "not_idle"  # システムが待機状態でない
