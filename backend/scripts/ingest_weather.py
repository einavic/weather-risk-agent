import json
from pathlib import Path

from app.data_layer.db import get_connection
from app.data_layer.open_meteo import fetch_daily, parse_daily

HUBS_PATH = Path(__file__).resolve().parents[2] / "data" / "hubs.json"
START = "2021-01-01"
END = "2025-12-31"


def main():
    hubs = json.loads(HUBS_PATH.read_text())
    conn = get_connection()
    for hub in hubs:
        data = fetch_daily(hub["lat"], hub["lon"], START, END)
        rows = parse_daily(data)
        conn.executemany(
            "INSERT OR REPLACE INTO daily_weather VALUES (?, ?, ?, ?, ?, ?, ?)",
            [(hub["id"],) + row for row in rows],
        )
        conn.commit()
        print(hub["id"], len(rows), "rows")
    conn.close()


if __name__ == "__main__":
    main()
