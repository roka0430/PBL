from datetime import datetime
from dataclasses import dataclass, fields


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
