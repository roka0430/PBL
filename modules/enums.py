from enum import Enum


class SystemStatus(Enum):
    IDLE = "idle"  # 待機中
    WATERING = "watering"  # 給水中
    CALIBRATING = "calibrating"  # 校正中
    ERROR = "error"  # 異常


class AutoWateringMode(Enum):
    OFF = "off"

    THRESHOLD_CONTROL = "threshold_control"
    FIXED_AMOUNT = "fixed_amount"
    SCHEDULED = "scheduled"


class WateringResult(Enum):
    ACCEPTED = "accepted"
    INVALID_AMOUNT = "invalid_amount"
    NOT_IDLE = "not_idle"
    TOO_SOON = "too_soon"
    THREAD_START_FAILED = "thread_start_failed"
    EXECUTION_FAILED = "execution_failed"


class WateringType(Enum):
    AUTO = "auto"  # 自動給水
    MANUAL = "manual"  # 手動給水
