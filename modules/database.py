import sqlite3
from datetime import datetime

from .paths import DATABASE_PATH
from .enums import WateringType

print(DATABASE_PATH)


class WateringDatabase:
    WATERING_HISTORY_TABLE = "watering_history"

    def __init__(self):
        DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)

        with sqlite3.connect(DATABASE_PATH) as con:
            con.execute(f"""
                CREATE TABLE IF NOT EXISTS {self.WATERING_HISTORY_TABLE} (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    watered_at TEXT NOT NULL,
                    watering_type TEXT NOT NULL,
                    amount_ml INTEGER NOT NULL
                )
                """)

    def add(self, watered_at, watering_type, amount_ml):
        watered_at_str = watered_at.isoformat(timespec="seconds")

        with sqlite3.connect(DATABASE_PATH) as con:
            con.execute(
                f"""
                INSERT INTO {self.WATERING_HISTORY_TABLE}
                    (watered_at, watering_type, amount_ml)
                VALUES (?, ?, ?)
                """,
                (watered_at_str, watering_type.value, amount_ml),
            )

    def get(self, start_id, limit) -> list[dict]:
        with sqlite3.connect(DATABASE_PATH) as con:
            con.row_factory = sqlite3.Row

            rows = con.execute(
                """
                SELECT id, watered_at, watering_type, amount_ml
                FROM watering_history
                WHERE id <= ?
                ORDER BY id DESC
                LIMIT ?
                """,
                (start_id, limit),
            ).fetchall()

        return [
            {
                "id": row["id"],
                "watered_at": datetime.fromisoformat(row["watered_at"]),
                "watering_type": WateringType(row["watering_type"]),
                "amount_ml": row["amount_ml"],
            }
            for row in rows
        ]

    def get_all(self) -> list[dict]:
        with sqlite3.connect(DATABASE_PATH) as con:
            con.row_factory = sqlite3.Row

            rows = con.execute(f"""
                SELECT id, watered_at, watering_type, amount_ml
                FROM {self.WATERING_HISTORY_TABLE}
                ORDER BY watered_at DESC
                """).fetchall()

            return [
                {
                    "id": row["id"],
                    "watered_at": datetime.fromisoformat(row["watered_at"]),
                    "watering_type": WateringType(row["watering_type"]),
                    "amount_ml": row["amount_ml"],
                }
                for row in rows
            ]

    def get_last_watered_at(self) -> datetime | None:
        with sqlite3.connect(DATABASE_PATH) as con:
            row = con.execute(f"""
                SELECT watered_at
                FROM {self.WATERING_HISTORY_TABLE}
                ORDER BY watered_at DESC
                LIMIT 1
                """).fetchone()

        if row is None:
            return None

        return datetime.fromisoformat(row[0])
