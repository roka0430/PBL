import sqlite3
from datetime import datetime

from .paths import DATABASE_PATH
from .enums import WateringType


class WateringDatabase:
    def __init__(self):
        DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)

        with sqlite3.connect(DATABASE_PATH) as con:
            con.execute("""
                CREATE TABLE IF NOT EXISTS watering_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    watered_at TEXT NOT NULL,
                    watering_type TEXT NOT NULL,
                    amount_ml INTEGER NOT NULL
                )
                """)

    def add(self, success, watered_at, watering_type, amount_ml):
        watered_at_str = watered_at.isoformat(timespec="seconds")

        print("成功" if success else "失敗", watered_at_str, watering_type, amount_ml)
        # TODO printは消す

        # with sqlite3.connect(DATABASE_PATH) as con:
        #     con.execute(
        #         """
        #         INSERT INTO watering_history
        #             (watered_at, watering_type, amount_ml)
        #         VALUES (?, ?, ?)
        #         """,
        #         (watered_at_str, watering_type.value, amount_ml),
        #     )
        # TODO successをdbに保存する処理を追加する

    def get(self, before_id, after_id, limit) -> list[dict]:
        with sqlite3.connect(DATABASE_PATH) as con:
            con.row_factory = sqlite3.Row

            if before_id is None and after_id is None:
                rows = con.execute(
                    """
                    SELECT id, watered_at, watering_type, amount_ml
                    FROM watering_history
                    ORDER BY id DESC
                    LIMIT ?
                    """,
                    (limit,),
                ).fetchall()
            elif before_id is not None:
                rows = con.execute(
                    """
                    SELECT id, watered_at, watering_type, amount_ml
                    FROM watering_history
                    WHERE id < ?
                    ORDER BY id DESC
                    LIMIT ?
                    """,
                    (before_id, limit),
                ).fetchall()
            else:
                rows = con.execute(
                    """
                    SELECT id, watered_at, watering_type, amount_ml
                    FROM watering_history
                    WHERE id > ?
                    ORDER BY id ASC
                    LIMIT ?
                    """,
                    (after_id, limit),
                ).fetchall()

            return [
                {
                    "id": row["id"],
                    "watered_at": row["watered_at"],
                    "watering_type": WateringType(row["watering_type"]),
                    "amount_ml": row["amount_ml"],
                }
                for row in rows
            ]

    def get_all(self) -> list[dict]:
        with sqlite3.connect(DATABASE_PATH) as con:
            con.row_factory = sqlite3.Row

            rows = con.execute("""
                SELECT id, watered_at, watering_type, amount_ml
                FROM watering_history
                ORDER BY watered_at DESC
                """).fetchall()

            return [
                {
                    "id": row["id"],
                    "watered_at": row["watered_at"],
                    "watering_type": WateringType(row["watering_type"]),
                    "amount_ml": row["amount_ml"],
                }
                for row in rows
            ]

    def get_count(self) -> int:
        with sqlite3.connect(DATABASE_PATH) as con:
            row = con.execute("SELECT COUNT(*) FROM watering_history").fetchone()

        return row[0]

    def get_last_watered_at(self) -> datetime | None:
        with sqlite3.connect(DATABASE_PATH) as con:
            row = con.execute("""
                SELECT watered_at
                FROM watering_history
                ORDER BY watered_at DESC
                LIMIT 1
                """).fetchone()

        if row is None:
            return None

        return datetime.fromisoformat(row[0])


class SensorDatabase:
    def __init__(self):
        DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)

        with sqlite3.connect(DATABASE_PATH) as con:
            con.execute("""
                CREATE TABLE IF NOT EXISTS sensor_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    measured_at TEXT NOT NULL,
                    temperature REAL,
                    humidity REAL,
                    soil_moisture REAL
                )
                """)

    def add(self, measured_at, temperature, humidity, soil_moisture):
        measured_at_str = measured_at.isoformat(timespec="seconds")

        with sqlite3.connect(DATABASE_PATH) as con:
            con.execute(
                """
                INSERT INTO sensor_history
                    (measured_at, temperature, humidity, soil_moisture)
                VALUES (?, ?, ?, ?)
                """,
                (measured_at_str, temperature, humidity, soil_moisture),
            )

    def get(self, limit) -> list[dict]:
        with sqlite3.connect(DATABASE_PATH) as con:
            con.row_factory = sqlite3.Row

            rows = con.execute(
                """
                SELECT id, measured_at, temperature, humidity, soil_moisture
                FROM sensor_history
                ORDER BY id DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()

        return [
            {
                "id": row["id"],
                "measured_at": row["measured_at"],
                "temperature": row["temperature"],
                "humidity": row["humidity"],
                "soil_moisture": row["soil_moisture"],
            }
            for row in reversed(rows)
        ]

    def get_last_measured_at(self) -> datetime | None:
        with sqlite3.connect(DATABASE_PATH) as con:
            row = con.execute("""
                SELECT measured_at
                FROM sensor_history
                ORDER BY measured_at DESC
                LIMIT 1
                """).fetchone()

        if row is None:
            return None

        return datetime.fromisoformat(row[0])
