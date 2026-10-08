import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parents[2] / "data" / "weather.db"


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS daily_weather (
            hub_id TEXT NOT NULL,
            date TEXT NOT NULL,
            snowfall_cm REAL,
            precipitation_mm REAL,
            temp_max_c REAL,
            temp_min_c REAL,
            wind_gust_max_kmh REAL,
            PRIMARY KEY (hub_id, date)
        )
        """
    )
    return conn
