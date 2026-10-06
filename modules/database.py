import sqlite3

from .paths import DATABASE_PATH

print(DATABASE_PATH)


class WateringDatabase:
    WATERING_HISTORY_TABLE = "watering_history"

    def add(self, watered_at, watering_type, amount_ml):
        pass

    def get_all(self):
        pass

    def close(self):
        pass
